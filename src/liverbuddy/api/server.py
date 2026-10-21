"""Production entry point: the API under /api plus the built web UI (web/dist) at /."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from liverbuddy.api.main import app as api_app
from liverbuddy.config import ROOT

root = FastAPI(title="Liver Buddy", docs_url=None, redoc_url=None, openapi_url=None)
root.mount("/api", api_app)

DIST = ROOT / "web" / "dist"

if (DIST / "assets").exists():
    root.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@root.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    """Serve static files from the build, falling back to index.html for client-side routes."""
    candidate = (DIST / path).resolve()
    if path and candidate.is_file() and DIST.resolve() in candidate.parents:
        return FileResponse(candidate)
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"detail": "Web UI not built. Run `npm run build` in web/, or use `npm run dev`."},
                        status_code=404)
