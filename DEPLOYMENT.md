# Deployment — ResearchCollision

Production topology: FastAPI backend on **Render**, Vite/React frontend on **Vercel**.
All values below were verified against the repository on 2026-09-30 (commit `5924c3d`).

---

## Frontend — Vercel

| Setting | Value |
| --- | --- |
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Install Command | default (`npm install`; `frontend/package-lock.json` is committed) |
| Build Command | `npm run build` (`tsc -b && vite build`) |
| Output Directory | `dist` |
| Node version | set explicitly in the dashboard (no `.nvmrc`/`engines` in repo) |

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | **yes, in production** | Full API base, e.g. `https://<render-host>/api/v1`. Vite inlines `VITE_*` at **build time**, so changing it requires a new deployment. |

`frontend/src/lib/api.ts` resolves its base URL as:

```ts
baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/v1"
```

When the variable is unset the app falls back to the relative `/api/v1`, which the
local Vite dev server proxies to `http://localhost:8000`
(`frontend/vite.config.ts`). No backend hostname is hardcoded in source.

### `vercel.json` and SPA routing

The app uses `BrowserRouter` (`frontend/src/main.tsx`), so a hard refresh on
`/login`, `/workspace/:id`, etc. must fall back to `index.html`. `vercel.json`
adds that rewrite:

```json
{ "rewrites": [ { "source": "/(.*)", "destination": "/index.html" } ] }
```

Vercel serves existing static files before applying rewrites, so hashed assets
under `dist/assets/` are still served normally.

**Placement:** Vercel reads `vercel.json` from the project's **Root Directory**.
Identical copies exist at `frontend/vercel.json` (correct when Root Directory is
`frontend`) and `vercel.json` (correct when Root Directory is the repository root
and the build runs from `frontend/`). Vercel ignores whichever file sits outside
the configured Root Directory, so the extra copy is inert. Delete the one that
does not match your project's Root Directory once it is confirmed.

---

## Backend — Render (Web Service)

| Setting | Value |
| --- | --- |
| Root Directory | `backend` |
| Runtime | Python (set `PYTHON_VERSION` to the 3.11 line used by `backend/Dockerfile`) |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Pre-Deploy Command | `alembic upgrade head` |
| Health Check Path | `/health` |

### Environment variables

| Variable | Required | Why |
| --- | --- | --- |
| `SECRET_KEY` | **yes** | JWT signing. Defaults to a value generated per process (`backend/app/core/config.py:25`), so without it every deploy/restart invalidates all sessions. |
| `APP_ENV` | **yes** (`production`) | Selects INFO logging over DEBUG (`backend/app/main.py:64`). |
| `CORS_ORIGINS` | **yes** | Comma-separated browser origin allowlist. Defaults to localhost only (`backend/app/core/config.py:26`), which blocks the Vercel origin. |
| `DATABASE_URL` | **yes in practice** | Defaults to local SQLite; set it explicitly to control where the database lives. |
| `RUN_WORKER_IN_APP` | **yes** (`true`) | Starts the embedded job worker in the API process. |
| `LLM_PROVIDER` | **yes** (`mock` for a key-free demo) | `mock` keeps the demo free of paid providers. |
| `EMBEDDING_PROVIDER` | **yes** (`mock`) | `sentence_transformer` is **not** in `requirements.txt`; it needs an extra install and downloads a model at runtime. |
| `PYTHON_VERSION` | **yes** | Platform-level setting; not read by application code. Pins the runtime to match `backend/Dockerfile`. |

Optional: `LITERATURE_PROVIDER`, `OPENALEX_EMAIL`, `SEMANTIC_SCHOLAR_API_KEY`,
`CROSSREF_EMAIL`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`,
`LLM_MODEL`, `RATE_LIMIT_REQUESTS_PER_MINUTE`, `MAX_UPLOAD_SIZE_MB`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `STRUCTURED_MAX_TOKENS`, `LLM_TIMEOUT_SECONDS`.
Defaults are documented in `.env.example`.

**CORS** needs no code change — `backend/app/main.py` already reads
`CORS_ORIGINS` at startup. Set it to the exact production origin, e.g.
`CORS_ORIGINS=https://researchcollision.vercel.app`. Keep explicit origins:
`allow_credentials=True` is enabled and tokens are sent from `localStorage`
(`frontend/src/lib/api.ts`), so `*` is not usable.

---

## Database migrations

Migrations are **required** before the app serves traffic: nothing calls
`create_all` at startup (`backend/app/db/database.py`), so an unmigrated
database makes queries fail.

```
cd backend && python -m alembic upgrade head
```

The project already ships one revision, `eaae242b764c` (initial schema), and
`backend/alembic/env.py` reads the URL from `DATABASE_URL`. On Render with Root
Directory `backend`, the pre-deploy command is simply `alembic upgrade head`.

---

## Deployment constraint: exactly one backend instance

The job queue has **no row-level locking**. `claim_next_pending()` is a plain
`SELECT ... WHERE status = 'PENDING' ORDER BY created_at LIMIT 1` followed by a
status flip (`backend/app/db/repositories/job_repository.py`); its docstring
states "single-worker MVP". The guard in `backend/app/workers/worker.py` is an
in-process `asyncio.Lock`.

Consequences for hosting:

- Run **one** Render instance.
- Never start the API with multiple uvicorn workers (`--workers >1`), and never
  run the standalone worker (`python -m app.workers.worker`) alongside an
  embedded worker (`RUN_WORKER_IN_APP=true`) — two workers would claim and run
  the same job.
- Scaling out requires adding `with_for_update(skip_locked=True)` to the claim
  query (or an external queue) first. That is a code change, deliberately out of
  scope for deployment configuration.

Because the worker lives inside the web process, any platform sleep/restart also
stops in-flight discovery jobs. Use an always-on instance for a live demo.

---

## Health check

`GET /health` is served at the app root, **not** under `/api/v1`
(`backend/app/main.py`). It does not touch the database, and rate limiting and
access logging explicitly skip it, so it is safe as the platform probe.

Production URL: `https://<render-host>/health`

Example response:

```json
{"status": "ok", "app_env": "production", "mock_mode": true, "time": 1790750520.3}
```

`scripts/health_check.py` performs a deeper check (tables, FTS index) and is
useful manually, but it is not required by the platform.

---

## Known limitations in hosted environments

- **SQLite is ephemeral on Render.** The default database file lives on the
  container disk, so it is lost on every deploy, restart, and free-tier
  spin-down. For a throwaway demo, re-run `alembic upgrade head` after each
  deploy. For persistence, use a managed Postgres database — note that
  `requirements.txt` ships **no Postgres driver**, so that switch requires
  adding one first. FTS5 search degrades to `LIKE` matching automatically
  (`backend/app/db/repositories/paper_repository.py`).
- **Uploaded CV blobs** are written to `data/uploads/` and are lost on redeploy;
  the extracted text is stored in the database, so profiles keep working.
- **Rate limiting** is in-memory and per process, and buckets by
  `request.client.host`. Behind Render's proxy that can be a shared address, and
  limits reset on restart. Adequate for a demo, not for production traffic.
- **`/docs`** is publicly exposed by default.
- Workspaces are private to their owner; there is no multi-user sharing.
