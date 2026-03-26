"""
Payment Service — Point d'entrée principal

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


settings = get_settings()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    
    - Au démarrage : initialiser la DB
    - À l'arrêt : fermer proprement les connexions
    """
    # ── Démarrage ──
    logger.info("🚀 Payment Service démarré", port=settings.SERVICE_PORT)
    await init_db()
    logger.info("✅ Base de données initialisée")
    
    yield
    
    # ── Arrêt ──
    logger.info("🛑 Payment Service en arrêt...")
    await close_db()
    logger.info("✅ Connexions fermées proprement")


# ── Création de l'application FastAPI ──
app = FastAPI(
    title="💳 Payment Service — Booking XP",
    description="""
## Service de gestion des paiements

Ce microservice gère l'ensemble des transactions de paiement
de la plateforme urbaine.

### Fonctionnalités :
- **Création de paiements** : pour chaque réservation
- **Traitement** : validation auprès du provider (Stripe, PayPal)
- **Remboursements** : total ou partiel
- **Événements** : notifications des autres services (Observer Pattern)
- **Audit** : traçabilité complète de chaque paiement

### Architecture :
- Architecture Hexagonale (Ports & Adapters)
- Database per Service (PostgreSQL dédié)
- Design Patterns : Observer, Decorator, Events
- Structured Logging avec structlog
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middlewares ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
app.include_router(router)


# ── Endpoint racine ──
@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil du service."""
    return {
        "service": "payment-service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/payments/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
