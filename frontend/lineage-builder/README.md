# Manual Lineage Builder

An embedded Atlan app that lets data stewards create, view, and delete manual lineage connections directly from an asset's profile tab — without leaving Atlan.

Built on the [Atlan Application SDK](https://docs.atlan.com/product/capabilities/build-apps).

## What it does

- Embeds as a tab on Table / View / MaterialisedView asset profiles
- Upstream and downstream lineage creation via asset search
- Shows all existing manual lineage connections for the asset
- Inline delete with confirmation (no browser dialogs — iframe-safe)

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.11+ with [uv](https://docs.astral.sh/uv/)
- An Atlan instance with API access

### Setup

```bash
cd frontend/ui
npm install
cp .env.local.example .env.local
# Edit .env.local with your tenant URL, API token, and a test asset GUID
```

### Option A: Vite dev server (fast UI iteration)

```bash
cd frontend/ui
npm run dev
# → http://localhost:5173
```

Vite proxies `/api/meta/*` to your Atlan tenant. The iframe handshake is bypassed — auth comes from `.env.local`.

### Option B: Full app framework

```bash
# 1. Build the frontend
cd frontend/ui && npm run build

# 2. Run the Python server with dev proxy
cd ../..
DEV_MODE=true ATLAN_BASE_URL=https://your-tenant.atlan.com uv sync && uv run main.py
# → http://localhost:8000
```

## Production Deploy

```bash
# Build frontend (without VITE_DEV_MODE=true)
cd frontend/ui && npm run build

# Docker build
docker build -t atlan-embedded-lineage-builder .
```

In production the platform serves `/api/meta/*` natively — no proxy is registered.

## Project Structure

```
atlan-embedded-lineage-builder/
├── main.py                     # Python entry point (application-sdk)
├── pyproject.toml
├── Dockerfile
├── frontend/
│   ├── templates/index.html    # Production HTML (served by FastAPI)
│   └── static/                 # Vite build output (git-ignored)
└── frontend/ui/
    ├── .env.local.example
    ├── vite.config.ts
    └── src/
        ├── App.tsx
        ├── types/atlan.ts
        ├── hooks/
        │   ├── use-atlan-auth.ts   # postMessage handshake + dev mode
        │   └── use-lineage.ts      # load / create / delete lineage
        ├── services/
        │   └── lineage-api.ts      # All Atlan API calls
        └── components/
            ├── asset-header.tsx
            ├── lineage-form.tsx    # Role toggle + asset search + create
            ├── asset-search.tsx    # Debounced search dropdown
            ├── lineage-list.tsx    # Existing connections with delete
            └── loading-state.tsx
```

## Lineage API notes

- Creates a `Process` asset with `connectorName: manual` and `qualifiedName: manual/lineage/{src}/{tgt}/{uuid}`
- Lineage graph API strips `inputs`/`outputs` from Process entities — the app does a two-step fetch (graph → full entity per process → batch GUID resolution)
- Deletion uses `?deleteType=SOFT`
