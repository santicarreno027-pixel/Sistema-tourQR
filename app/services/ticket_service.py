import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reserva import Reserva, EstadoReserva
from app.schemas.reserva import ValidarTicketResult
from app.core.time_utils import combinar_fecha_y_hora

# 🌟 Definimos la zona horaria fija de Quintana Roo (UTC-5 sin horario de verano)
TZ_LOCAL = ZoneInfo("America/Cancun")

class TicketService:
    
    @staticmethod
    def _reserva_a_dict(reserva: Reserva) -> dict:
        """Convierte un objeto Reserva a diccionario para evitar problemas de Pydantic"""
        return {
            "id": reserva.id,
            "folio_fisico": reserva.folio_fisico,
            "cliente_nombre": reserva.cliente_nombre,
            "cliente_telefono": reserva.cliente_telefono,
            "cliente_email": reserva.cliente_email,
            "tour_nombre": reserva.tour_nombre,
            "fecha_servicio": reserva.fecha_servicio,
            "hora_salida": reserva.hora_salida,
            "ubicacion_pickup": reserva.ubicacion_pickup,
            "pax_adultos": reserva.pax_adultos,
            "pax_menores": reserva.pax_menores,
            "pax_infantes": reserva.pax_infantes,
            "id_empresa": reserva.id_empresa,
            "estado": reserva.estado,
            "contador_escaneos": reserva.contador_escaneos,
            "creado_en": reserva.creado_en,
            "primer_escaneo_en": reserva.primer_escaneo_en,
            "ultimo_escaneo_en": reserva.ultimo_escaneo_en,
            # Campos de finanzas (si existen)
            "monto_total": getattr(reserva, 'monto_total', None),
            "monto_deposito": getattr(reserva, 'monto_deposito', None),
            "monto_saldo": getattr(reserva, 'monto_saldo', None),
            "status_pago": getattr(reserva, 'status_pago', None)
        }

    @staticmethod
    async def validar_y_registrar_escaneo(
        db: AsyncSession, 
        ticket_id: uuid.UUID
    ) -> ValidarTicketResult:
        
        # 1. Bloqueo Pesimista atómico dirigido a una sola tabla
        query = (
            select(Reserva)
            .options(joinedload(Reserva.finanzas))
            .where(Reserva.id == ticket_id)
            .with_for_update(of=Reserva)
        )
        result = await db.execute(query)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            return ValidarTicketResult(
                valido=False, 
                mensaje="ERROR: El ticket no existe.", 
                detalles=None
            )

        # 2. Cálculos del Reloj Logístico
        ahora_utc = datetime.now(ZoneInfo("UTC"))
        ahora = ahora_utc.astimezone(TZ_LOCAL)
        
        # 🟢 VARIABLE PLANA DESDE EL INICIO: Limpia de zonas horarias para Postgres
        ahora_db = ahora.replace(tzinfo=None)

        # --- CASO 1: PARQUES / ACTIVIDADES SIN HORA ("OPEN") ---
        if reserva.hora_salida == "OPEN":
            if ahora.date() != reserva.fecha_servicio:
                return ValidarTicketResult(
                    valido=False,
                    mensaje=f"FECHA INCORRECTA: Este pase es válido únicamente para el día {reserva.fecha_servicio}.",
                    detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
                )
            
        # --- CASO 2: TOURS CON HORARIO FIJO (Ventana de 4 horas activa) ---
        else:
            hora_salida_real = combinar_fecha_y_hora(reserva.fecha_servicio, reserva.hora_salida)
            inicio_ventana = hora_salida_real - timedelta(hours=2)
            fin_ventana = hora_salida_real + timedelta(hours=2)

            # --- REGLA AUTOMÁTICA 1: ¿Es muy temprano? ---
            if ahora < inicio_ventana:
                return ValidarTicketResult(
                    valido=False,
                    mensaje=f"TICKET INACTIVO: Tu tour es el {reserva.fecha_servicio} a las {reserva.hora_salida}. El QR se activará 2 horas antes de la salida.",
                    detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
                )

            # --- REGLA AUTOMÁTICA 2: ¿Ya expiró la ventana de 4 horas? ---
            if ahora > fin_ventana:
                estado_nuevo = EstadoReserva.COMPLETADO if reserva.contador_escaneos > 0 else EstadoReserva.CANCELADO
                if reserva.estado != estado_nuevo:
                    reserva.estado = estado_nuevo
                await db.commit()
                await db.refresh(reserva)
                return ValidarTicketResult(
                    valido=False,
                    mensaje="TICKET EXPIRADO: La ventana de 4 horas para utilizar este código ha terminado.",
                    detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
                )

        # --- 3. AUDITORÍA DE ESCANEOS ---
        reserva.contador_escaneos += 1
        
        # 🟢 Forzamos el desprendimiento de tzinfo en la asignación directa
        if reserva.primer_escaneo_en is None:
            reserva.primer_escaneo_en = ahora.astimezone(TZ_LOCAL).replace(tzinfo=None)
        else:
            # Si ya existía en la DB, nos aseguramos de que SQLAlchemy lo trate como naive
            reserva.primer_escaneo_en = reserva.primer_escaneo_en.replace(tzinfo=None)
            
        reserva.ultimo_escaneo_en = ahora.astimezone(TZ_LOCAL).replace(tzinfo=None)
        
        # --- REGLA AUTOMÁTICA 3: Control de Estados en la ventana legal ---
        if reserva.estado == EstadoReserva.CANCELADO:
            await db.commit()
            await db.refresh(reserva)
            return ValidarTicketResult(
                valido=False, 
                mensaje="ERROR: Reserva Cancelada.", 
                detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
            )

        # Si ya está en proceso, es una RE-ENTRADA válida
        if reserva.estado == EstadoReserva.EN_PROCESO:
            await db.commit()
            await db.refresh(reserva)
            return ValidarTicketResult(
                valido=True,
                mensaje="RE-ENTRADA PERMITIDA. Pasajeros a bordo.",
                detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
            )

        # --- CASO DE ÉXITO PUREZA: Primer escaneo real ---
        reserva.estado = EstadoReserva.EN_PROCESO
        
        # Guardamos todo de forma permanente
        await db.commit()
        await db.refresh(reserva)

        return ValidarTicketResult(
            valido=True,
            mensaje=f"ACCESO PERMITIDO. ¡Buen viaje! Adultos: {reserva.pax_adultos}, Menores: {reserva.pax_menores}",
            detalles=TicketService._reserva_a_dict(reserva)  # ✅ Convertir a dict
        )