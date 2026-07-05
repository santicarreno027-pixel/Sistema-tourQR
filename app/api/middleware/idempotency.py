from fastapi import Request, Response, HTTPException
import json
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.future import select
from app.core.database import SessionLocal
from app.models.idempotency import IdempotencyKey

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Solo aplicar idempotencia a métodos que alteran estado
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # Buscar si la llave ya existe
        async with SessionLocal() as db:
            stmt = select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
            result = await db.execute(stmt)
            existing_key = result.scalar_one_or_none()

            if existing_key:
                # Si existe, devolvemos la respuesta guardada
                headers = {"Idempotency-Replayed": "true"}
                return Response(
                    content=json.dumps(existing_key.response_body) if existing_key.response_body else "",
                    status_code=existing_key.status_code,
                    media_type="application/json",
                    headers=headers
                )

        # Si no existe, procesar la petición normalmente
        response = await call_next(request)

        # Leer el cuerpo de la respuesta para guardarlo
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
            
        # Reconstruir la respuesta para que pueda ser leida por el cliente
        # FastAPI's background tasks might interfere if we just read it, but this is a simple approach
        try:
            body_json = json.loads(response_body.decode()) if response_body else None
        except:
            body_json = None

        # Guardar en base de datos
        async with SessionLocal() as db:
            new_key = IdempotencyKey(
                key=idempotency_key,
                status_code=response.status_code,
                response_body=body_json
            )
            db.add(new_key)
            await db.commit()

        # Retornar la respuesta original
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
