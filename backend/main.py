from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
