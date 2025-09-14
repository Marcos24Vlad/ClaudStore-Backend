from pydantic import BaseModel
from datetime import datetime

class VentaCreate(BaseModel):
    id_producto: int
    cantidad: int

class VentaResponse(BaseModel):
    id_venta: int
    id_producto: int
    cantidad: int
    precio_total: float
    precio_unitario: float
    fecha_venta: datetime
    # fecha: datetime  ← ELIMINAR ESTA LÍNEA (campo duplicado)

    class Config:
        from_attributes = True