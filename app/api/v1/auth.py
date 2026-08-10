# app/api/v1/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.api.middleware.auth import verify_token
from app.api.middleware.auth import verify_token
from supabase import create_client
from app.core.config import settings
import logging

logger = logging.getLogger("n8n")

router = APIRouter()

# Inicializar Supabase
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Modelos de datos
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: Optional[str] = None
    telefono: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/auth/login")
async def login(request: LoginRequest):
    """
    Iniciar sesión con email y password
    """
    try:
        logger.info(f"🔐 Intento de login: {request.email}")
        
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        logger.info(f"✅ Login exitoso: {request.email}")
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "nombre": response.user.user_metadata.get("nombre", response.user.email),
                "telefono": response.user.user_metadata.get("telefono", ""),
                "created_at": response.user.created_at
            }
        }
    except Exception as e:
        logger.error(f"❌ Error de login: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Credenciales inválidas: {str(e)}"
        )

@router.post("/auth/register")
async def register(request: RegisterRequest):
    """
    Registrar un nuevo usuario
    """
    try:
        logger.info(f"📝 Registro de usuario: {request.email}")
        
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "nombre": request.nombre or request.email,
                    "telefono": request.telefono or ""
                }
            }
        })
        
        if not response.user:
            raise HTTPException(status_code=400, detail="Error al crear usuario")
        
        logger.info(f"✅ Usuario registrado: {request.email}")
        
        return {
            "message": "Usuario creado exitosamente",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "nombre": response.user.user_metadata.get("nombre", response.user.email),
                "telefono": response.user.user_metadata.get("telefono", ""),
                "created_at": response.user.created_at
            }
        }
    except Exception as e:
        logger.error(f"❌ Error de registro: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error de registro: {str(e)}")

@router.post("/auth/logout")
async def logout():
    """
    Cerrar sesión
    """
    try:
        supabase.auth.sign_out()
        logger.info("🔒 Logout exitoso")
        return {"message": "Sesión cerrada exitosamente"}
    except Exception as e:
        logger.error(f"❌ Error al cerrar sesión: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error al cerrar sesión: {str(e)}")

@router.post("/auth/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """
    Refrescar el token de acceso
    """
    try:
        response = supabase.auth.refresh_session(request.refresh_token)
        logger.info("🔄 Token refrescado exitosamente")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except Exception as e:
        logger.error(f"❌ Error al refrescar token: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Error al refrescar token: {str(e)}")

@router.get("/auth/me")
async def get_me(current_user = Depends(verify_token)):
    """
    Obtener información del usuario autenticado
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre": current_user.user_metadata.get("nombre", current_user.email),
        "telefono": current_user.user_metadata.get("telefono", ""),
        "created_at": str(current_user.created_at)
    }