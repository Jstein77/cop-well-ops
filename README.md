# Well Ops: IT golden template

A small well status app that shows how Emerging Tech / IT standards are built into a project from the first line of code. All well data is synthetic.

## Run it

Requires Python 3.12 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. The SQLite database is created and seeded with 12 synthetic wells in `data/wells.db` on first start.

In local development (`WELL_OPS_ENV=dev`, the default) you are signed in as `WELL_OPS_DEV_USER`. In any other environment, identity comes from the corporate SSO proxy headers. See `.env.example` for all settings.

```bash
ruff check .
pytest -q
```

## What IT enforces, and where

| Standard | Enforced by |
| --- | --- |
| Approved stack, SQL, secrets, auth, logging, tests | Cursor project rules in `.cursor/rules/` |
| Approved packages only (SEC-PKG-001) | Blocking `beforeShellExecution` hook in `.cursor/hooks.json`, plus the CI policy step |
| Security review of every PR | Cursor Bugbot, with repo rules in `.cursor/BUGBOT.md` |
| Lint and tests | GitHub Actions `lint-and-test` check |
| Human accountability | Branch protection on `main`: one approval and a green `lint-and-test` check, no bypass |

## Package policy

`policy/approved-packages.txt` is the list of approved Python packages, owned by IT Architecture. The hook denies any `pip`, `uv`, `poetry`, `pipx`, `conda`, or `npm` install that names a package not on the list and cites the policy in its message. To request a new package, open an Approved Package Request with IT Architecture.
