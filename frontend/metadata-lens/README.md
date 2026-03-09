# MetadataLens

A frontend app that surfaces all non-null backend attributes for an Atlan asset. It embeds as a tab in the asset profile via the iframe postMessage protocol, or runs standalone for local development.

## Local Development

There are two ways to run locally:

| Mode | What it runs | When to use |
|------|-------------|-------------|
| **Vite dev server** | React only (hot reload) | UI development — fast iteration |
| **App framework** | Python server + built React | Testing the full stack as it runs in production |

### Prerequisites

- Node.js 18+
- Python 3.11+ with [uv](https://docs.astral.sh/uv/) (for app framework mode)
- An Atlan instance with API access
- A valid API token (Settings > API Tokens > Generate)
- A sample asset GUID (grab from the asset URL: `https://tenant.atlan.com/assets/<GUID>/overview`)

### Common setup

```bash
cd frontend/ui
npm install
cp .env.local.example .env.local
```

Edit `frontend/ui/.env.local` with your values:

```env
VITE_DEV_MODE=true
VITE_ATLAN_BASE_URL=https://YOUR_TENANT.atlan.com
VITE_ATLAN_API_TOKEN=your-bearer-token-here
VITE_ATLAN_ASSET_GUID=your-asset-guid-here
```

| Variable | Purpose |
|----------|---------|
| `VITE_DEV_MODE` | Set to `true` to bypass the iframe postMessage handshake |
| `VITE_ATLAN_BASE_URL` | Your Atlan instance URL — Vite proxies `/api/meta/*` here to avoid CORS |
| `VITE_ATLAN_API_TOKEN` | Bearer token for API authentication |
| `VITE_ATLAN_ASSET_GUID` | GUID of the asset whose metadata you want to view |

### Option A: Vite dev server (UI development)

```bash
cd frontend/ui
npm run dev
# → http://localhost:5173
```

This uses the Vite dev server with hot reload. The `VITE_*` env vars are read at runtime, and Vite proxies `/api/meta/*` to your Atlan instance to avoid CORS.

### Option B: App framework (full stack)

This runs the same Python + FastAPI server that runs in production, serving the built React frontend.

```bash
# 1. Build the frontend (bakes .env.local values into the JS bundle)
cd frontend/ui
npm run build

# 2. Start the Python app server with the proxy enabled
cd ../..
ATLAN_BASE_URL=https://YOUR_TENANT.atlan.com uv sync && uv run main.py
# → http://localhost:8000
```

`ATLAN_BASE_URL` is a **shell environment variable** (not a Vite variable). When set, `main.py` registers a reverse proxy that forwards `/api/meta/*` to your Atlan instance. When unset, no proxy is registered — the app behaves exactly as it would in production.

**Important**: `VITE_*` values are baked into the JS bundle at `npm run build` time. So `.env.local` must be configured _before_ you build. If you change env vars, rebuild.

### How the two modes differ

| Concern | Vite dev server | App framework |
|---------|----------------|---------------|
| Frontend served by | Vite (hot reload) | FastAPI (static files) |
| API proxy | Vite `server.proxy` | Python reverse proxy in `main.py` |
| Env vars read | At runtime by Vite | Baked into JS at `npm run build` |
| Port | 5173 | 8000 |
| Use for | UI iteration | Full-stack testing |

### How dev mode works

Normally, the app expects to be embedded in an Atlan iframe that performs a postMessage handshake to provide authentication tokens and the asset GUID. In dev mode:

- The iframe handshake is skipped entirely
- Auth token and asset GUID come from `.env.local` (baked in at build time for app framework mode)
- API calls to `/api/meta/*` are proxied to your Atlan instance — by Vite in dev server mode, or by a reverse proxy route in `main.py` in app framework mode
- The app renders exactly as it would in production, minus the iframe context

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "VITE_ATLAN_API_TOKEN and VITE_ATLAN_ASSET_GUID must be set" | Missing env vars | Check `.env.local` has non-empty values for both |
| `403 Forbidden` in console | Token expired or invalid | Generate a fresh API token from Atlan Settings |
| `404 Not Found` in console | Bad GUID | Verify the GUID exists — open `https://tenant.atlan.com/assets/<GUID>/overview` |
| "Connecting to Atlan" + timeout | Dev mode not enabled | Ensure `VITE_DEV_MODE=true` is in `.env.local` |
| CORS errors | Proxy not configured | Ensure `VITE_ATLAN_BASE_URL` is set in `.env.local` |

## Architecture

```
┌─────────────────────────────┐
│  Atlan UI (parent frame)    │
│  ┌───────────────────────┐  │
│  │  MetadataLens (iframe) │  │  ← postMessage handshake for auth
│  │  ┌─────────────────┐  │  │
│  │  │ AttributesTable  │  │  │  ← searchable table of non-null attributes
│  │  └─────────────────┘  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

### Iframe postMessage flow (production)

```
Atlan parent         MetadataLens iframe
    │                       │
    ├─ ATLAN_HANDSHAKE ────►│
    │◄── IFRAME_READY ──────┤
    ├─ ATLAN_AUTH_CONTEXT ─►│  (token, user, page.params.id = GUID)
    │                       ├─ GET /api/meta/entity/guid/{GUID}
    │                       │  → renders attributes table
    │                       │
    ├─ ATLAN_TOKEN_REFRESH ►│  (proactive refresh before expiry)
    ├─ ATLAN_LOGOUT ───────►│  (clears state)
```

### Dev mode flow

```
.env.local provides token + GUID
    │
    ├─ Skip postMessage entirely
    ├─ GET /api/meta/entity/guid/{GUID}  (via Vite proxy → Atlan instance)
    └─ Render attributes table
```

## Project Structure

```
MetadataLens/
├── main.py                          # Python entry point (application-sdk)
├── pyproject.toml                   # Python dependencies
├── Dockerfile                       # Production container
├── frontend/
│   ├── templates/
│   │   └── index.html               # Production HTML (served by FastAPI)
│   └── static/                      # Vite build output
│       └── assets/
│           ├── index.js
│           └── index.css
└── frontend/ui/                     # React source
    ├── .env.local.example           # Env var template
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html                   # Vite dev entry
    └── src/
        ├── main.tsx                 # React entry point
        ├── App.tsx                  # Orchestrates auth → fetch → display
        ├── types/atlan.ts           # TypeScript types
        ├── hooks/
        │   ├── use-atlan-auth.ts    # postMessage handshake + dev mode
        │   └── use-asset-metadata.ts # Entity fetch + attribute extraction
        ├── services/
        │   └── atlan-api.ts         # API client
        ├── components/
        │   ├── attributes-table.tsx # Searchable attribute table
        │   └── loading-state.tsx    # Loading/error/connecting states
        └── styles/
            └── index.css
```

## Commands

All commands run from `frontend/ui/`:

| Command | Purpose |
|---------|---------|
| `npm install` | Install dependencies |
| `npm run dev` | Start Vite dev server (localhost:5173) |
| `npm run build` | Production build → `frontend/static/` |
| `npm test` | Run tests (Vitest) |
| `npm run test:coverage` | Run tests with coverage report |

## Production Build

For a production build, make sure `.env.local` does **not** have `VITE_DEV_MODE=true` (or delete/rename the file), then:

```bash
cd frontend/ui
npm run build
```

This outputs `frontend/static/assets/index.js` and `index.css` with deterministic filenames. The Python app server (via `application-sdk`) serves these automatically. No proxy is registered since `ATLAN_BASE_URL` won't be set in production — the platform handles `/api/meta/*` natively.

## Tests

```bash
cd frontend/ui
npm test              # 50 tests across 6 files
npm run test:coverage # coverage report (target: 80%+)
```

Test coverage includes:
- postMessage handshake (production path)
- Dev mode auth bypass
- API client with mocked fetch
- Attribute extraction and non-null filtering
- Component rendering, search filtering, value formatting
- Integration test: full auth → fetch → display flow
