import uuid
from typing import List
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.reserva import ReservaCreate, ReservaResponse, ReservaUpdate
from app.core.database import get_db
from app.api.deps import obtener_tenant_autenticado, verify_api_key
from app.api.middleware.auth import validar_cliente_frontend
from app.services.n8n_service import N8nService
from app.services.reserva_service import ReservaService

router = APIRouter(prefix="/reservas", tags=["Reservas Management"])


@router.post("/", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(validar_cliente_frontend)])
async def crear_reserva_vendedor(
    datos: ReservaCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.crear_reserva(db, datos, background_tasks)

@router.get("/", response_model=List[ReservaResponse])
async def obtener_todas_las_reservas(
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.obtener_todas_las_reservas(db, id_empresa)

@router.get("/tours-activos", response_model=None)
async def obtener_lista_de_tours(
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.obtener_lista_de_tours(db, id_empresa)

@router.get("/reporte-vendedor/{vendedor_name}")
async def obtener_reporte_vendedor(
    vendedor_name: str,
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.obtener_reporte_vendedor(db, vendedor_name, id_empresa)

@router.patch("/{reserva_id}/registrar-abono")
async def registrar_abono_manual(
    reserva_id: uuid.UUID, 
    monto_abono: float, 
    background_tasks: BackgroundTasks,
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.registrar_abono_manual(db, reserva_id, monto_abono, id_empresa, background_tasks)

@router.patch("/{reserva_id}/cancelar")
async def cancelar_reserva_manual(
    reserva_id: uuid.UUID, 
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.cancelar_reserva_manual(db, reserva_id, id_empresa)

@router.post("/cron/auditar-tours-pasados", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_api_key)])
async def auditar_tours_pasados(
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.auditar_tours_pasados(db)

@router.get("/{reserva_id}", response_model=ReservaResponse)
async def obtener_reserva_por_id(
    reserva_id: uuid.UUID,
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.obtener_reserva_por_id(db, reserva_id, id_empresa)

@router.patch("/{reserva_id}/editar", response_model=ReservaResponse)
async def editar_reserva(
    reserva_id: uuid.UUID,
    datos: ReservaUpdate,
    id_empresa: str = Depends(obtener_tenant_autenticado),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.editar_reserva(db, reserva_id, id_empresa, datos)

@router.post("/{reserva_id}/reenviar-qr")
async def reenviar_qr(
    reserva_id: uuid.UUID,
    id_empresa: str = Depends(obtener_tenant_autenticado),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.reenviar_qr(db, reserva_id, id_empresa, background_tasks)

@router.post("/test-n8n", dependencies=[Depends(verify_api_key)])
async def test_n8n(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Endpoint de prueba para verificar la conexión con n8n"""
    test_id = uuid.uuid4()
    
    background_tasks.add_task(
        N8nService.notificar_a_n8n,
        test_id,
        "test@example.com",
        "tours-playa-aventura"
    )
    
    return {"status": "success", "message": f"Prueba enviada con ID: {test_id}"}