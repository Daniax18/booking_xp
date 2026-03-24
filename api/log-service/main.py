"""
Log Service — Point d'entrée principal

📚 Explication Pédagogique :
C'est ici que tout est assemblé (Composition Root).
On crée l'application FastAPI, on ajoute les middlewares,
et on configure les événements de démarrage/arrêt.

En architecture hexagonale, le main.py est la "colle" qui
connecte les adaptateurs au domaine.
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.routes import router
from infrastructure.config import get_settings
from infrastructure.database import init_db, close_db
from infrastructure.middleware import CorrelationIdMiddleware
from infrastructure.logging_config import setup_logging


settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    
    - Au démarrage : initialiser la DB et le logging
    - À l'arrêt : fermer proprement les connexions
    
    C'est un pattern recommandé par FastAPI (remplace on_event).
    """
    # ── Démarrage ──
    setup_logging()
    await logger.ainfo("🚀 Log Service démarré", port=settings.SERVICE_PORT)
    await init_db()
    await logger.ainfo("✅ Base de données initialisée")

    yield

    # ── Arrêt ──
    await logger.ainfo("🛑 Log Service en arrêt...")
    await close_db()
    await logger.ainfo("✅ Connexions fermées proprement")


# ── Création de l'application FastAPI ──
app = FastAPI(
    title="📋 Log Service — Booking XP",
    description="""
## Service de centralisation des logs

Ce microservice collecte et centralise les logs de tous les services
de la plateforme de réservation UrbanHub.

### Fonctionnalités :
- **System Logs** : Logs techniques des microservices
- **Audit Logs** : Traçabilité des actions utilisateur
- **Correlation ID** : Suivi des requêtes inter-services
- **Health Check** : Vérification de l'état du service

### Architecture :
- Architecture Hexagonale (Ports & Adapters)
- Database per Service (PostgreSQL dédié)
- Logs structurés JSON avec structlog
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)

# ── Middlewares ──

# CORS : permettre aux autres services d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID : traçabilité automatique
app.add_middleware(CorrelationIdMiddleware)

# ── Routes ──
app.include_router(router)


# ── Endpoint racine ──
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil du service."""
    return {
        "service": "log-service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
