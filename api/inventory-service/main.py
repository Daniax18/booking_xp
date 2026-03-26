# main.py
"""Point d'entrée de l'Inventory Service avec FastAPI."""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import logging
from uuid import UUID
from contextlib import asynccontextmanager

from application.dtos import (
    CreateResourceRequest, CreateResourceResponse, ResourceResponse,
    UpdateResourceRequest, CreateAvailabilitySlotRequest, AvailabilitySlotResponse,
    GetAvailabilityRequest, AvailabilityCheckResponse, ErrorResponse
)
from application.use_cases.create_resource import CreateResource
from application.use_cases.get_resource import GetResource
from application.use_cases.update_resource import UpdateResource
from application.use_cases.get_availability import GetAvailability
from application.use_cases.set_availability import SetAvailability
from domain.repositories.interfaces import ResourceRepository, AvailabilityRepository
from domain.exceptions import DomainException, ResourceNotFound, InvalidDateRange
from infrastructure.databases.async_resource_repo import ResourceRepositoryAsync
from infrastructure.databases.async_availability_repo import AvailabilityRepositoryAsync
from infrastructure.databases.models import Base

# ====== Configuration ======
import os

# PostgreSQL avec driver asyncpg (asynchrone)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://inventory_user:inventory_password@localhost:5432/inventory_db")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# ====== Logging ======
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ====== Database Setup ======
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Async_SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialiser la base de données (créer les tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Fermer les connexions à la base de données."""
    await engine.dispose()


# ====== Lifespan ======
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    logger.info("🚀 Démarrage du service...")
    await init_db()
    logger.info("✅ Base de données initialisée")
    yield
    logger.info("🛑 Arrêt du service...")
    await close_db()
    logger.info("✅ Connexions fermées")


# ====== FastAPI Application ======
app = FastAPI(
    title="Inventory Service",
    description="Service de gestion des ressources et de leur disponibilité",
    version="1.0.0",
    lifespan=lifespan
)

# ====== CORS Middleware ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== Database Dependency ======
async def get_db():
    """Dépendance pour obtenir une session de base de données asynchrone."""
    async with Async_SessionLocal() as session:
        yield session


def get_resource_repo(db: AsyncSession = Depends(get_db)) -> ResourceRepository:
    """Dépendance pour obtenir le repository des ressources."""
    return ResourceRepositoryAsync(db)


def get_availability_repo(db: AsyncSession = Depends(get_db)) -> AvailabilityRepository:
    """Dépendance pour obtenir le repository de disponibilité."""
    return AvailabilityRepositoryAsync(db)


# ====== Exception Handlers ======
@app.exception_handler(ResourceNotFound)
async def resource_not_found_handler(request, exc):
    """Gestionnaire pour les ressources non trouvées."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="RESOURCE_NOT_FOUND",
            message=str(exc),
            timestamp=datetime.now().isoformat()
        ).__dict__
    )


@app.exception_handler(InvalidDateRange)
async def invalid_date_range_handler(request, exc):
    """Gestionnaire pour les plages de dates invalides."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="INVALID_DATE_RANGE",
            message=str(exc),
            timestamp=datetime.now().isoformat()
        ).__dict__
    )


@app.exception_handler(DomainException)
async def domain_exception_handler(request, exc):
    """Gestionnaire pour les exceptions du domaine."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="DOMAIN_ERROR",
            message=str(exc),
            timestamp=datetime.now().isoformat()
        ).__dict__
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Gestionnaire général pour les exceptions non prévues."""
    logger.error(f"Erreur non prévue: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="Une erreur interne s'est produite",
            timestamp=datetime.now().isoformat()
        ).__dict__
    )


# ====== Endpoints Health Check ======
@app.get("/health")
async def health_check():
    """Vérifier l'état du service."""
    return {"status": "healthy", "service": "inventory-service"}


# ====== Endpoints Ressources ======

@app.post("/resources", response_model=dict, status_code=201)
async def create_resource(
    resource_data: CreateResourceRequest,
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Créer une nouvelle ressource."""
    use_case = CreateResource(resource_repo)
    result = await use_case.execute({
        "name": resource_data.name,
        "type": resource_data.type.value,
        "description": resource_data.description,
        "capacity": resource_data.capacity,
        "location": resource_data.location,
        "price": resource_data.price,
    })
    return result


@app.get("/resources/{resource_id}", response_model=dict)
async def get_resource(
    resource_id: str,
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Récupérer les détails d'une ressource."""
    use_case = GetResource(resource_repo)
    result = await use_case.execute(resource_id)
    return result


@app.get("/resources", response_model=List[dict])
async def list_resources(
    type: Optional[str] = Query(None, description="Filtrer par type de ressource"),
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Récupérer la liste de toutes les ressources."""
    use_case = GetResource(resource_repo)
    
    if type:
        results = await use_case.get_resources_by_type(type)
    else:
        results = await use_case.get_all_resources()
    
    return results


@app.put("/resources/{resource_id}", response_model=dict)
async def update_resource(
    resource_id: str,
    resource_data: UpdateResourceRequest,
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Mettre à jour une ressource."""
    use_case = UpdateResource(resource_repo)
    
    update_dict = {}
    for field, value in resource_data.__dict__.items():
        if value is not None:
            update_dict[field] = value
    
    result = await use_case.execute(resource_id, update_dict)
    return result


@app.post("/resources/{resource_id}/deactivate", response_model=dict)
async def deactivate_resource(
    resource_id: str,
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Désactiver une ressource."""
    use_case = UpdateResource(resource_repo)
    result = await use_case.deactivate(resource_id)
    return result


@app.post("/resources/{resource_id}/activate", response_model=dict)
async def activate_resource(
    resource_id: str,
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Activer une ressource."""
    use_case = UpdateResource(resource_repo)
    result = await use_case.activate(resource_id)
    return result


# ====== Endpoints Disponibilité ======

@app.post("/resources/{resource_id}/availability", response_model=dict, status_code=201)
async def create_availability_slot(
    resource_id: str,
    slot_data: CreateAvailabilitySlotRequest,
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Créer un créneau de disponibilité."""
    use_case = SetAvailability(resource_repo, availability_repo)
    
    start_time = datetime.fromisoformat(slot_data.start_time)
    end_time = datetime.fromisoformat(slot_data.end_time)
    
    result = await use_case.execute(
        resource_id,
        start_time,
        end_time,
        slot_data.quantity,
        slot_data.reason_if_unavailable
    )
    
    return result


@app.get("/resources/{resource_id}/availability", response_model=dict)
async def get_availability(
    resource_id: str,
    start_time: str = Query(..., description="Date/heure de début (ISO format)"),
    end_time: str = Query(..., description="Date/heure de fin (ISO format)"),
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Récupérer la disponibilité d'une ressource."""
    use_case = GetAvailability(resource_repo, availability_repo)
    
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)
    
    result = await use_case.execute(resource_id, start, end)
    return result


@app.get("/resources/{resource_id}/availability/check", response_model=dict)
async def check_availability(
    resource_id: str,
    start_time: str = Query(..., description="Date/heure de début (ISO format)"),
    end_time: str = Query(..., description="Date/heure de fin (ISO format)"),
    quantity: int = Query(1, description="Quantité requise"),
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Vérifier si une ressource est disponible pour une période."""
    use_case = GetAvailability(resource_repo, availability_repo)
    
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)
    
    result = await use_case.check_availability(resource_id, start, end, quantity)
    return result


@app.get("/resources/{resource_id}/availability/next-slot", response_model=dict)
async def get_next_available_slot(
    resource_id: str,
    start_time: str = Query(..., description="Date/heure de début (ISO format)"),
    duration_minutes: int = Query(..., description="Durée requise en minutes"),
    availability_repo: AvailabilityRepository = Depends(get_availability_repo),
    resource_repo: ResourceRepository = Depends(get_resource_repo)
):
    """Trouver le prochain créneau disponible."""
    use_case = GetAvailability(resource_repo, availability_repo)
    
    start = datetime.fromisoformat(start_time)
    
    result = await use_case.get_next_available_slot(resource_id, start, duration_minutes)
    return result


# ====== App Startup ======
@app.on_event("startup")
async def startup_event():
    """Événement au démarrage de l'application."""
    logger.info("Inventory Service démarrée")


@app.on_event("shutdown")
async def shutdown_event():
    """Événement à l'arrêt de l'application."""
    logger.info("Inventory Service arrêtée")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level=LOG_LEVEL.lower()
    )
