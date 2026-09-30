# Well Ops review rules

These are IT standards for this repo. Flag violations as bugs, with the standard ID.

- **SEC-002 Parameterized SQL.** Any SQL built with f-strings, `%`, `.format()`, or concatenation is a SQL injection bug. So is a router that calls `sqlite3.connect` directly instead of using `get_db`.
- **SEC-003 No secrets in code.** Hardcoded passwords, API keys, tokens, or connection strings are bugs, including in tests. Endpoints gated by a shared password are bugs.
- **SEC-004 Auth.** Any route other than `/health` without `Depends(require_reader)` or another `require_role(...)` dependency is a bug.
- **OPS-001 Logging.** Data access without a `get_logger` audit event, or any `print()`, should be flagged.
- **QA-001 Tests.** New routes without tests in `tests/` should be flagged.
- **SEC-PKG-001 Packages.** Changes to `requirements.txt` that add packages missing from `policy/approved-packages.txt`, and any change to `policy/approved-packages.txt`, should be flagged for IT review.
