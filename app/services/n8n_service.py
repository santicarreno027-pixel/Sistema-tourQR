import uuid
import httpx
import asyncio
import logging
import json
from app.core.config import settings

# Logger específico para n8n
logger = logging.getLogger("n8n")

class N8nService:
    HEADERS_SEGURIDAD_N8N = {
        "Content-Type": "application/json",
        settings.N8N_HEADER_NAME: settings.N8N_HEADER_PASSWORD
    }

    @classmethod
    async def notificar_a_n8n(cls, reserva_id: uuid.UUID, cliente_email: str, id_empresa: str):
        """
        Envía datos a n8n para emisión de QR inicial con pool optimizado y tolerancia a fallos.
        """
        payload = {
            "reserva_id": str(reserva_id),
            "id_empresa": id_empresa,
            "cliente_email": cliente_email,
            "evento": "reserva_creada"
        }

        # 🔥 LOGS EXTREMADAMENTE DETALLADOS
        print("=" * 60)
        print("🚀 N8N SERVICE - ENVÍO DE WEBHOOK")
        print(f"📤 PAYLOAD: {json.dumps(payload, indent=2)}")
        print(f"📍 URL: {settings.N8N_WEBHOOK_URL}")
        print(f"🔑 HEADER NAME: {settings.N8N_HEADER_NAME}")
        print(f"🔑 HEADER VALUE: {settings.N8N_HEADER_PASSWORD}")
        print(f"📋 HEADERS COMPLETOS: {cls.HEADERS_SEGURIDAD_N8N}")
        print("=" * 60)

        max_reintentos = 3
        espera_segundos = 2

        async with httpx.AsyncClient() as client:
            for intento in range(1, max_reintentos + 1):
                try:
                    logger.info(f"🔄 Intento {intento}/{max_reintentos}...")
                    print(f"⏳ Enviando intento {intento}...")
                    
                    response = await client.post(
                        settings.N8N_WEBHOOK_URL,
                        json=payload,
                        headers=cls.HEADERS_SEGURIDAD_N8N,
                        timeout=10.0
                    )
                    
                    print(f"📨 RESPUESTA RECIBIDA - Status: {response.status_code}")
                    print(f"📨 RESPUESTA BODY: {response.text[:500]}")
                    
                    logger.info(f"[LOG n8n] Creación (Intento {intento}/{max_reintentos}) - Código: {response.status_code}")
                    logger.info(f"[LOG n8n] Respuesta: {response.text[:200]}")
                    
                    if response.status_code == 200:
                        print(f"✅ n8n procesó correctamente la reserva {reserva_id}")
                        logger.info(f"✅ n8n procesó correctamente la reserva {reserva_id}")
                        return
                        
                except httpx.TimeoutException:
                    print(f"⏰ Timeout en intento {intento}")
                    logger.error(f"⏰ Timeout en intento {intento}")
                except httpx.ConnectError as e:
                    print(f"🔌 Error de conexión en intento {intento}: {e}")
                    logger.error(f"🔌 Error de conexión en intento {intento}: {e}")
                except Exception as e:
                    print(f"❌ Error en intento {intento}: {str(e)}")
                    logger.error(f"❌ Error en intento {intento}: {str(e)}")
                    import traceback
                    traceback.print_exc()

                if intento < max_reintentos:
                    await asyncio.sleep(espera_segundos * intento)

        print(f"❌ CRÍTICO: Fallaron todos los reintentos para la reserva {reserva_id}")
        logger.error(f"❌ CRÍTICO: Fallaron todos los reintentos para la reserva {reserva_id}")

    @classmethod
    async def notificar_liquidacion_a_n8n(cls, reserva_id: uuid.UUID, id_empresa: str):
        """
        Despierta el flujo de n8n cuando una reserva es liquidada de forma tardía.
        """
        payload = {
            "reserva_id": str(reserva_id),
            "id_empresa": id_empresa,
            "evento": "LIQUIDADO",
            "fuente": "manual_patch_abono"
        }

        print("=" * 60)
        print("📤 N8N LIQUIDACIÓN - ENVÍO DE WEBHOOK")
        print(f"📤 PAYLOAD: {json.dumps(payload, indent=2)}")
        print(f"📍 URL: {settings.N8N_WEBHOOK_UPDATE_URL}")
        print("=" * 60)

        max_reintentos = 3
        espera_segundos = 2

        async with httpx.AsyncClient() as client:
            for intento in range(1, max_reintentos + 1):
                try:
                    response = await client.post(
                        settings.N8N_WEBHOOK_UPDATE_URL,
                        json=payload,
                        headers=cls.HEADERS_SEGURIDAD_N8N,
                        timeout=10.0
                    )
                    
                    print(f"📨 RESPUESTA LIQUIDACIÓN - Status: {response.status_code}")
                    logger.info(f"[LOG n8n] Liquidación (Intento {intento}/{max_reintentos}) - Código: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"✅ Liquidación procesada para {reserva_id}")
                        logger.info(f"✅ Liquidación procesada para {reserva_id}")
                        return
                        
                except Exception as e:
                    print(f"❌ Error en liquidación: {e}")
                    logger.error(f"❌ Error en liquidación: {e}")

                if intento < max_reintentos:
                    await asyncio.sleep(espera_segundos * intento)

        print(f"❌ CRÍTICO: n8n no procesó la liquidación para la reserva {reserva_id}")
        logger.error(f"❌ CRÍTICO: n8n no procesó la liquidación para la reserva {reserva_id}")