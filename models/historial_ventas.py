from sqlalchemy import Table, Column, Integer, Float, DateTime, ForeignKey
from backend.config.db import meta
from datetime import datetime

historial_ventas = Table(
    "historial_ventas", meta,
    Column("id_historial", Integer, primary_key=True, autoincrement=True),
    Column("id_venta", Integer, nullable=False),
    Column("id_producto", Integer, ForeignKey("productos.id_producto"), nullable=False),
    Column("cantidad", Integer, nullable=False),
    Column("precio_unitario", Float, nullable=False),
    Column("precio_total", Float, nullable=False),
    Column("fecha_venta", DateTime, default=datetime.now)
)

from backend.config.db import engine
meta.create_all(engine)
