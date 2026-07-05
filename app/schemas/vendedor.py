from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class VendedorCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., min_length=2)
    rol: Literal["ADMIN", "VENDEDOR"] = "VENDEDOR"

class VendedorUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[Literal["ADMIN", "VENDEDOR"]] = None
    password: Optional[str] = Field(None, min_length=6)
    activo: Optional[bool] = None  # False = banear (desactivar), True = reactivar

class VendedorResponse(BaseModel):
    id: str
    email: EmailStr
    nombre: Optional[str] = None
    rol: Optional[str] = None
    id_empresa: Optional[str] = None
    activo: bool
    creado_en: Optional[datetime] = None