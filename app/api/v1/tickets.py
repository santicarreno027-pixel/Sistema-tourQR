import uuid
from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.ticket_service import TicketService
from app.services.reserva_service import ReservaService
from app.core.database import get_db
from app.api.deps import verify_api_key
from app.views.ticket_html import generar_pantalla_html, generar_bloque_cobro_html, generar_bloque_confirmar_html

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# =========================================================================
# ENDPOINT PÚBLICO: Escaneo QR desde el celular del guía
# =========================================================================
@router.get("/scan/{ticket_id}", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def escanear_codigo_qr(
    request: Request,
    ticket_id: uuid.UUID,
    signature: str = "",
    db: AsyncSession = Depends(get_db)
):
    """
    Ruta de solo lectura (GET) que valida la firma digital y muestra el estado del ticket.
    No realiza escrituras en la base de datos para evitar falsos positivos por bots.
    """
    # 1. Obtener detalles de la reserva sin mutar
    reserva = await TicketService.obtener_detalles_reserva(db, ticket_id)
    if not reserva:
        return generar_pantalla_html(
            color_fondo="#d32f2f", # Rojo
            titulo="❌ TICKET INVÁLIDO",
            mensaje="ERROR: El ticket no existe o fue eliminado."
        )

    # 2. Validar Firma Digital para prevenir IDOR y enumeración de UUIDs
    from app.core.security import verificar_firma_ticket
    if not verificar_firma_ticket(str(ticket_id), reserva.id_empresa, signature):
        return generar_pantalla_html(
            color_fondo="#d32f2f", # Rojo
            titulo="🛑 ACCESO DENEGADO",
            mensaje="Firma digital del ticket inválida o ausente. Por favor, escanee el código QR original."
        )

    # 3. Evaluar reglas de negocio en memoria (lectura)
    resultado = await TicketService.validar_ticket_lectura(db, ticket_id)

    # --- CASO 1: ERROR DE FECHA O CADUCIDAD (PANTALLA ROJA / AMARILLA) ---
    if not resultado.valido:
        if "INACTIVO" in resultado.mensaje.upper():
            return generar_pantalla_html(
                color_fondo="#fbc02d", # Amarillo
                titulo="⏳ QR INACTIVO",
                mensaje=resultado.mensaje
            )
            
        return generar_pantalla_html(
            color_fondo="#d32f2f", # Rojo
            titulo="🛑 ACCESO DENEGADO",
            mensaje=resultado.mensaje,
            detalles_html=f"""
                <div class="detalles">
                    <h3>Datos de la Reserva:</h3>
                    <b>Cliente:</b> {reserva.cliente_nombre}<br>
                    <b>Tour:</b> {reserva.tour_nombre}<br>
                    <b>Estado actual:</b> {reserva.estado}<br>
                    <b>Escaneos totales:</b> {reserva.contador_escaneos}
                </div>
            """
        )

    # --- CASO 2: TICKET VÁLIDO ---
    # Obtener saldo de finanzas de la reserva
    saldo_real = reserva.finanzas.monto_saldo if reserva.finanzas and reserva.finanzas.monto_saldo is not None else 0.0

    if saldo_real > 0:
        saldo_txt = f'<span class="saldo-alerta">⚠️ SALDO PENDIENTE: ${saldo_real:,.2f} MXN</span>'
    else:
        saldo_txt = '<span class="saldo-pagado">✅ ¡TODO PAGADO!</span>'

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

    # Si hay saldo pendiente → pantalla naranja + formulario de cobro seguro
    if saldo_real > 0:
        bloque_cobro = generar_bloque_cobro_html(
            reserva_id=str(ticket_id),
            signature=signature,
            saldo=saldo_real
        )
        return generar_pantalla_html(
            color_fondo="#e65100",  # Naranja fuerte
            titulo="⚠️ SALDO PENDIENTE",
            mensaje=f"Cobrar ${saldo_real:,.2f} MXN en campo para poder embarcar",
            detalles_html=detalles_base_html + bloque_cobro
        )

    # Sin saldo / Re-entrada válida → pantalla verde con botón de Confirmar Embarque
    if reserva.estado == "EN_PROCESO":
        # Si ya está embarcado, informamos al guía que es una re-entrada
        return generar_pantalla_html(
            color_fondo="#388e3c",
            titulo="🟢 RE-ENTRADA OK",
            mensaje="Pasajeros a bordo. Este ticket ya fue verificado.",
            detalles_html=detalles_base_html
        )
    
    # Si está PENDIENTE de confirmación, mostramos el botón explícito de confirmación
    bloque_confirmar = generar_bloque_confirmar_html(
        reserva_id=str(ticket_id),
        signature=signature
    )
    return generar_pantalla_html(
        color_fondo="#0288d1", # Azul - Listo para embarcar
        titulo="👍 TICKET VÁLIDO",
        mensaje="Haga clic a continuación para registrar la entrada del pasajero.",
        detalles_html=detalles_base_html + bloque_confirmar
    )


# =========================================================================
# ENDPOINTS SEGUROS FIRMADOS CON HMAC (Acciones del Guía en el Campo)
# =========================================================================
@router.post("/scan/{ticket_id}/confirmar")
async def confirmar_embarque_publico(
    ticket_id: uuid.UUID,
    signature: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Ruta de confirmación de embarque (POST). Valida la firma del QR antes de procesar.
    """
    reserva = await TicketService.obtener_detalles_reserva(db, ticket_id)
    if not reserva:
        return {"valido": False, "mensaje": "La reserva no existe."}

    from app.core.security import verificar_firma_ticket
    if not verificar_firma_ticket(str(ticket_id), reserva.id_empresa, signature):
        return {"valido": False, "mensaje": "Firma digital del ticket inválida."}

    return await TicketService.confirmar_embarque_ticket(db, ticket_id)


@router.post("/scan/{ticket_id}/registrar-abono")
async def registrar_abono_publico(
    ticket_id: uuid.UUID,
    signature: str,
    monto_abono: float,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Ruta para que el guía registre un abono de saldo pendiente en efectivo en el campo.
    Validado mediante firma digital en lugar de requerir credenciales locales.
    """
    reserva = await TicketService.obtener_detalles_reserva(db, ticket_id)
    if not reserva:
        return {"status": "error", "detail": "La reserva no existe."}

    from app.core.security import verificar_firma_ticket
    if not verificar_firma_ticket(str(ticket_id), reserva.id_empresa, signature):
        return {"status": "error", "detail": "Firma digital del ticket inválida."}

    # Llamar al servicio para registrar el abono manual
    resultado = await ReservaService.registrar_abono_manual(
        db=db,
        reserva_id=ticket_id,
        monto_abono=monto_abono,
        id_empresa=reserva.id_empresa,
        background_tasks=background_tasks
    )

    # Si se liquidó por completo ($0 de saldo), confirmamos de forma automática el embarque
    if resultado.get("status") == "success" and resultado["datos_operacion"]["saldo_restante"] <= 0:
        await TicketService.confirmar_embarque_ticket(db, ticket_id)

    return resultado


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
    ✅ CON AUTENTICACIÓN - Protegido (Solo lectura)
    """
    resultado = await TicketService.validar_ticket_lectura(db, ticket_id)
    detalles = resultado.detalles or {}
    return {
        "valido": resultado.valido,
        "mensaje": resultado.mensaje,
        "detalles": {
            "id": str(detalles.get("id")) if detalles.get("id") else None,
            "cliente_nombre": detalles.get("cliente_nombre"),
            "tour_nombre": detalles.get("tour_nombre"),
            "estado": detalles.get("estado"),
            "contador_escaneos": detalles.get("contador_escaneos", 0),
            "monto_saldo": detalles.get("monto_saldo"),
            "status_pago": detalles.get("status_pago")
        }
    }