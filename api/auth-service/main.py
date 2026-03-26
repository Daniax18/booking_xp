from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.routes import router
from infrastructure.config import get_settings
from infrastructure.database import close_db, init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Auth Service - Booking XP",
    description="Service d'authentification (Hexagonal Architecture).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """Return basic metadata and useful endpoints for the service."""
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/auth/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
