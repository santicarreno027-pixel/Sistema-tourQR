# init_db.py
import os
import sys
import asyncio
import uuid
from datetime import date, datetime, timezone

# --- PARCHE DE RUTAS DE ARQUITECTURA ---
# Agrega la carpeta raíz actual al radar de Python de forma dinámica
ruta_raiz = os.path.abspath(os.path.dirname(__file__))
if ruta_raiz not in sys.path:
    sys.path.insert(0, ruta_raiz)
# ----------------------------------------

from sqlalchemy.ext.asyncio import AsyncSession
# Ahora estas importaciones funcionarán sí o sí, sin importar el entorno
from app.core.database import engine, Base, SessionLocal
from app.models.reserva import Reserva, EstadoReserva
from app.models.idempotency import IdempotencyKey

async def crear_tablas():
    print("Conectando a Supabase y creando tablas...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("¡Tablas creadas exitosamente en Supabase!")

async def insertar_datos_prueba(db: AsyncSession):
    print("Inyectando datos de prueba (Seed)...")
    
    ahora = datetime.now(timezone.utc).replace(tzinfo=None)
    ticket_valido_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    
    reserva_valida = Reserva(
        id=ticket_valido_id,
        agencia_id="agencia-playa-01",
        cliente_nombre="Santiago Carreño",
        tour_nombre="Chichen Itza Classic",
        fecha_tour=date.today(),
        pax_count=2,
        estado=EstadoReserva.NO_PARTIO,
        contador_escaneos=0,
        creado_en=ahora,
        actualizado_en=ahora
    )

    ticket_usado_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    reserva_usada = Reserva(
        id=ticket_usado_id,
        agencia_id="agencia-playa-01",
        cliente_nombre="John Doe",
        tour_nombre="Catamaran Isla Mujeres",
        fecha_tour=date.today(),
        pax_count=1,
        estado=EstadoReserva.EN_PROCESO,
        contador_escaneos=1,
        creado_en=ahora,
        actualizado_en=ahora
    )

    db.add(reserva_valida)
    db.add(reserva_usada)
    
    await db.commit()
    print("\n--- DATOS DE PRUEBA INYECTADOS CON ÉXITO ---")
    print(f"QR Válido (UUID): {ticket_valido_id}")
    print(f"QR Fraudulento/Usado (UUID): {ticket_usado_id}")
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