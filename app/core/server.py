from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.core.config import settings
from app.api.middleware.idempotency import IdempotencyMiddleware
from app.api.v1.tickets import router as tickets_router
from app.api.v1.reservas import router as reservas_router
from app.api.v1.vendedores import router as vendedores_router

# 🔥 CONFIGURAR LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Logger para n8n
logger = logging.getLogger("n8n")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Rate Limiter
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Middlewares
    app.add_middleware(IdempotencyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(reservas_router, prefix=settings.API_V1_STR)
    app.include_router(tickets_router, prefix=settings.API_V1_STR)
    app.include_router(vendedores_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": "SaaS Sistema-Tour API running successfully!"}

    # 🔥 LOG DE INICIO
    logger.info("🚀 API iniciada correctamente")
    logger.info(f"📡 N8N Webhook URL: {settings.N8N_WEBHOOK_URL}")
    logger.info(f"🔑 N8N Header: {settings.N8N_HEADER_NAME}")

    return app