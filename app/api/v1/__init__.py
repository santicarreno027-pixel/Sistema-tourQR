# app/api/v1/__init__.py
from .auth import router as auth_router
from .tickets import router as tickets_router
from .reservas import router as reservas_router
from .vendedores import router as vendedores_router

__all__ = [
    "auth_router",
    "tickets_router",
    "reservas_router",
    "vendedores_router"
]