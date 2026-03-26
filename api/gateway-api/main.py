"""Exposer l'API Gateway de Booking XP.

Ce module centralise deux responsabilites principales:
- securiser les appels entrants avec un JWT sur toutes les routes protegees;
- router les requetes HTTP vers le microservice interne approprie.

Le gateway laisse uniquement les routes de login et de register accessibles
sans authentification afin que les autres services puissent, pour l'instant,
deleguer entierement la verification des tokens a cette couche.

## TODO : Verification de sécurité pour chaque service ou on laisse gateway seulement
"""

from functools import lru_cache
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Definir la configuration d'execution de l'API Gateway.

    Les valeurs sont chargees depuis les variables d'environnement puis mises
    en cache afin de partager la meme configuration entre le proxy HTTP, la
    validation JWT et les reglages reseau.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SERVICE_NAME: str = "gateway-api"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    DEBUG: bool = False

    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    INVENTORY_SERVICE_URL: str = "http://inventory-service:8002"
    BOOKING_SERVICE_URL: str = "http://booking-service:8003"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8004"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"

    CORS_ORIGINS: str = "*"
    HTTP_TIMEOUT_SECONDS: float = 30.0


@lru_cache
def get_settings() -> Settings:
    """Retourner la configuration mise en cache du gateway."""
    return Settings()


settings = get_settings()

## TODO : Verifier les api des autres services une fois tout est mergé
SERVICE_ROUTES: dict[str, str] = {
    "/api/v1/auth": settings.AUTH_SERVICE_URL,
    "/api/v1/inventory": settings.INVENTORY_SERVICE_URL,
    "/api/v1/booking": settings.BOOKING_SERVICE_URL,
    "/api/v1/bookings": settings.BOOKING_SERVICE_URL,
    "/api/v1/payment": settings.PAYMENT_SERVICE_URL,
    "/api/v1/payments": settings.PAYMENT_SERVICE_URL,
}

PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/health",
    "/",
}

HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


app = FastAPI(
    title="Gateway API - Booking XP",
    description="API Gateway charge de la securite JWT et du routage vers les microservices.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_target_service(path: str) -> str | None:
    """Resoudre le service cible a partir du chemin demande.

    Args:
        path: Chemin HTTP entrant, par exemple ``/api/v1/auth/login``.

    Returns:
        L'URL de base du microservice cible si un prefixe correspond, sinon
        ``None``.
    """
    matching_prefixes = sorted(SERVICE_ROUTES.keys(), key=len, reverse=True)
    for prefix in matching_prefixes:
        if path == prefix or path.startswith(f"{prefix}/"):
            return SERVICE_ROUTES[prefix]
    return None


def _build_upstream_headers(request: Request) -> dict[str, str]:
    """Construire les en-tetes a transmettre au microservice cible.

    Args:
        request: Requete HTTP recue par le gateway.

    Returns:
        Un dictionnaire d'en-tetes sans les hop-by-hop headers, enrichi avec
        ``x-forwarded-for`` et ``x-forwarded-proto`` pour conserver le contexte
        du client d'origine.
    """
    forwarded_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    client_host = request.client.host if request.client else "unknown"
    forwarded_headers["x-forwarded-for"] = client_host
    forwarded_headers["x-forwarded-proto"] = request.url.scheme
    return forwarded_headers


def _build_gateway_response(upstream_response: httpx.Response) -> Response:
    """Transformer la reponse d'un microservice en reponse FastAPI.

    Args:
        upstream_response: Reponse brute retournee par le microservice appele.

    Returns:
        Une ``Response`` FastAPI prete a etre renvoyee au client, avec les
        en-tetes autorises et le contenu original.
    """
    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


def _decode_token(token: str) -> dict[str, Any]:
    """Decoder et valider un token Bearer recu par le gateway.

    Args:
        token: JWT transmis dans l'en-tete ``Authorization``.

    Returns:
        Les claims du token decode si la signature et l'expiration sont valides.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Verifier l'authentification avant de laisser passer la requete.

    Args:
        request: Requete HTTP entrante interceptee par le middleware.
        call_next: Fonction FastAPI appelee pour poursuivre la chaine middleware.

    Returns:
        La reponse generee par la suite de la pile applicative, ou une reponse
        ``401`` si le token est absent ou invalide.
    """
    if request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    if _get_target_service(request.url.path) is None:
        return await call_next(request)

    authorization = request.headers.get("authorization")
    if not authorization:
        return Response(
            content='{"detail":"Not authenticated"}',
            media_type="application/json",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return Response(
            content='{"detail":"Invalid authorization header"}',
            media_type="application/json",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        claims = _decode_token(token)
    except JWTError:
        return Response(
            content='{"detail":"Token invalide ou expire"}',
            media_type="application/json",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not claims.get("sub"):
        return Response(
            content='{"detail":"Token invalide: claim sub manquant"}',
            media_type="application/json",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.state.jwt_claims = claims
    return await call_next(request)


@app.get("/", tags=["Root"])
async def root():
    """Retourner les informations minimales de presentation du gateway."""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Retourner un etat de sante simple pour le gateway."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
    }


@app.api_route(
    "/api/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_request(full_path: str, request: Request):
    """Relayer une requete API vers le microservice approprie.

    Args:
        full_path: Portion dynamique capturee apres ``/api/`` dans l'URL.
        request: Requete HTTP complete recue par le gateway.

    Returns:
        La reponse du microservice cible, retransmise au client apres filtrage
        des en-tetes non transferables.

    Raises:
        HTTPException: Si aucun service n'est mappe pour le chemin demande ou
        si le microservice cible est indisponible.
    """
    _ = full_path
    target_service = _get_target_service(request.url.path)
    if not target_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No upstream service configured for path '{request.url.path}'",
        )

    upstream_url = httpx.URL(f"{target_service}{request.url.path}").copy_merge_params(request.query_params)
    headers = _build_upstream_headers(request)

    claims = getattr(request.state, "jwt_claims", None)
    if claims:
        headers["x-user-id"] = str(claims.get("sub", ""))
        headers["x-user-email"] = str(claims.get("email", ""))
        headers["x-user-role"] = str(claims.get("role", ""))

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            upstream_response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
                cookies=request.cookies,
            )
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream service unavailable for path '{request.url.path}'",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gateway request error while calling '{request.url.path}'",
        ) from exc

    return _build_gateway_response(upstream_response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
