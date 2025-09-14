from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductoBase(BaseModel):
    nombre: str
    costo: float
    precio_venta: float
    stock: int
    imagen_url: Optional[str] = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    costo: Optional[float] = None
    precio_venta: Optional[float] = None
    stock: Optional[int] = None
    imagen_url: Optional[str] = None


class ProductoResponse(BaseModel):
    id_producto: int
    nombre: str
    costo: float
    precio_venta: float
    stock: int
    imagen_url: Optional[str] = None
    inversion_acumulada: Optional[float] = None  # 🔥 Agregado
    activo: Optional[bool] = None                # 🔥 Agregado
    fecha_registro: Optional[datetime] = None

    class Config:
        from_attributes = True