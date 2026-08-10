# app/api/middleware/auth.py
from fastapi import Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from supabase import create_client
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger("n8n")

# Inicializar cliente de Supabase
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Seguridad para tokens Bearer (para usuarios)
security = HTTPBearer()

# Para API Key de frontend (ya lo tienes)
X_API_KEY_FRONT = APIKeyHeader(name="X-API-Key", auto_error=True)

async def validar_cliente_frontend(api_key: str = Security(X_API_KEY_FRONT)):
    """Valida la API Key del frontend (NEXT.JS)"""
    if api_key != settings.FRONTEND_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: API Key de cliente inválida o ausente."
        )
    return api_key

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica el token JWT de Supabase para usuarios
    """
    token = credentials.credentials
    
    try:
        # Verificar token con Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=401,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_response.user
        
    except Exception as e:
        logger.error(f"❌ Error de autenticación: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Error de autenticación: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user(request: Request):
    """
    Obtiene el usuario actual desde el token
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    try:
        token = auth_header.split(" ")[1]
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        return user_response.user
        
    except IndexError:
        raise HTTPException(status_code=401, detail="Formato de token inválido. Use 'Bearer <token>'")
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuario: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {str(e)}")

async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Obtiene el usuario si existe, pero no falla si no hay token
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None