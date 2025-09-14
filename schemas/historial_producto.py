from pydantic import BaseModel
from datetime import datetime

class HistorialProductoBase(BaseModel):
    id_producto: int
    cambio: str

class HistorialProductoCreate(HistorialProductoBase):
    pass

class HistorialProducto(HistorialProductoBase):
    id: int
    fecha: datetime

    class Config:
        from_attributes = True
