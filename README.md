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

## Deploy to Azure

The app is a single FastAPI process with a SQLite file, so it fits Azure App Service (Linux, Python 3.12) without containers. This repo does not ship a deploy workflow yet; the process below is the target.

### Environments

| Environment | App Service slot | Deployed from |
| --- | --- | --- |
| Test | `staging` slot | Every merge to `main`, after `lint-and-test` passes |
| Production | `production` slot | Manual slot swap, approved in a GitHub `production` environment |

### One-time setup (platform team)

1. **Resource group and plan.** One resource group per app (for example `rg-wellops-prod`), a Linux App Service plan, and a web app with a `staging` slot. Set the startup command to:

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Settings.** Set app settings per slot, never in code. Mark `WELL_OPS_ENV` and `WELL_OPS_DB_PATH` as slot settings so they stay put during a swap.

   | Setting | Value |
   | --- | --- |
   | `WELL_OPS_ENV` | `test` or `prod` (anything but `dev` disables the dev user) |
   | `WELL_OPS_DB_PATH` | `/home/data/wells.db` |
   | `WELL_OPS_LOG_LEVEL` | `INFO` |
   | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` (Oryx runs `pip install -r requirements.txt`) |

   If a future feature needs a secret, store it in Key Vault and reference it from an app setting (`@Microsoft.KeyVault(...)`) using the web app's managed identity.

3. **Storage.** `/home` on App Service is persistent across restarts and deploys, so the SQLite file survives. Everything else on disk is wiped. SQLite on `/home` is fine for this read-heavy, single-instance app. Keep the plan at one instance; scaling out, or real write traffic, means moving to Azure SQL, which needs its own ARCH-001 review.

4. **Identity (SEC-004).** The app trusts the `X-Forwarded-Email` and `X-Forwarded-Groups` headers, so it must be reachable only through the corporate SSO proxy (Entra ID in front, groups mapped to `wellops.*` roles):
   - Put the web app behind the proxy or Application Gateway and disable public network access, or add access restrictions that allow only the proxy's subnet or service tag.
   - Do not turn on App Service Authentication ("Easy Auth") instead. It injects `X-MS-CLIENT-PRINCIPAL-*` headers, which this app does not read.
   - Confirm from outside the network that a request with a hand-set `X-Forwarded-Email` header is rejected before it reaches the app.

5. **Pipeline identity.** Create an Entra app registration with a federated credential for this GitHub repo (OIDC, no client secret), scoped to `Website Contributor` on the resource group. Store only the client, tenant, and subscription IDs as GitHub variables.

6. **Monitoring.** Connect Application Insights and send App Service console logs to Log Analytics. The JSON audit events (`wells.list` and the like) come from stdout, so they show up there without code changes. Point the health check at `/health`.

### Every release

1. Open a PR. `lint-and-test` and Bugbot run, and one reviewer approves.
2. Merge to `main`. A deploy job (`azure/login` with OIDC, then `azure/webapps-deploy`) pushes the commit to the `staging` slot.
3. Smoke test staging through the SSO proxy: `/health` returns 200, the dashboard loads for a `wellops.reader` user, and a user without the role gets 403.
4. An approver in the GitHub `production` environment approves the swap job, which runs `az webapp deployment slot swap --slot staging --target-slot production`.
5. Watch Application Insights for 5xx errors and the audit event volume for 15 minutes.

**Rollback:** swap the slots back. The previous build is still warm in `staging`. The database is not swapped, so any schema change must be backward compatible with the previous release.

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
