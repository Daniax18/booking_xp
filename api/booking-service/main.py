from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.inbound.routes import router
from infrastructure.config import get_settings
from infrastructure.database import close_db, init_db
from infrastructure.logging_config import setup_logging
from infrastructure.middleware import AccessLogMiddleware, CorrelationIdMiddleware


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown concerns for the booking service."""
    setup_logging()
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title='Booking Service - Booking XP',
    description='Hexagonal booking service with prepared inventory and payment integrations.',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(AccessLogMiddleware)
app.include_router(router)


@app.get('/', tags=['Root'])
async def root():
    """Return service metadata and useful endpoints."""
    return {
        'service': settings.SERVICE_NAME,
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/api/v1/bookings/health',
    }


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        'main:app',
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
    )
