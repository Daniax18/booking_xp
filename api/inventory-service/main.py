"""Point d'entree FastAPI de l'Inventory Service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.routes import router
from config import get_settings
from infrastructure.database import close_db, init_db


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerer l'initialisation et l'arret des ressources applicatives."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Inventory Service - Booking XP",
    description="Service de gestion des ressources et de leurs disponibilites.",
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
    """Retourner les informations minimales du service inventory."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/inventory/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
