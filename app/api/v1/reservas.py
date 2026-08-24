import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.reserva import ReservaCreate, ReservaResponse, ReservaUpdate, ReservaListResponse
from app.models.reserva import EstadoReserva, EstadoPago
from app.core.database import get_db
from app.api.deps import obtener_tenant_autenticado, verify_api_key
from app.api.middleware.auth import validar_cliente_frontend
from app.services.reserva_service import ReservaService

router = APIRouter(prefix="/reservas", tags=["Reservas"])


@router.post("/", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(validar_cliente_frontend)])
async def crear_reserva_vendedor(
    datos: ReservaCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.crear_reserva(db, datos, background_tasks)


@router.get("/", response_model=ReservaListResponse)
async def obtener_todas_las_reservas(
    id_empresa: str = Depends(obtener_tenant_autenticado),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde esta fecha de servicio"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta esta fecha de servicio"),
    estado: Optional[EstadoReserva] = Query(None, description="Filtrar por estado de reserva"),
    status_pago: Optional[EstadoPago] = Query(None, description="Filtrar por estado contable"),
    busqueda: Optional[str] = Query(None, description="Búsqueda por cliente, tour, folio o teléfono"),
    limit: int = Query(50, ge=1, le=200, description="Cantidad de registros por página"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    db: AsyncSession = Depends(get_db)
):
    return await ReservaService.obtener_todas_las_reservas(
        db=db,
        id_empresa=id_empresa,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado,
        status_pago=status_pago,
        busqueda=busqueda,
        limit=limit,
        offset=offset
    )


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