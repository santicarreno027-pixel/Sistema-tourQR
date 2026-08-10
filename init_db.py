# init_db.py
import os
import sys
import asyncio
import uuid
from datetime import date, datetime, timezone

# --- PARCHE DE RUTAS DE ARQUITECTURA ---
ruta_raiz = os.path.abspath(os.path.dirname(__file__))
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)
# ----------------------------------------

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, Base, SessionLocal
from app.models.reserva import Reserva, FinanzasReserva, EstadoReserva, EstadoPago
from app.models.idempotency import IdempotencyKey


async def crear_tablas():
    print("Conectando a Supabase y creando tablas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("¡Tablas creadas exitosamente en Supabase!")


async def insertar_datos_prueba(db: AsyncSession):
    print("Inyectando datos de prueba (Seed)...")

    ahora = datetime.now(timezone.utc).replace(tzinfo=None)

    # --- TICKET 1: Válido, sin escanear todavía, con saldo pendiente ---
    ticket_valido_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

    reserva_valida = Reserva(
        id=ticket_valido_id,
        id_empresa="agencia-playa-01",
        folio_fisico="TEST-001",
        cliente_nombre="Santiago Carreño",
        cliente_telefono="9841234567",
        cliente_email="santiago@example.com",
        tour_nombre="Chichen Itza Classic",
        fecha_servicio=date.today(),
        hora_salida="OPEN",
        ubicacion_pickup="Hotel Test",
        pax_adultos=2,
        pax_menores=0,
        pax_infantes=0,
        estado=EstadoReserva.PENDIENTE,
        contador_escaneos=0,
        creado_en=ahora
    )

    finanzas_validas = FinanzasReserva(
        reserva_id=ticket_valido_id,
        vendedor_nombre="Gonzalo",
        monto_total=2000.0,
        monto_deposito=1000.0,
        monto_saldo=1000.0,
        status_pago=EstadoPago.PENDIENTE,
        actualizado_en=ahora
    )

    # --- TICKET 2: Ya usado / en proceso, totalmente pagado ---
    ticket_usado_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    reserva_usada = Reserva(
        id=ticket_usado_id,
        id_empresa="agencia-playa-01",
        folio_fisico="TEST-002",
        cliente_nombre="John Doe",
        cliente_telefono="9847654321",
        cliente_email="johndoe@example.com",
        tour_nombre="Catamaran Isla Mujeres",
        fecha_servicio=date.today(),
        hora_salida="OPEN",
        ubicacion_pickup="Hotel Test",
        pax_adultos=1,
        pax_menores=0,
        pax_infantes=0,
        estado=EstadoReserva.EN_PROCESO,
        contador_escaneos=1,
        creado_en=ahora,
        primer_escaneo_en=ahora,
        ultimo_escaneo_en=ahora
    )

    finanzas_usadas = FinanzasReserva(
        reserva_id=ticket_usado_id,
        vendedor_nombre="Gonzalo",
        monto_total=1500.0,
        monto_deposito=1500.0,
        monto_saldo=0.0,
        status_pago=EstadoPago.PAGADO,
        actualizado_en=ahora
    )

    db.add_all([reserva_valida, finanzas_validas, reserva_usada, finanzas_usadas])

    await db.commit()
    print("\n--- DATOS DE PRUEBA INYECTADOS CON ÉXITO ---")
    print(f"QR Válido, con saldo pendiente (UUID): {ticket_valido_id}")
    print(f"QR Ya usado, pagado (UUID): {ticket_usado_id}")
    print("--------------------------------------------\n")


async def main():
    await crear_tablas()
    async with SessionLocal() as session:
        try:
            await insertar_datos_prueba(session)
        except Exception as e:
            print(f"Aviso: No se pudieron insertar los datos (es posible que ya existan): {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(main())