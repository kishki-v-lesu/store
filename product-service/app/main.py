import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.api.products import router as products_router
from app.core.config import settings
from app.core.database import engine, Base

logger = logging.getLogger(__name__)

request_counter = Counter('product_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('product_request_duration_seconds', 'Request duration', ['method', 'endpoint'])


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        logger.info(f"[{request_id}] {request.method} {request.url.path}")
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        request_counter.labels(request.method, request.url.path, response.status_code).inc()
        logger.info(f"[{request_id}] Response: {response.status_code}")
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        from app.core.elasticsearch import create_products_index
        await create_products_index()
    except Exception as e:
        logger.warning(f"Failed to create ES index: {e}")
    yield
    logger.info("Shutting down product-service...")
    await engine.dispose()
    try:
        from app.core.elasticsearch import close_es_client
        await close_es_client()
    except Exception:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    app.add_middleware(TracingMiddleware)
    app.include_router(products_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": settings.APP_NAME}

    @app.get("/ready")
    async def readiness_check():
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()