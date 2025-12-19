# Data SLA Monitor (React) — Compatible with App Framework default UI routes

This UI is structured to work with the **default** `BaseApplication.register_ui_routes()`:

```python
def register_ui_routes(self):
    self.app.get("/")(self.frontend_home)
    self.app.mount("/", StaticFiles(directory="frontend/static"), name="static")
```

## Key implications

1. `GET /` is served by `frontend_home` (usually rendering `frontend/templates/index.html`).
2. Static files are mounted at **root (`/`)**, so JS/CSS must be referenced as **`/assets/...`**.
3. There is no catch-all route for SPA deep links. This demo is intentionally a single-page UI.

## Structure

- `frontend/ui/` → React source (Vite)
- `frontend/templates/index.html` → template rendered by `frontend_home`
- `frontend/static/` → built assets served by StaticFiles mount

## Build

```bash
cd frontend/ui
npm install
npm run build
```

After build, you will see:

- `frontend/static/assets/index.js`
- `frontend/static/assets/index.css`

## Dev

```bash
cd frontend/ui
npm install
npm run dev
```

The dev server is just for local UI iteration.