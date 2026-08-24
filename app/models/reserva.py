import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

# =========================================================================
# ENUMS PARA VALIDACIÓN DE ESTADOS (Case-Insensitive)
# =========================================================================
class EstadoReserva(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"

    @classmethod
    def _missing_(cls, value):
        """
        Garantiza que si la base de datos o el cliente envían 'en_proceso', 
        'Pendiente' o cualquier variante, se normalice automáticamente a MAYÚSCULAS.
        """
        if isinstance(value, str):
            value_upper = value.upper()
            for member in cls:
                if member.value == value_upper:
                    return member
        return None


class EstadoPago(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_upper = value.upper()
            for member in cls:
                if member.value == value_upper:
                    return member
        return None
# =========================================================================
# 1. TABLA OPERATIVA: RESERVAS
# =========================================================================
class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        Index("idx_reservas_empresa_fecha", "id_empresa", "fecha_servicio"),
        Index("idx_reservas_empresa_creado", "id_empresa", "creado_en"),
        Index("idx_reservas_empresa_estado", "id_empresa", "estado"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    id_empresa = Column(String(50), nullable=False, index=True)  # ID de la agencia SaaS multi-tenant
    folio_fisico = Column(String(20), nullable=True)
    
    cliente_nombre = Column(String(100), nullable=False)
    cliente_telefono = Column(String(30), nullable=True)
    cliente_email = Column(String(100), nullable=False)
    
    tour_nombre = Column(String(100), nullable=False)
    fecha_servicio = Column(Date, nullable=False, index=True)
    hora_salida = Column(String(30), nullable=True)
    ubicacion_pickup = Column(String(200), nullable=True)
    
    # Desglose de pasajeros
    pax_adultos = Column(Integer, default=1, nullable=False)
    pax_menores = Column(Integer, default=0, nullable=False)
    pax_infantes = Column(Integer, default=0, nullable=False)
    
    # 🌟 SOLUCIÓN: Cambiado a String(30) para emparejar perfectamente con tu VARCHAR de Supabase
    estado = Column(String(30), default=EstadoReserva.PENDIENTE, nullable=False)
    contador_escaneos = Column(Integer, default=0, nullable=False)
    
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
    primer_escaneo_en = Column(DateTime, nullable=True)
    ultimo_escaneo_en = Column(DateTime, nullable=True)

    # Relación virtual 1-a-1 con las finanzas (Borra en cascada si se elimina la reserva)
    finanzas = relationship(
        "FinanzasReserva", 
        back_populates="reserva", 
        uselist=False, 
        cascade="all, delete-orphan"
    )


# =========================================================================
# 2. TABLA CONTABLE: FINANZAS_RESERVAS
# =========================================================================
class FinanzasReserva(Base):
    __tablename__ = "finanzas_reservas"
    __table_args__ = (
        Index("idx_finanzas_empresa_status", "id_empresa", "status_pago"),
    )

    reserva_id = Column(UUID(as_uuid=True), ForeignKey("reservas.id", ondelete="CASCADE"), primary_key=True)
    vendedor_nombre = Column(String(50), nullable=False)
    monto_total = Column(Float, nullable=False)
    monto_deposito = Column(Float, default=0.0, nullable=False)
    monto_saldo = Column(Float, default=0.0, nullable=False)
    
    # 🌟 SOLUCIÓN: Cambiado a String(30) para evitar colisiones de tipos complejos nativos
    status_pago = Column(String(30), default=EstadoPago.PENDIENTE, nullable=False)
    
    # ✅ AGREGAR id_empresa (coincide con la tabla en Supabase)
    id_empresa = Column(String(100), nullable=True, index=True)
    
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relación inversa hacia la tabla operativa de reservas
    reserva = relationship("Reserva", back_populates="finanzas")