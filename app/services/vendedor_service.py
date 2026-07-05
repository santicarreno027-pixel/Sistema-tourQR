import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.vendedor import VendedorCreate, VendedorUpdate

ADMIN_API_BASE = f"{settings.SUPABASE_URL}/auth/v1/admin/users"
HEADERS_ADMIN = {
    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
    "Content-Type": "application/json",
}


class VendedorService:

    @staticmethod
    def _to_response(user: dict) -> dict:
        metadata = user.get("user_metadata", {}) or {}
        return {
            "id": user.get("id"),
            "email": user.get("email"),
            "nombre": metadata.get("nombre"),
            "rol": metadata.get("rol"),
            "id_empresa": metadata.get("id_empresa"),
            "activo": not bool(user.get("banned_until")),
            "creado_en": user.get("created_at"),
        }

    @staticmethod
    async def crear_vendedor(datos: VendedorCreate, admin_ctx: dict) -> dict:
        # 🌟 Forzamos id_empresa del token del ADMIN, nunca del body, para evitar fuga cross-tenant
        payload = {
            "email": datos.email,
            "password": datos.password,
            "email_confirm": True,
            "user_metadata": {
                "nombre": datos.nombre,
                "rol": datos.rol,
                "id_empresa": admin_ctx["id_empresa"],
            },
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(ADMIN_API_BASE, json=payload, headers=HEADERS_ADMIN, timeout=10.0)

        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=resp.status_code, detail=f"Error creando vendedor: {resp.text}")

        return VendedorService._to_response(resp.json())

    @staticmethod
    async def listar_vendedores(admin_ctx: dict) -> list:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                ADMIN_API_BASE, params={"page": 1, "per_page": 1000}, headers=HEADERS_ADMIN, timeout=10.0
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Error listando vendedores: {resp.text}")

        data = resp.json()
        usuarios = data.get("users", data if isinstance(data, list) else [])

        propios = [
            VendedorService._to_response(u)
            for u in usuarios
            if (u.get("user_metadata") or {}).get("id_empresa") == admin_ctx["id_empresa"]
        ]
        return propios

    @staticmethod
    async def _obtener_usuario_validado(user_id: str, admin_ctx: dict) -> dict:
        """Trae el usuario y valida que pertenezca a la misma empresa del admin."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ADMIN_API_BASE}/{user_id}", headers=HEADERS_ADMIN, timeout=10.0)

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Vendedor no encontrado.")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Error obteniendo vendedor: {resp.text}")

        usuario = resp.json()
        metadata = usuario.get("user_metadata", {}) or {}
        if metadata.get("id_empresa") != admin_ctx["id_empresa"]:
            raise HTTPException(status_code=403, detail="No puedes modificar vendedores de otra empresa.")

        return usuario

    @staticmethod
    async def editar_vendedor(user_id: str, datos: VendedorUpdate, admin_ctx: dict) -> dict:
        usuario_actual = await VendedorService._obtener_usuario_validado(user_id, admin_ctx)
        metadata_actual = usuario_actual.get("user_metadata", {}) or {}

        body = {}

        if datos.nombre is not None:
            metadata_actual["nombre"] = datos.nombre
        if datos.rol is not None:
            metadata_actual["rol"] = datos.rol
        body["user_metadata"] = metadata_actual

        if datos.password is not None:
            body["password"] = datos.password

        if datos.activo is not None:
            body["ban_duration"] = "none" if datos.activo else "876000h"  # ~100 años = baneo indefinido reversible

        async with httpx.AsyncClient() as client:
            resp = await client.put(f"{ADMIN_API_BASE}/{user_id}", json=body, headers=HEADERS_ADMIN, timeout=10.0)

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Error editando vendedor: {resp.text}")

        return VendedorService._to_response(resp.json())

    @staticmethod
    async def desactivar_vendedor(user_id: str, admin_ctx: dict) -> dict:
        """'Eliminar' = baneo reversible, nunca borrado permanente."""
        await VendedorService._obtener_usuario_validado(user_id, admin_ctx)

        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{ADMIN_API_BASE}/{user_id}",
                json={"ban_duration": "876000h"},
                headers=HEADERS_ADMIN,
                timeout=10.0,
            )

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Error desactivando vendedor: {resp.text}")

        return {"status": "success", "mensaje": "Vendedor desactivado. Puede reactivarse después."}