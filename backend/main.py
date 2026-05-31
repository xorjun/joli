import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import init_db
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://joli.arjun.cloud"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from .routers.auth import router as auth_router
from .routers.chat import router as chat_router
from .routers.jobs import router as jobs_router
from .routers.documents import router as documents_router
from .routers.profile import router as profile_router
from .routers.zeugnisse import router as zeugnisse_router

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(jobs_router)
app.include_router(documents_router)
app.include_router(profile_router)
app.include_router(zeugnisse_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


# Serve frontend static files in production
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")
    app.mount("/icons.svg", StaticFiles(directory=STATIC_DIR), name="icons")

    def _serve_file(path: str):
        headers = {}
        if path.endswith(".html"):
            # Always fetch fresh index HTML so new asset hashes are picked up after deploys.
            headers = {"Cache-Control": "no-store, no-cache, must-revalidate"}
        return FileResponse(path, headers=headers)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return _serve_file(file_path)
        return _serve_file(os.path.join(STATIC_DIR, "index.html"))

