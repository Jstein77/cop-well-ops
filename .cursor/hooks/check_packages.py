#!/usr/bin/env python3
"""Enforce IT Policy SEC-PKG-001 (Approved Python Packages).

As a Cursor beforeShellExecution hook it reads the hook payload on stdin and
denies any package install that names a package missing from
policy/approved-packages.txt. CI runs the same check against requirements.txt:

    python .cursor/hooks/check_packages.py --check-requirements requirements.txt
"""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

POLICY_ID = "SEC-PKG-001"
POLICY_NAME = "Approved Python Packages"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "policy" / "approved-packages.txt"

SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
PYTHON_RE = re.compile(r"^(python|python3(\.\d+)?|py)$")
PIP_RE = re.compile(r"^pip(3(\.\d+)?)?$")
REDIRECT_RE = re.compile(r"^(\d*|&)(>>?|<)(&\d+)?")
SHELLS = {"bash", "sh", "zsh"}
PREFIXES = {"sudo", "env", "command", "exec", "time", "nohup"}

# Installer flags that consume the following token.
VALUE_FLAGS = set(
    """
    -c --constraint -i --index-url --extra-index-url --index --default-index -f --find-links
    -t --target --prefix --root --src --python -p --platform --python-version --implementation
    --abi --cache-dir --trusted-host --proxy --timeout --retries --log --progress-bar
    --upgrade-strategy --group --optional --extra --source -G --save-prefix --registry --tag
    """.split()
)


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def load_policy(path: Path) -> set[str]:
    lines = path.read_text().splitlines()
    return {normalize(line.split("#")[0].strip()) for line in lines if line.split("#")[0].strip()}


def requirement_names(path: Path, seen: set[Path] | None = None) -> list[str]:
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        return []
    seen.add(path)
    specs: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith(("-r ", "--requirement ")):
            specs += requirement_names(path.parent / line.split(maxsplit=1)[1], seen)
        elif not line.startswith("-"):
            specs.append(line)
    return specs


def split_tokens(segment: str) -> list[str]:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    while tokens and (tokens[0] in PREFIXES or re.match(r"^\w+=", tokens[0])):
        tokens = tokens[1:]
    return strip_redirects(tokens)


def strip_redirects(tokens: list[str]) -> list[str]:
    kept: list[str] = []
    skip_target = False
    for token in tokens:
        if skip_target:
            skip_target = False
            continue
        match = REDIRECT_RE.match(token)
        if match:
            # A bare operator such as ">" or "2>" takes its target from the next token.
            skip_target = match.end() == len(token) and not match.group(3)
            continue
        kept.append(token)
    return kept


def install_args(tokens: list[str]) -> tuple[str, list[str]] | None:
    """Return (ecosystem, args after the install verb) if tokens are a package install."""
    if not tokens:
        return None
    exe = Path(tokens[0]).name
    rest = tokens[1:]
    if PYTHON_RE.match(exe) and rest[:2] == ["-m", "pip"]:
        exe, rest = "pip", rest[2:]
    if PIP_RE.match(exe) and rest[:1] == ["install"]:
        return "python", rest[1:]
    if exe == "uv" and rest[:2] == ["pip", "install"]:
        return "python", rest[2:]
    if exe == "uv" and rest[:1] == ["add"]:
        return "python", rest[1:]
    if exe in {"poetry", "pdm"} and rest[:1] == ["add"]:
        return "python", rest[1:]
    if exe in {"pipx", "conda", "mamba"} and rest[:1] == ["install"]:
        return "python", rest[1:]
    if exe in {"npm", "pnpm", "yarn", "bun"} and rest[:1] and rest[0] in {"install", "i", "add"}:
        return "node", rest[1:]
    return None


def check_install(ecosystem: str, args: list[str], cwd: Path, approved: set[str]) -> list[str]:
    """Return human-readable violations for one install command."""
    violations: list[str] = []
    specs: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]
        flag, _, inline = arg.partition("=")
        if flag in {"-r", "--requirement"}:
            target = inline or (args[i + 1] if i + 1 < len(args) else "")
            i += 1 if inline else 2
            req = cwd / target
            if not req.is_file():
                violations.append(f"cannot verify requirements file '{target}'")
            else:
                specs += requirement_names(req)
            continue
        if flag in {"-e", "--editable"}:
            target = inline or (args[i + 1] if i + 1 < len(args) else "")
            i += 1 if inline else 2
            if "://" in target or target.startswith("git+"):
                violations.append(f"'{target}' (installs from an unapproved source)")
            continue
        if arg.startswith("-"):
            i += 2 if arg in VALUE_FLAGS else 1
            continue
        specs.append(arg)
        i += 1

    for spec in specs:
        if "://" in spec or spec.startswith("git+"):
            violations.append(f"'{spec}' (installs from an unapproved source)")
            continue
        if (cwd / spec).is_dir():
            continue
        if ecosystem == "node":
            violations.append(f"'{spec}' (Node.js packages are not part of the approved stack)")
            continue
        match = NAME_RE.match(spec)
        if not match or normalize(match.group(1)) not in approved:
            violations.append(f"'{match.group(1) if match else spec}'")
    return violations


def check_command(command: str, cwd: Path, approved: set[str]) -> list[str]:
    violations: list[str] = []
    for segment in SEGMENT_SPLIT.split(command):
        tokens = split_tokens(segment)
        if tokens and Path(tokens[0]).name in SHELLS and "-c" in tokens:
            idx = tokens.index("-c")
            if idx + 1 < len(tokens):
                violations += check_command(tokens[idx + 1], cwd, approved)
            continue
        parsed = install_args(tokens)
        if parsed:
            violations += check_install(*parsed, cwd, approved)
    return violations


def run_hook() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    command = payload.get("command", "")
    cwd = Path(payload.get("cwd") or REPO_ROOT)
    violations = check_command(command, cwd, load_policy(DEFAULT_POLICY))
    if not violations:
        print(json.dumps({"permission": "allow"}))
        return 0

    listed = ", ".join(violations)
    print(
        json.dumps(
            {
                "permission": "deny",
                "user_message": (
                    f"Blocked by IT Policy {POLICY_ID} ({POLICY_NAME}): {listed} not on "
                    "policy/approved-packages.txt. Request an exception from IT Architecture."
                ),
                "agent_message": (
                    f"This install was blocked by IT Policy {POLICY_ID} ({POLICY_NAME}). "
                    f"Not approved: {listed}. Do not retry with another installer, a different "
                    "package name, or by editing policy/approved-packages.txt. Tell the user the "
                    "package is not approved, quote the policy ID, and offer to build the feature "
                    "with the approved stack (FastAPI + Jinja2 server-rendered templates) or to "
                    "file an exception request with IT Architecture."
                ),
            }
        )
    )
    return 0


def run_ci(requirements: Path, policy: Path) -> int:
    approved = load_policy(policy)
    bad = [
        spec
        for spec in requirement_names(requirements)
        if not (m := NAME_RE.match(spec)) or normalize(m.group(1)) not in approved
    ]
    if bad:
        print(f"IT Policy {POLICY_ID} ({POLICY_NAME}) violation in {requirements}:")
        for spec in bad:
            print(f"  - {spec}")
        return 1
    print(f"{requirements}: all packages approved under {POLICY_ID}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-requirements", type=Path)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args()
    if args.check_requirements:
        sys.exit(run_ci(args.check_requirements, args.policy))
    sys.exit(run_hook())
