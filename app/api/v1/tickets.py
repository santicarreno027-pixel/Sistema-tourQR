import uuid
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.ticket_service import TicketService
from app.core.database import get_db
from app.api.deps import verify_api_key
from app.views.ticket_html import generar_pantalla_html, generar_bloque_cobro_html

limiter = Limiter(key_func=get_remote_address)

# =========================================================================
# 🔥 ROUTER SIN AUTENTICACIÓN GLOBAL
# =========================================================================
router = APIRouter(prefix="/tickets", tags=["Tickets Scanner"])

# =========================================================================
# ENDPOINT PÚBLICO: Escaneo QR desde el celular del guía
# ✅ SIN AUTENTICACIÓN - Público para que funcione desde cualquier dispositivo
# =========================================================================
@router.get("/scan/{ticket_id}", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def escanear_codigo_qr(
    request: Request,
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Ruta que se ejecuta al escanear el QR desde la cámara normal del celular.
    Procesa las reglas de ventana de 4 horas y devuelve una interfaz HTML de color.
    ✅ SIN AUTENTICACIÓN - Pública
    """
    # 1. Ejecutamos la matemática del servicio
    resultado = await TicketService.validar_y_registrar_escaneo(db, ticket_id)
    reserva = resultado.detalles

    # --- CASO 1: ERROR O ACCESO DENEGADO (PANTALLA ROJA / AMARILLA) ---
    if not resultado.valido:
        # Si el ticket ni siquiera existe
        if not reserva:
            return generar_pantalla_html(
                color_fondo="#d32f2f", # Rojo
                titulo="❌ TICKET INVÁLIDO",
                mensaje=resultado.mensaje
            )
        
        # Si está inactivo todavía (PANTALLA AMARILLA)
        if "INACTIVO" in resultado.mensaje or "INACTIVO" in resultado.mensaje.upper():
            return generar_pantalla_html(
                color_fondo="#fbc02d", # Amarillo
                titulo="⏳ QR INACTIVO",
                mensaje=resultado.mensaje
            )
            
        # Si ya expiró o es fraude (PANTALLA ROJA)
        return generar_pantalla_html(
            color_fondo="#d32f2f", # Rojo
            titulo="🛑 ACCESO DENEGADO",
            mensaje=resultado.mensaje,
            detalles_html=f"""
                <div class="detalles">
                    <h3>Datos del Intento:</h3>
                    <b>Cliente:</b> {getattr(reserva, 'cliente_nombre', 'N/A')}<br>
                    <b>Tour:</b> {getattr(reserva, 'tour_nombre', 'N/A')}<br>
                    <b>Escaneos totales:</b> {getattr(reserva, 'contador_escaneos', 0)}
                </div>
            """
        )

    # --- CASO 2: ACCESO VÁLIDO O RE-ENTRADA (PANTALLA VERDE) ---
    saldo_real = 0
    
    try:
        # Consultamos directamente a la tabla de finanzas usando el ID de la reserva
        # Esto evita fallos si SQLAlchemy limpió la relación en memoria tras el refresh
        from sqlalchemy import select
        from app.models.reserva import FinanzasReserva 
        
        stmt_finanzas = select(FinanzasReserva).where(FinanzasReserva.reserva_id == ticket_id)
        res_finanzas = await db.execute(stmt_finanzas)
        finanzas_obj = res_finanzas.scalar_one_or_none()
        
        if finanzas_obj:
            saldo_real = finanzas_obj.monto_saldo if finanzas_obj.monto_saldo is not None else 0
            
    except Exception as e:
        print(f"⚠️ Error al consultar finanzas directamente: {e}")
        saldo_real = 0

    # Determinar el mensaje y estilo del estatus de pago
    if saldo_real > 0:
        saldo_txt = f'<span class="saldo-alerta">⚠️ SALDO PENDIENTE: ${saldo_real:,.2f} MXN</span>'
    else:
        saldo_txt = '<span class="saldo-pagado">✅ ¡TODO PAGADO!</span>'

    # Detalles base del pasajero
    detalles_base_html = f"""
        <div class="detalles">
            <h3>Detalles del Tour:</h3>
            <b>Pasajero:</b> {reserva.cliente_nombre}<br>
            <b>Tour:</b> {reserva.tour_nombre}<br>
            <b>Punto de Encuentro:</b> {reserva.ubicacion_pickup or 'No especificado'}<br>
            <b>Hora de Salida:</b> {reserva.hora_salida or 'N/A'}<br>
            <hr>
            <b>Adultos:</b> {reserva.pax_adultos} | 
            <b>Menores:</b> {reserva.pax_menores} | 
            <b>Infantes:</b> {reserva.pax_infantes}<br>
            <hr>
            <b>Estatus de Pago:</b> {saldo_txt}
        </div>
    """

    # Si hay saldo pendiente → pantalla naranja + formulario de cobro en campo
    if saldo_real > 0:
        bloque_cobro = generar_bloque_cobro_html(
            reserva_id=str(ticket_id),
            saldo=saldo_real
        )
        return generar_pantalla_html(
            color_fondo="#e65100",  # Naranja fuerte = ojo, hay saldo
            titulo="⚠️ SALDO PENDIENTE",
            mensaje=f"Cobrar ${saldo_real:,.2f} MXN antes de embarcar",
            detalles_html=detalles_base_html + bloque_cobro
        )

    # Sin saldo → pantalla verde de bienvenida
    titulo_verde = "🟢 RE-ENTRADA OK" if "RE-ENTRADA" in resultado.mensaje.upper() else "✅ BIENVENIDO"
    return generar_pantalla_html(
        color_fondo="#388e3c",
        titulo=titulo_verde,
        mensaje=resultado.mensaje,
        detalles_html=detalles_base_html
    )


# =========================================================================
# ENDPOINTS PROTEGIDOS (requieren API Key)
# =========================================================================
@router.get("/admin/estado/{ticket_id}")
async def obtener_estado_ticket(
    ticket_id: uuid.UUID,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para consultar estado del ticket (solo admin/guía autorizado)
    ✅ CON AUTENTICACIÓN - Protegido
    """
    resultado = await TicketService.validar_y_registrar_escaneo(db, ticket_id)
    return {
        "valido": resultado.valido,
        "mensaje": resultado.mensaje,
        "detalles": {
            "id": str(resultado.detalles.id) if resultado.detalles else None,
            "cliente_nombre": resultado.detalles.cliente_nombre if resultado.detalles else None,
            "tour_nombre": resultado.detalles.tour_nombre if resultado.detalles else None,
            "estado": resultado.detalles.estado if resultado.detalles else None,
            "contador_escaneos": resultado.detalles.contador_escaneos if resultado.detalles else 0
        }
    }


@router.get("/admin/listas")
async def listas_tickets(
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Listas todos los tickets (solo admin)
    ✅ CON AUTENTICACIÓN - Protegido
    """
    from sqlalchemy import select
    from app.models.reserva import Reserva
    
    stmt = select(Reserva).order_by(Reserva.creado_en.desc()).limit(100)
    result = await db.execute(stmt)
    reservas = result.scalars().all()
    
    return {
        "total": len(reservas),
        "tickets": [
            {
                "id": str(r.id),
                "cliente": r.cliente_nombre,
                "tour": r.tour_nombre,
                "estado": r.estado,
                "fecha": r.fecha_servicio.isoformat() if r.fecha_servicio else None
            }
            for r in reservas
        ]
    }