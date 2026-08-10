import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.schemas.reserva import ReservaCreate, ReservaResponse, ReservaUpdate
from app.models.reserva import Reserva, FinanzasReserva, EstadoReserva, EstadoPago
from app.services.n8n_service import N8nService

TZ_LOCAL = ZoneInfo("America/Cancun")

class ReservaService:

    # ============================================================
    # 🔧 HELPER: Convierte modelo SQLAlchemy a Pydantic Response
    # ============================================================
    @staticmethod
    def _model_to_response(reserva: Reserva, finanzas: Optional[FinanzasReserva] = None) -> ReservaResponse:
        """Convierte un modelo SQLAlchemy Reserva a ReservaResponse para evitar errores de validación."""
        if finanzas is None and hasattr(reserva, 'finanzas'):
            finanzas = reserva.finanzas
            
        return ReservaResponse(
            id=reserva.id,
            folio_fisico=reserva.folio_fisico,
            cliente_nombre=reserva.cliente_nombre,
            cliente_telefono=reserva.cliente_telefono,
            cliente_email=reserva.cliente_email,
            tour_nombre=reserva.tour_nombre,
            fecha_servicio=reserva.fecha_servicio,
            hora_salida=reserva.hora_salida,
            ubicacion_pickup=reserva.ubicacion_pickup,
            pax_adultos=reserva.pax_adultos,
            pax_menores=reserva.pax_menores,
            pax_infantes=reserva.pax_infantes,
            id_empresa=reserva.id_empresa,
            estado_reserva=reserva.estado,
            contador_escaneos=reserva.contador_escaneos,
            creado_en=reserva.creado_en,
            primer_escaneo_en=reserva.primer_escaneo_en,
            ultimo_escaneo_en=reserva.ultimo_escaneo_en,
            monto_total=finanzas.monto_total if finanzas else None,
            monto_deposito=finanzas.monto_deposito if finanzas else None,
            monto_saldo=finanzas.monto_saldo if finanzas else None,
            status_pago=finanzas.status_pago if finanzas else None
        )

    # ============================================================
    # 1. CREAR RESERVA
    # ============================================================
    @staticmethod
    async def crear_reserva(db: AsyncSession, datos: ReservaCreate, background_tasks) -> ReservaResponse:
        nuevo_id = uuid.uuid4()
        saldo_calculado = datos.monto_total - datos.monto_deposito
        
        if saldo_calculado < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto del depósito no puede ser mayor al monto total del tour."
            )

        ahora_local = datetime.now(TZ_LOCAL).replace(tzinfo=None)

        nueva_reserva = Reserva(
            id=nuevo_id,
            id_empresa=datos.id_empresa,
            folio_fisico=datos.folio_fisico,
            cliente_nombre=datos.cliente_nombre,
            cliente_telefono=datos.cliente_telefono,
            cliente_email=datos.cliente_email,
            tour_nombre=datos.tour_nombre,
            fecha_servicio=datos.fecha_servicio,
            hora_salida=datos.hora_salida.strip().upper() if datos.hora_salida else "OPEN",
            ubicacion_pickup=datos.ubicacion_pickup,
            pax_adultos=datos.pax_adultos,
            pax_menores=datos.pax_menores,
            pax_infantes=datos.pax_infantes,
            estado=EstadoReserva.PENDIENTE,
            contador_escaneos=0,
            creado_en=ahora_local
        )

        nuevas_finanzas = FinanzasReserva(
            reserva_id=nuevo_id,
            id_empresa=datos.id_empresa,
            vendedor_nombre=datos.vendedor_nombre,
            monto_total=datos.monto_total,
            monto_deposito=datos.monto_deposito,
            monto_saldo=saldo_calculado,
            status_pago=EstadoPago.PAGADO if saldo_calculado == 0 else EstadoPago.PENDIENTE,
            actualizado_en=ahora_local
        )

        try:
            db.add(nueva_reserva)
            db.add(nuevas_finanzas)
            
            await db.commit()
            await db.refresh(nueva_reserva)
            
            # Notificar a n8n en background
            background_tasks.add_task(N8nService.notificar_a_n8n, nuevo_id, nueva_reserva.cliente_email, datos.id_empresa)
            
            # ✅ Devolver ReservaResponse en lugar del modelo SQLAlchemy
            return ReservaService._model_to_response(nueva_reserva, nuevas_finanzas)

        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error crítico al guardar en la base de datos: {str(e)}"
            )

    # ============================================================
    # 2. OBTENER TODAS LAS RESERVAS
    # ============================================================
    @staticmethod
    async def obtener_todas_las_reservas(db: AsyncSession, id_empresa: str) -> List[ReservaResponse]:
        query = (
            select(Reserva)
            .options(joinedload(Reserva.finanzas))  
            .where(Reserva.id_empresa == id_empresa)
            .order_by(Reserva.creado_en.desc())
        )
        result = await db.execute(query)
        reservas = result.scalars().all()
        
        # ✅ Convertir cada reserva a ReservaResponse
        return [ReservaService._model_to_response(r) for r in reservas]

    # ============================================================
    # 3. OBTENER LISTA DE TOURS (NO CAMBIA - ya devuelve dict)
    # ============================================================
    @staticmethod
    async def obtener_lista_de_tours(db: AsyncSession, id_empresa: str):
        try:
            query = (
                select(
                    Reserva.tour_nombre,
                    Reserva.hora_salida,
                    func.count(Reserva.id).label("total_reservas"),
                    func.sum(Reserva.pax_adultos + Reserva.pax_menores + Reserva.pax_infantes).label("pasajeros_totales_historicos")
                )
                .where(Reserva.id_empresa == id_empresa)
                .group_by(Reserva.tour_nombre, Reserva.hora_salida)
                .order_by(Reserva.tour_nombre.asc(), Reserva.hora_salida.asc())
            )
            
            result = await db.execute(query)
            filas = result.all()
            
            reporte_tours = []
            for fila in filas:
                reporte_tours.append({
                    "tour_nombre": fila.tour_nombre,
                    "hora_salida": fila.hora_salida,
                    "metricas_futuras": {
                        "operaciones_registradas": fila.total_reservas,
                        "volumen_pasajeros_acumulado": int(fila.pasajeros_totales_historicos or 0)
                    }
                })
                
            return {
                "id_empresa": id_empresa,
                "total_tours_configurados": len(reporte_tours),
                "catalogo_tours": reporte_tours
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error interno al compilar el catálogo de tours: {str(e)}"
            )

    # ============================================================
    # 4. OBTENER REPORTE DE VENDEDOR (NO CAMBIA - ya devuelve dict)
    # ============================================================
    @staticmethod
    async def obtener_reporte_vendedor(db: AsyncSession, vendedor_name: str, id_empresa: str):
        try:
            stmt_detalle = (
                select(Reserva)
                .join(Reserva.finanzas)
                .options(joinedload(Reserva.finanzas))
                .where(Reserva.id_empresa == id_empresa)
                .where(FinanzasReserva.vendedor_nombre.ilike(vendedor_name))
                .order_by(Reserva.creado_en.desc())
            )
            
            result_detalle = await db.execute(stmt_detalle)
            reservas_vendedor = result_detalle.scalars().all()

            if not reservas_vendedor:
                return {
                    "vendedor": vendedor_name,
                    "id_empresa": id_empresa,
                    "kpis_globales": {
                        "tickets_vendidos": 0,
                        "total_monto": 0.0,
                        "total_depositos_efectivo": 0.0,
                        "total_saldos_pendientes": 0.0
                    },
                    "tickets": []
                }

            tickets_vendidos = len(reservas_vendedor)
            total_monto = 0.0
            total_depositos = 0.0
            total_saldos = 0.0
            
            lista_tickets = []
            for r in reservas_vendedor:
                monto = r.finanzas.monto_total if (r.finanzas and r.finanzas.monto_total is not None) else 0.0
                deposito = r.finanzas.monto_deposito if (r.finanzas and r.finanzas.monto_deposito is not None) else 0.0
                saldo = r.finanzas.monto_saldo if (r.finanzas and r.finanzas.monto_saldo is not None) else 0.0
                status_pago_actual = r.finanzas.status_pago if r.finanzas else EstadoPago.PENDIENTE
                
                total_monto += monto
                total_depositos += deposito
                total_saldos += saldo
                
                lista_tickets.append({
                    "ticket_id": r.id,
                    "folio_fisico": r.folio_fisico,
                    "cliente_nombre": r.cliente_nombre,
                    "tour_nombre": r.tour_nombre,
                    "fecha_servicio": str(r.fecha_servicio),
                    "hora_salida": r.hora_salida,
                    "estado_reserva": r.estado,
                    "pax_totales": (r.pax_adultos or 0) + (r.pax_menores or 0) + (r.pax_infantes or 0),
                    "finanzas": {
                        "monto_total": float(monto),
                        "monto_deposito": float(deposito),
                        "monto_saldo": float(saldo),
                        "status_pago": status_pago_actual
                    }
                })

            return {
                "vendedor": vendedor_name,
                "id_empresa": id_empresa,
                "kpis_globales": {
                    "tickets_vendidos": tickets_vendidos,
                    "total_monto": round(total_monto, 2),
                    "total_depositos_efectivo": round(total_depositos, 2),
                    "total_saldos_pendientes": round(total_saldos, 2)
                },
                "tickets": lista_tickets
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error interno al compilar el reporte contable: {str(e)}"
            )

    # ============================================================
    # 5. REGISTRAR ABONO MANUAL
    # ============================================================
    @staticmethod
    async def registrar_abono_manual(db: AsyncSession, reserva_id: uuid.UUID, monto_abono: float, id_empresa: str, background_tasks):
        stmt = (
            select(FinanzasReserva)
            .options(joinedload(FinanzasReserva.reserva))  
            .where(FinanzasReserva.reserva_id == reserva_id)
            .where(FinanzasReserva.id_empresa == id_empresa)
        )
        result = await db.execute(stmt)
        finanzas = result.scalar_one_or_none()
        
        if not finanzas:
            raise HTTPException(status_code=404, detail="Registro financiero no encontrado en esta empresa.")
        
        if finanzas.status_pago == EstadoPago.PAGADO or finanzas.monto_saldo <= 0:
            return {
                "status": "info",
                "mensaje": "Esta reserva ya se encuentra totalmente pagada.",
                "saldo_restante": 0.0,
                "status_pago": finanzas.status_pago
            }
            
        saldo_anterior = finanzas.monto_saldo if finanzas.monto_saldo is not None else 0.0
        saldo_nuevo = saldo_anterior - monto_abono
        
        if saldo_nuevo < 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Error: El abono (${monto_abono:,.2f}) es mayor que el saldo pendiente (${saldo_anterior:,.2f})."
            )
            
        deposito_actual = finanzas.monto_deposito if finanzas.monto_deposito is not None else 0.0
        finanzas.monto_deposito = deposito_actual + monto_abono
        finanzas.monto_saldo = saldo_nuevo
        finanzas.actualizado_en = datetime.now(TZ_LOCAL).replace(tzinfo=None)
        
        if saldo_nuevo == 0:
            finanzas.status_pago = EstadoPago.PAGADO
        else:
            finanzas.status_pago = EstadoPago.PENDIENTE
        
        await db.commit()
        
        if finanzas.status_pago == EstadoPago.PAGADO:
            id_empresa_real = finanzas.reserva.id_empresa if finanzas.reserva else "unknown"
            background_tasks.add_task(N8nService.notificar_liquidacion_a_n8n, reserva_id, id_empresa_real)
        
        return {
            "status": "success",
            "mensaje": "¡Abono registrado con éxito!",
            "datos_operacion": {
                "saldo_anterior": float(saldo_anterior),
                "monto_abonado": float(monto_abono),
                "saldo_restante": float(saldo_nuevo),
                "status_pago": finanzas.status_pago
            }
        }

    # ============================================================
    # 6. CANCELAR RESERVA
    # ============================================================
    @staticmethod
    async def cancelar_reserva_manual(db: AsyncSession, reserva_id: uuid.UUID, id_empresa: str):
        stmt = select(Reserva).where(Reserva.id == reserva_id).where(Reserva.id_empresa == id_empresa)
        result = await db.execute(stmt)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            raise HTTPException(status_code=404, detail="La reserva no existe en esta empresa.")
        
        reserva.estado = EstadoReserva.CANCELADO
        await db.commit()
        
        return {"status": "success", "mensaje": "Reserva cancelada. El QR ahora mostrará pantalla roja."}

    # ============================================================
    # 7. AUDITAR TOURS PASADOS (NO CAMBIA - ya devuelve dict)
    # ============================================================
    @staticmethod
    async def auditar_tours_pasados(db: AsyncSession):
        hoy_local = datetime.now(TZ_LOCAL).date()
        
        try:
            stmt = (
                select(Reserva)
                .where(Reserva.fecha_servicio < hoy_local)  
                .where(Reserva.estado.in_([EstadoReserva.PENDIENTE, EstadoReserva.EN_PROCESO]))
            )
            
            result = await db.execute(stmt)
            reservas_a_auditar = result.scalars().all()
            
            total_completados = 0
            total_no_shows = 0
            
            for reserva in reservas_a_auditar:
                if reserva.contador_escaneos > 0:
                    reserva.estado = EstadoReserva.COMPLETADO
                    total_completados += 1
                else:
                    reserva.estado = EstadoReserva.CANCELADO
                    total_no_shows += 1
                
            if (total_completados + total_no_shows) > 0:
                await db.commit()
                
            return {
                "status": "success",
                "mensaje": "Auditoría nocturna de seguridad completada con éxito.",
                "métricas": {
                    "tours_ejecutados_completados": total_completados,
                    "cupones_expirados_no_show": total_no_shows,
                    "total_registros_procesados": total_completados + total_no_shows
                }
            }
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error crítico en el motor de auditoría interna: {str(e)}"
            )

    # ============================================================
    # 8. OBTENER RESERVA POR ID
    # ============================================================
    @staticmethod
    async def obtener_reserva_por_id(db: AsyncSession, reserva_id: uuid.UUID, id_empresa: str) -> ReservaResponse:
        query = (
            select(Reserva)
            .options(joinedload(Reserva.finanzas))
            .where(Reserva.id == reserva_id)
            .where(Reserva.id_empresa == id_empresa)
        )
        result = await db.execute(query)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            raise HTTPException(status_code=404, detail="La reserva no existe en esta empresa.")
        
        # ✅ Devolver ReservaResponse
        return ReservaService._model_to_response(reserva)

    # ============================================================
    # 9. EDITAR RESERVA
    # ============================================================
    @staticmethod
    async def editar_reserva(db: AsyncSession, reserva_id: uuid.UUID, id_empresa: str, datos: ReservaUpdate) -> ReservaResponse:
        query = (
            select(Reserva)
            .options(joinedload(Reserva.finanzas))
            .where(Reserva.id == reserva_id)
            .where(Reserva.id_empresa == id_empresa)
        )
        result = await db.execute(query)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            raise HTTPException(status_code=404, detail="La reserva no existe en esta empresa.")
        
        # Actualizar solo los campos enviados (PATCH parcial)
        update_data = datos.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            if campo == 'monto_total' and reserva.finanzas:
                # Si cambia el monto total, recalculamos el saldo
                deposito_actual = reserva.finanzas.monto_deposito or 0
                nuevo_saldo = valor - deposito_actual
                if nuevo_saldo < 0:
                    raise HTTPException(status_code=400, detail="El monto total no puede ser menor al anticipo ya registrado.")
                reserva.finanzas.monto_total = valor
                reserva.finanzas.monto_saldo = nuevo_saldo
                reserva.finanzas.status_pago = EstadoPago.PAGADO if nuevo_saldo == 0 else EstadoPago.PENDIENTE
                reserva.finanzas.actualizado_en = datetime.now(TZ_LOCAL).replace(tzinfo=None)
            else:
                setattr(reserva, campo, valor)
        
        await db.commit()
        await db.refresh(reserva)
        
        # ✅ Devolver ReservaResponse
        return ReservaService._model_to_response(reserva)

    # ============================================================
    # 10. REENVIAR QR (NO CAMBIA - ya devuelve dict)
    # ============================================================
    @staticmethod
    async def reenviar_qr(db: AsyncSession, reserva_id: uuid.UUID, id_empresa: str, background_tasks):
        query = select(Reserva).where(Reserva.id == reserva_id).where(Reserva.id_empresa == id_empresa)
        result = await db.execute(query)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            raise HTTPException(status_code=404, detail="La reserva no existe en esta empresa.")
        
        background_tasks.add_task(N8nService.notificar_a_n8n, reserva_id, reserva.cliente_email, id_empresa)
        
        return {"status": "success", "mensaje": f"QR reenviado al correo {reserva.cliente_email} correctamente."}