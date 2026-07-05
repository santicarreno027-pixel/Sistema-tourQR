from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer
from app.core.database import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String(100), primary_key=True, index=True)
    status_code = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)
