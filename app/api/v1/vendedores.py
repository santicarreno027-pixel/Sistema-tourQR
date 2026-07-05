from fastapi import APIRouter, Depends
from app.schemas.vendedor import VendedorCreate, VendedorUpdate, VendedorResponse
from app.services.vendedor_service import VendedorService
from app.core.security import verificar_admin

router = APIRouter(prefix="/vendedores", tags=["Gestión de Vendedores"])


@router.post("/", response_model=VendedorResponse, status_code=201)
async def crear_vendedor(datos: VendedorCreate, admin_ctx: dict = Depends(verificar_admin)):
    return await VendedorService.crear_vendedor(datos, admin_ctx)


@router.get("/", response_model=list[VendedorResponse])
async def listar_vendedores(admin_ctx: dict = Depends(verificar_admin)):
    return await VendedorService.listar_vendedores(admin_ctx)


@router.patch("/{user_id}", response_model=VendedorResponse)
async def editar_vendedor(user_id: str, datos: VendedorUpdate, admin_ctx: dict = Depends(verificar_admin)):
    return await VendedorService.editar_vendedor(user_id, datos, admin_ctx)


@router.delete("/{user_id}")
async def desactivar_vendedor(user_id: str, admin_ctx: dict = Depends(verificar_admin)):
    return await VendedorService.desactivar_vendedor(user_id, admin_ctx)