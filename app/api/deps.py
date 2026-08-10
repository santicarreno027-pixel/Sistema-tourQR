# app/api/deps.py
from typing import AsyncGenerator
from app.core.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.security import verificar_admin

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o no proporcionada",
        )
    return api_key_header

def obtener_tenant_autenticado(admin_ctx: dict = Depends(verificar_admin)) -> str:
    """
    Extrae de forma segura el id_empresa desde el JWT verificado por Supabase Auth.
    Garantiza que el usuario no pueda acceder ni modificar datos de otro tenant.
    """
    id_empresa = admin_ctx.get("id_empresa")
    if not id_empresa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de autenticación no asociado a ninguna empresa."
        )
    return id_empresa

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia que abre una sesión con Supabase por cada petición de la API
    y la cierra automáticamente al terminar, garantizando limpieza de recursos.
    """
    async with SessionLocal() as session:
        yield session
        # Al salir del bloque 'with', la sesión hace un rollback automático si no se hizo commit,
        # y cierra la conexión de forma segura.