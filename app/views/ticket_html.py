def generar_pantalla_html(color_fondo: str, titulo: str, mensaje: str, detalles_html: str = "") -> str:
    """Genera un HTML responsivo y limpio para el navegador del móvil del guía."""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Validador de Tickets</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: {color_fondo};
                color: white;
                padding: 20px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                text-align: center;
            }}
            .card {{
                background: rgba(0, 0, 0, 0.2);
                padding: 25px;
                border-radius: 18px;
                max-width: 95%;
                width: 420px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }}
            h1 {{ font-size: 2rem; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
            p {{ font-size: 1.1rem; line-height: 1.5; margin-bottom: 20px; opacity: 0.95; }}
            .detalles {{
                background: rgba(255,255,255,0.92);
                color: #333;
                padding: 15px;
                border-radius: 12px;
                text-align: left;
                font-size: 0.95rem;
                margin-bottom: 16px;
                line-height: 1.8;
            }}
            .detalles h3 {{ margin-bottom: 8px; color: #111; border-bottom: 2px solid #eee; padding-bottom: 6px; font-size: 1rem; }}
            .saldo-alerta {{ font-weight: 800; color: #c62828; font-size: 1.3rem; display: block; margin-top: 6px; }}
            .saldo-pagado {{ font-weight: 800; color: #2e7d32; font-size: 1.1rem; }}
            /* FORMULARIO DE COBRO */
            .cobro-box {{
                background: rgba(255,255,255,0.15);
                border: 2px solid rgba(255,255,255,0.4);
                border-radius: 14px;
                padding: 18px;
                margin-top: 10px;
            }}
            .cobro-box h3 {{
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 12px;
                opacity: 0.9;
            }}
            .cobro-input-wrap {{
                display: flex;
                align-items: center;
                background: rgba(255,255,255,0.2);
                border: 2px solid rgba(255,255,255,0.5);
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 12px;
            }}
            .cobro-input-wrap span {{
                font-size: 1.4rem;
                font-weight: 800;
                margin-right: 8px;
                opacity: 0.8;
            }}
            .cobro-input {{
                background: transparent;
                border: none;
                outline: none;
                color: white;
                font-size: 1.6rem;
                font-weight: 800;
                width: 100%;
                text-align: right;
            }}
            .cobro-input::placeholder {{ color: rgba(255,255,255,0.5); font-weight: 400; font-size: 1.2rem; }}
            .btn-cobrar {{
                background: rgba(0,0,0,0.35);
                color: white;
                border: 2px solid rgba(255,255,255,0.6);
                padding: 14px 20px;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 800;
                cursor: pointer;
                width: 100%;
                letter-spacing: 0.5px;
                transition: background 0.2s;
                -webkit-tap-highlight-color: transparent;
            }}
            .btn-cobrar:active {{ background: rgba(0,0,0,0.55); transform: scale(0.98); }}
            .loading-msg {{ display: none; font-size: 0.9rem; opacity: 0.8; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{titulo}</h1>
            <p>{mensaje}</p>
            {detalles_html}
        </div>
    </body>
    </html>
    """


def generar_bloque_cobro_html(reserva_id: str, signature: str, saldo: float) -> str:
    """
    Genera el bloque HTML del formulario de cobro en campo para el guía.
    Se inyecta dentro de detalles_html cuando hay saldo pendiente.
    Llama al endpoint POST /api/v1/tickets/scan/{id}/registrar-abono con la firma de seguridad.
    """
    return f"""
        <div class="cobro-box">
            <h3>💵 Cobrar Saldo en Efectivo</h3>
            <div class="cobro-input-wrap">
                <span>$</span>
                <input 
                    id="monto_cobrar"
                    class="cobro-input" 
                    type="number" 
                    step="0.01" 
                    value="{saldo:.2f}"
                    placeholder="{saldo:.2f}"
                    inputmode="decimal"
                />
            </div>
            <button class="btn-cobrar" onclick="registrarCobro()">
                ✅ Confirmar Cobro Recibido
            </button>
            <p class="loading-msg" id="loading_msg">Registrando pago y embarque...</p>
        </div>

        <script>
        async function registrarCobro() {{
            const montoInput = document.getElementById('monto_cobrar');
            const monto = parseFloat(montoInput.value);
            const loadingMsg = document.getElementById('loading_msg');

            if (!monto || monto <= 0) {{
                alert('Por favor ingresa un monto válido mayor a $0.');
                return;
            }}
            if (!confirm('¿Confirmas haber recibido $' + monto.toFixed(2) + ' MXN en efectivo?')) {{
                return;
            }}

            document.querySelector('.btn-cobrar').disabled = true;
            document.querySelector('.btn-cobrar').innerText = '⏳ Procesando...';
            loadingMsg.style.display = 'block';

            try {{
                const response = await fetch(
                    `/api/v1/tickets/scan/{reserva_id}/registrar-abono?signature={signature}&monto_abono=` + monto,
                    {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }}
                    }}
                );

                const data = await response.json();

                if (response.ok && data.status === 'success') {{
                    const saldoNuevo = data.datos_operacion.saldo_restante;
                    if (saldoNuevo <= 0) {{
                        document.body.style.backgroundColor = '#2e7d32';
                        document.querySelector('.card').innerHTML = `
                            <h1>✅ ¡PAGADO Y EMBARCADO!</h1>
                            <p>Saldo cancelado y acceso confirmado.<br>El turista puede ingresar.</p>
                            <div class="detalles">
                                <h3>Resumen del Cobro</h3>
                                Monto cobrado: <b>$` + data.datos_operacion.monto_abonado.toFixed(2) + ` MXN</b><br>
                                Estado: <span class="saldo-pagado">✅ TOTALMENTE PAGADO</span>
                            </div>
                        `;
                    }} else {{
                        document.querySelector('.card').innerHTML = `
                            <h1>⚠️ PAGO PARCIAL</h1>
                            <p>Cobro registrado. Saldo restante:</p>
                            <div class="detalles">
                                Nuevo saldo pendiente: <span class="saldo-alerta">${{saldoNuevo.toFixed(2)}} MXN</span>
                            </div>
                        `;
                    }}
                }} else {{
                    alert('Error: ' + (data.detail || 'No se pudo registrar el pago.'));
                    document.querySelector('.btn-cobrar').disabled = false;
                    document.querySelector('.btn-cobrar').innerText = '✅ Confirmar Cobro Recibido';
                    loadingMsg.style.display = 'none';
                }}
            }} catch (error) {{
                alert('Error de conexión. Verifica el internet e intenta de nuevo.');
                document.querySelector('.btn-cobrar').disabled = false;
                document.querySelector('.btn-cobrar').innerText = '✅ Confirmar Cobro Recibido';
                loadingMsg.style.display = 'none';
            }}
        }}
        </script>
    """


def generar_bloque_confirmar_html(reserva_id: str, signature: str) -> str:
    """
    Genera el bloque HTML del botón para confirmar el embarque del pasajero de manera explícita (GET/POST separation).
    """
    return f"""
        <div class="confirmar-box" style="margin-top: 15px;">
            <button class="btn-confirmar" onclick="confirmarEmbarque()" style="
                background: rgba(0,0,0,0.3);
                color: white;
                border: 2px solid rgba(255,255,255,0.6);
                padding: 14px 20px;
                border-radius: 12px;
                font-size: 1.2rem;
                font-weight: 800;
                cursor: pointer;
                width: 100%;
                letter-spacing: 0.5px;
                transition: background 0.2s;
                -webkit-tap-highlight-color: transparent;
            ">
                🚀 Confirmar Embarque
            </button>
            <p class="loading-msg" id="loading_msg_confirmar" style="display: none; font-size: 0.9rem; opacity: 0.8; margin-top: 8px;">Registrando embarque...</p>
        </div>

        <script>
        async function confirmarEmbarque() {{
            const btn = document.querySelector('.btn-confirmar');
            const loading = document.getElementById('loading_msg_confirmar');
            
            btn.disabled = true;
            btn.innerText = '⏳ Procesando...';
            loading.style.display = 'block';

            try {{
                const response = await fetch(
                    `/api/v1/tickets/scan/{reserva_id}/confirmar?signature={signature}`,
                    {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }}
                    }}
                );

                const data = await response.json();

                if (response.ok && data.valido) {{
                    document.body.style.backgroundColor = '#1b5e20';
                    document.querySelector('.card').innerHTML = `
                        <h1>🟢 EMBARCADO OK</h1>
                        <p>El embarque del pasajero ha sido registrado correctamente.</p>
                        <div class="detalles">
                            <h3>Resumen del Viaje</h3>
                            Pasajero: <b>` + data.detalles.cliente_nombre + `</b><br>
                            Tour: <b>` + data.detalles.tour_nombre + `</b><br>
                            Escaneos: <b>` + data.detalles.contador_escaneos + `</b>
                        </div>
                    `;
                }} else {{
                    alert('Error: ' + (data.mensaje || 'No se pudo confirmar el embarque.'));
                    btn.disabled = false;
                    btn.innerText = '🚀 Confirmar Embarque';
                    loading.style.display = 'none';
                }}
            }} catch (error) {{
                alert('Error de conexión. Intente de nuevo.');
                btn.disabled = false;
                btn.innerText = '🚀 Confirmar Embarque';
                loading.style.display = 'none';
            }}
        }}
        </script>
    """
