"""
Middleware Correlation ID

📚 Explication Pédagogique :
Le correlation_id est UN des concepts les plus importants en microservices.

Scénario : Un client fait une réservation
1. Requête arrive au API Gateway → génère correlation_id = "abc-123"
2. auth-service reçoit "abc-123" → log avec ce correlation_id
3. booking-service reçoit "abc-123" → log avec ce correlation_id
4. payment-service reçoit "abc-123" → log avec ce correlation_id
5. inventory-service reçoit "abc-123" → log avec ce correlation_id

Résultat : On peut chercher "abc-123" dans les logs centralisés
et voir TOUT ce qui s'est passé pour cette réservation !

Ce middleware :
- Extrait le correlation_id du header HTTP "X-Correlation-ID"
- Si absent, en génère un nouveau (UUID)
- Le stocke dans un contexte accessible partout dans la requête
- L'ajoute dans le header de la réponse
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar = variable thread-safe accessible dans toute la requête
# C'est comme un "thread-local" mais compatible avec asyncio
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str:
    """Récupérer le correlation_id du contexte actuel."""
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui gère automatiquement le correlation_id
    pour chaque requête HTTP entrante.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Lire le correlation_id du header (s'il existe)
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER,
            str(uuid.uuid4())  # Sinon, en générer un nouveau
        )

        # 2. Stocker dans le contexte de la requête
        token = correlation_id_ctx.set(correlation_id)

        try:
            # 3. Exécuter la requête
            response = await call_next(request)

            # 4. Ajouter le correlation_id dans la réponse
            response.headers[CORRELATION_ID_HEADER] = correlation_id

            return response
        finally:
            # 5. Nettoyer le contexte
            correlation_id_ctx.reset(token)
