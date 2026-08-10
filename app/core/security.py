# app/core/security.py
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import jwt as pyjwt
from jwt import PyJWKClient

# -------------------------------------------------------------------------
# 🔐 VALIDACIÓN DE ADMIN VÍA JWT DE SUPABASE AUTH (firma asimétrica ES256/JWKS)
# -------------------------------------------------------------------------
bearer_scheme = HTTPBearer(auto_error=True)

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
_jwks_client = PyJWKClient(JWKS_URL)  # cachea las llaves públicas internamente


def verificar_admin(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    """
    Decodifica el JWT que emite Supabase Auth al loguear al ADMIN.
    Usa JWKS (llave pública) en vez de secreto compartido, ya que Supabase
    firma con ES256 por default en proyectos nuevos.
    Extrae rol e id_empresa desde user_metadata y bloquea si no es ADMIN.
    """
    token = credentials.credentials
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],  # cubrimos los 3 esquemas posibles de Supabase
            options={"verify_aud": False},
        )
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    metadata = payload.get("user_metadata", {}) or {}
    rol = metadata.get("rol")
    id_empresa = metadata.get("id_empresa")

    if rol != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores.",
        )
    if not id_empresa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token sin id_empresa válido.",
        )

    return {"user_id": payload.get("sub"), "id_empresa": id_empresa, "email": payload.get("email")}


# -------------------------------------------------------------------------
# 🔑 FIRMA DIGITAL HMAC PARA TICKET QR (Stateless & Secure Validation)
# -------------------------------------------------------------------------
import hmac
import hashlib

def generar_firma_ticket(ticket_id: str, id_empresa: str) -> str:
    """
    Genera una firma HMAC de 16 caracteres para un ticket en base al ID y al tenant,
    usando la API_KEY del backend como secreto.
    """
    mensaje = f"{ticket_id}:{id_empresa}".encode()
    return hmac.new(settings.API_KEY.encode(), mensaje, hashlib.sha256).hexdigest()[:16]

def verificar_firma_ticket(ticket_id: str, id_empresa: str, signature: str) -> bool:
    """
    Compara de manera segura (tiempo constante) la firma recibida con la firma esperada.
    """
    if not signature:
        return False
    firma_esperada = generar_firma_ticket(ticket_id, id_empresa)
    return hmac.compare_digest(firma_esperada, signature)