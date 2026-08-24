import uuid
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
# 🌟 Importamos ambos Enums desde el modelo para mantener la coherencia de tipado
from app.models.reserva import EstadoReserva, EstadoPago

# ==========================================
# 1. ESQUEMA DE ENTRADA (Lo que envía el Frontend del Vendedor)
# ==========================================
class ReservaCreate(BaseModel):
    folio_fisico: Optional[str] = Field(None, max_length=20, description="Número de folio del bloc de papel")
    cliente_nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del pasajero principal")
    cliente_telefono: Optional[str] = Field(None, description="Teléfono de contacto")
    cliente_email: EmailStr = Field(..., description="Correo para envío del voucher y CRM")
    
    tour_nombre: str = Field(..., description="Nombre de la excursión o parque")
    fecha_servicio: date = Field(..., description="Fecha del tour")
    hora_salida: Optional[str] = Field(None, description="Hora de salida (ej: '12:30 PM' o 'OPEN')")
    ubicacion_pickup: Optional[str] = Field(None, description="Punto de encuentro")
    
    pax_adultos: int = Field(default=1, ge=0)
    pax_menores: int = Field(default=0, ge=0)
    pax_infantes: int = Field(default=0, ge=0)
    
    vendedor_nombre: str = Field(..., description="Nombre del staff que vende")
    monto_total: float = Field(..., gt=0, description="Precio total pactado")
    monto_deposito: float = Field(default=0.0, ge=0, description="Dinero cobrado en el momento")
    
    id_empresa: str = Field(..., description="ID de control Multi-tenant para aislar las agencias")

    # ✅ VALIDADOR PARA FECHA EN FORMATO DD-MM-YYYY
    @field_validator('fecha_servicio', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        """Convierte fechas en formato DD-MM-YYYY a objeto date"""
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            # Intentar parsear como DD-MM-YYYY, DD/MM/YYYY o DD.MM.YYYY
            for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y'):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            # Si falla, Pydantic intentará el formato ISO automáticamente
            raise ValueError(f"Formato de fecha inválido. Usa DD-MM-YYYY (ej: 30-06-2026)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "folio_fisico": "04280",
                "cliente_nombre": "test",
                "cliente_telefono": "9841234567",
                "cliente_email": "santicarreno027@gmail.com",
                "tour_nombre": "Cozumel Catamaran",
                "fecha_servicio": "30-06-2026",  # ✅ AHORA ACEPTA DD-MM-YYYY
                "hora_salida": "12:30 PM",
                "ubicacion_pickup": "El Ancla",
                "pax_adultos": 5,
                "pax_menores": 1,
                "pax_infantes": 1,
                "vendedor_nombre": "Gonzalo",
                "monto_total": 8150.0,
                "monto_deposito": 8150.0,
                "id_empresa": "tours-playa-aventura"
            }
        }

# ==========================================
# 2. ESQUEMA DE SALIDA (Para Swagger, n8n y respuestas internas)
# ==========================================
class ReservaResponse(BaseModel):
    id: uuid.UUID
    folio_fisico: Optional[str]
    cliente_nombre: str
    cliente_telefono: Optional[str]
    cliente_email: EmailStr
    tour_nombre: str
    fecha_servicio: date
    hora_salida: Optional[str]
    ubicacion_pickup: Optional[str]
    pax_adultos: int
    pax_menores: int
    pax_infantes: int
    id_empresa: str 
    
    estado_reserva: EstadoReserva
    contador_escaneos: int
    creado_en: datetime
    primer_escaneo_en: Optional[datetime] = None
    ultimo_escaneo_en: Optional[datetime] = None
    
    # Propiedades unificadas desde la relación contable de finanzas
    monto_total: Optional[float] = None
    monto_deposito: Optional[float] = None
    monto_saldo: Optional[float] = None
    
    # 🌟 NUEVA PROPIEDAD: Viaja directo al JSON para que n8n o tu Dashboard lean el estatus de cobro
    status_pago: Optional[EstadoPago] = None

    class Config:
        from_attributes = True

# ==========================================
# 3. ESQUEMA DEL RESULTADO DEL ESCANEO (Cámara del Guía)
# ==========================================
class ValidarTicketResult(BaseModel):
    valido: bool
    mensaje: str
    detalles: Optional[dict] = None  # ← Cambiado a dict

    class Config:
        from_attributes = True

# ==========================================
# 4. ESQUEMAS AUXILIARES (Para cargar el Formulario Frontend)
# ==========================================
class TourInfoResponse(BaseModel):
    tour_nombre: str

class VendedorReporteResponse(BaseModel):
    vendedor_nombre: str
    total_ventas_monto: float
    cantidad_tickets: int

# ==========================================
# 5. SCHEMA DE EDICIÓN (Dashboard del Supervisor)
# ==========================================
class ReservaUpdate(BaseModel):
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[EmailStr] = None
    tour_nombre: Optional[str] = None
    fecha_servicio: Optional[date] = None
    hora_salida: Optional[str] = None
    ubicacion_pickup: Optional[str] = None
    pax_adultos: Optional[int] = Field(None, ge=0)
    pax_menores: Optional[int] = Field(None, ge=0)
    pax_infantes: Optional[int] = Field(None, ge=0)
    folio_fisico: Optional[str] = Field(None, max_length=20)
    monto_total: Optional[float] = Field(None, gt=0)
    
    # ✅ VALIDADOR PARA FECHA EN FORMATO DD-MM-YYYY (también en edición)
    @field_validator('fecha_servicio', mode='before')
    @classmethod
    def parse_fecha(cls, v):
        if v is None:
            return v
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y'):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Formato de fecha inválido. Usa DD-MM-YYYY")
        return v

# ==========================================
# 6. ESQUEMA DE RESPUESTA PAGINADA Y KPIS
# ==========================================
class ReservaKPIsResponse(BaseModel):
    total_reservas: int = 0
    total_ventas: float = 0.0
    con_saldo_pendiente: int = 0
    saldo_total_pendiente: float = 0.0
    total_completadas: int = 0

class ReservaListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ReservaResponse]
    kpis: Optional[ReservaKPIsResponse] = None