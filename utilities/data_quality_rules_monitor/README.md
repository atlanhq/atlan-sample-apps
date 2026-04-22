# Data Quality Rules Monitor


Read-only Atlan embedded app that shows the DQ rules linked to the current asset.

Rules are modeled as `CustomEntity` assets under the `Data Quality` connection and linked to their target asset via `applicationQualifiedName`. This app renders them as a single table — table-level rules (exact match) plus column-level rules (prefix match `<tableQn>/<column>`).

## Local dev

Prerequisites: Node.js 20+, Python 3.11+.

```bash
# Frontend dev (hot-reload, hits Atlan directly via Vite proxy)
cd frontend/ui
npm install
cp .env.local.example .env.local   # fill in token + test asset GUID
npm run dev                         # http://localhost:5173

# Backend (only needed to preview the built SPA)
uv sync
npm --prefix frontend/ui run build  # writes to frontend/static
uv run main.py                      # http://localhost:8000
```

The Vite dev server proxies `/api/meta/*` to `VITE_ATLAN_BASE_URL`.

## What it queries

```
POST /api/meta/search/indexsearch
{
  "dsl": {
    "query": {
      "bool": {
        "filter": [
          {"term": {"__typeName.keyword": "CustomEntity"}},
          {"bool": {"should": [
            {"term":   {"applicationQualifiedName.keyword": "<tableQn>"}},
            {"prefix": {"applicationQualifiedName.keyword": "<tableQn>/"}}
          ]}}
        ]
      }
    }
  },
  "attributes": ["name","description","applicationQualifiedName", ...]
}
```

Custom metadata (`DQ.Results`, `DQ.ID`) is returned inline under `entity.businessAttributes.DQ`.
