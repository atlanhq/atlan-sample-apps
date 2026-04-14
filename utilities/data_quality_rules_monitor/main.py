"""Minimal FastAPI backend that serves the Data Quality Rules Monitor UI.

The app is read-only — every request goes from the React iframe directly
to the tenant's `/api/meta/search/indexsearch` endpoint using the session
JWT delivered via Atlan's postMessage handshake. So this backend only has
one job: serve the built SPA.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

app = FastAPI(title="Data Quality Rules Monitor")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
