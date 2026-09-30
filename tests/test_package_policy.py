import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".cursor" / "hooks" / "check_packages.py"
spec = importlib.util.spec_from_file_location("check_packages", HOOK)
check_packages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_packages)

APPROVED = check_packages.load_policy(check_packages.DEFAULT_POLICY)
ROOT = HOOK.parents[2]


def run_hook(command: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"command": command, "cwd": str(ROOT)}),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    "command",
    [
        "pip install streamlit",
        "pip3 install -U streamlit==1.40.0",
        "python -m pip install --quiet streamlit",
        ".venv/bin/pip install streamlit",
        "uv pip install streamlit",
        "uv add streamlit",
        "cd app && pip install fastapi streamlit",
        "bash -c 'pip install streamlit'",
        "pip install git+https://github.com/example/pkg.git",
        "npm install left-pad",
    ],
)
def test_denies_unapproved_installs(command):
    decision = run_hook(command)
    assert decision["permission"] == "deny"
    assert "SEC-PKG-001" in decision["user_message"]


@pytest.mark.parametrize(
    "command",
    [
        "pip install fastapi",
        "pip install 'uvicorn[standard]>=0.30'",
        "python3 -m pip install -r requirements.txt",
        "pip install -e .",
        "ls -la",
        "pytest -q",
    ],
)
def test_allows_approved_and_unrelated_commands(command):
    assert run_hook(command) == {"permission": "allow"}


def test_names_are_normalized():
    assert check_packages.check_command("pip install Jinja2 Pydantic_Core", ROOT, APPROVED) == []


def test_requirements_file_is_approved():
    assert check_packages.run_ci(ROOT / "requirements.txt", check_packages.DEFAULT_POLICY) == 0
