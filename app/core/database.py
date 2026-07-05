# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. Crear el motor asíncrono apuntando a Supabase
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Muestra en tu consola local los SQL reales que se ejecutan
    pool_pre_ping=True, # Verifica si la conexión a Supabase sigue viva antes de usarla
    connect_args={
        "statement_cache_size": 0  # 🌟 SOLUCIÓN: Desactiva el caché de sentencias preparadas para PgBouncer
    }
)

# 2. Configurar la fábrica de sesiones asíncronas
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession, 
    expire_on_commit=False 
)

# 3. Clase Base para nuestros modelos
class Base(DeclarativeBase):
    pass

# 4. Generador de sesiones asíncronas para los endpoints de FastAPI
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()