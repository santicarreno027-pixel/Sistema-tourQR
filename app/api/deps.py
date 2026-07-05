# app/api/deps.py
from typing import AsyncGenerator
from app.core.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no proporcionada",
        )
    return api_key_header

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia que abre una sesión con Supabase por cada petición de la API
    y la cierra automáticamente al terminar, garantizando limpieza de recursos.
    """
    async with SessionLocal() as session:
        yield session
        # Al salir del bloque 'with', la sesión hace un rollback automático si no se hizo commit,
        # y cierra la conexión de forma segura.