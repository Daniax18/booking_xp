import time
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='')
CORRELATION_ID_HEADER = 'X-Correlation-ID'
logger = structlog.get_logger(__name__)


def get_correlation_id() -> str:
    """Return the correlation identifier attached to the current request context."""
    return correlation_id_ctx.get()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach or create a correlation identifier for each HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER, str(uuid.uuid4()))
        token = correlation_id_ctx.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
        finally:
            correlation_id_ctx.reset(token)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Emit structured logs for incoming HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        started_at = time.perf_counter()
        logger.info('booking.api.request.received', method=request.method, path=request.url.path)
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            'booking.api.request.completed',
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
