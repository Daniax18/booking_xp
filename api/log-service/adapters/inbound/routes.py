"""
Routes API — Adaptateur Inbound (Architecture Hexagonale)

📚 Explication Pédagogique :
Les routes FastAPI sont des ADAPTATEURS INBOUND (Driving Adapters).
Elles reçoivent les requêtes HTTP et appellent le domaine via les ports.

Flux complet pour POST /api/v1/system-logs :
1. FastAPI reçoit la requête JSON
2. Pydantic valide les données (schema)
3. La route appelle le LogService (via le port inbound)
4. Le LogService exécute la logique métier
5. Le Repository persiste en DB (via le port outbound)
6. La réponse remonte avec le schéma de sortie

🔗 Synchronisation inter-services :
Les autres services appellent ces endpoints pour centraliser leurs logs.
Le correlation_id est soit fourni par le service appelant, soit
extrait automatiquement du header X-Correlation-ID par le middleware.
"""
from typing import Optional

from sqlalchemy import text

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.inbound.schemas import (
    SystemLogCreateRequest,
    SystemLogResponse,
    SystemLogListResponse,
    AuditLogCreateRequest,
    AuditLogResponse,
    AuditLogListResponse,
    HealthResponse,
)
from adapters.outbound.repositories import (
    PostgresSystemLogRepository,
    PostgresAuditLogRepository,
)
from domain.models.system_log import LogLevel
from domain.services.log_service import LogService
from infrastructure.database import get_db_session
from infrastructure.middleware import get_correlation_id


router = APIRouter(prefix="/api/v1", tags=["Logs"])


def get_log_service(session: AsyncSession) -> LogService:
    """
    Factory pour créer le LogService avec injection de dépendances.
    
    On injecte les repositories concrets (PostgreSQL) dans le service.
    Le service ne sait pas qu'il utilise PostgreSQL !
    """
    system_log_repo = PostgresSystemLogRepository(session)
    audit_log_repo = PostgresAuditLogRepository(session)
    return LogService(system_log_repo, audit_log_repo)


# ────────────────── System Logs ──────────────────

@router.post(
    "/system-logs",
    response_model=SystemLogResponse,
    status_code=201,
    summary="Créer un log système",
    description="Endpoint appelé par les autres microservices pour centraliser leurs logs.",
)
async def create_system_log(
    request: SystemLogCreateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    📌 C'est cet endpoint que auth-service, booking-service, etc. appellent.
    
    Exemple avec httpx (depuis un autre service) :
    ```python
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://log-service:8005/api/v1/system-logs",
            json={"service_name": "auth-service", "level": "INFO", ...},
            headers={"X-Correlation-ID": correlation_id}
        )
    ```
    """
    service = get_log_service(db)

    # Utiliser le correlation_id du body, sinon celui du header
    correlation_id = request.correlation_id or get_correlation_id()

    try:
        log = await service.create_system_log(
            service_name=request.service_name,
            level=LogLevel(request.level),
            message=request.message,
            correlation_id=correlation_id,
            metadata=request.metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SystemLogResponse(
        id=log.id,
        service_name=log.service_name,
        level=log.level.value,
        message=log.message,
        correlation_id=log.correlation_id,
        timestamp=log.timestamp,
        metadata=log.metadata,
    )


@router.get(
    "/system-logs",
    response_model=SystemLogListResponse,
    summary="Lister les logs système",
    description="Récupérer les logs avec filtres optionnels. Utile pour le monitoring.",
)
async def list_system_logs(
    service_name: Optional[str] = Query(None, description="Filtrer par service"),
    level: Optional[str] = Query(None, description="Filtrer par niveau"),
    correlation_id: Optional[str] = Query(None, description="Filtrer par correlation"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    service = get_log_service(db)
    log_level = LogLevel(level) if level else None

    logs = await service.get_system_logs(
        service_name=service_name,
        level=log_level,
        correlation_id=correlation_id,
        limit=limit,
        offset=offset,
    )

    return SystemLogListResponse(
        items=[
            SystemLogResponse(
                id=log.id,
                service_name=log.service_name,
                level=log.level.value,
                message=log.message,
                correlation_id=log.correlation_id,
                timestamp=log.timestamp,
                metadata=log.metadata,
            )
            for log in logs
        ],
        total=len(logs),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/system-logs/correlation/{correlation_id}",
    response_model=list[SystemLogResponse],
    summary="Tracer une requête inter-services",
    description="Récupérer tous les logs d'un même correlation_id pour suivre le parcours d'une requête.",
)
async def get_logs_by_correlation(
    correlation_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    📌 Endpoint clé pour l'observabilité !
    Permet de voir tout ce qui s'est passé pour UNE requête
    à travers TOUS les microservices.
    """
    service = get_log_service(db)
    logs = await service.get_logs_by_correlation_id(correlation_id)

    return [
        SystemLogResponse(
            id=log.id,
            service_name=log.service_name,
            level=log.level.value,
            message=log.message,
            correlation_id=log.correlation_id,
            timestamp=log.timestamp,
            metadata=log.metadata,
        )
        for log in logs
    ]


@router.get(
    "/system-logs/{log_id}",
    response_model=SystemLogResponse,
    summary="Détail d'un log système",
)
async def get_system_log(
    log_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    service = get_log_service(db)
    log = await service.get_system_log_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log non trouvé")

    return SystemLogResponse(
        id=log.id,
        service_name=log.service_name,
        level=log.level.value,
        message=log.message,
        correlation_id=log.correlation_id,
        timestamp=log.timestamp,
        metadata=log.metadata,
    )


# ────────────────── Audit Logs ──────────────────

@router.post(
    "/audit-logs",
    response_model=AuditLogResponse,
    status_code=201,
    summary="Créer un log d'audit",
    description="Tracer une action utilisateur pour conformité et traçabilité.",
)
async def create_audit_log(
    request: AuditLogCreateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    service = get_log_service(db)
    correlation_id = request.correlation_id or get_correlation_id()

    try:
        log = await service.create_audit_log(
            user_id=request.user_id,
            action=request.action,
            entity=request.entity,
            entity_id=request.entity_id,
            correlation_id=correlation_id,
            details=request.details,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity=log.entity,
        entity_id=log.entity_id,
        correlation_id=log.correlation_id,
        timestamp=log.timestamp,
        details=log.details,
    )


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="Lister les logs d'audit",
)
async def list_audit_logs(
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    service = get_log_service(db)

    logs = await service.get_audit_logs(
        user_id=user_id,
        action=action,
        entity=entity,
        limit=limit,
        offset=offset,
    )

    return AuditLogListResponse(
        items=[
            AuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                entity=log.entity,
                entity_id=log.entity_id,
                correlation_id=log.correlation_id,
                timestamp=log.timestamp,
                details=log.details,
            )
            for log in logs
        ],
        total=len(logs),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit-logs/{log_id}",
    response_model=AuditLogResponse,
    summary="Détail d'un log d'audit",
)
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    service = get_log_service(db)
    log = await service.get_audit_log_by_id(log_id)

    if not log:
        raise HTTPException(status_code=404, detail="Log d'audit non trouvé")

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        entity=log.entity,
        entity_id=log.entity_id,
        correlation_id=log.correlation_id,
        timestamp=log.timestamp,
        details=log.details,
    )


# ────────────────── Health Check ──────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check du service",
    description="Vérifie que le service est vivant et que la DB est accessible.",
)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
):
    """
    📌 Endpoint de santé — utilisé par :
    - Docker HEALTHCHECK pour vérifier si le conteneur est sain
    - Le pipeline CI/CD pour valider le déploiement
    - Les autres services pour savoir si log-service est disponible
    - Les load balancers pour le routage du trafic
    """
    try:
        # Vérifier la connexion DB
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="log-service",
        version="1.0.0",
        database=db_status,
    )
