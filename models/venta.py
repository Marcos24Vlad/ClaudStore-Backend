from sqlalchemy import Table, Column, Integer, Float, DateTime, ForeignKey
from backend.config.db import meta, engine

ventas = Table(
    "ventas", meta,
    Column("id_venta", Integer, primary_key=True, autoincrement=True),
    Column("id_producto", Integer, ForeignKey("productos.id_producto")),
    Column("cantidad", Integer),
    Column("precio_total", Float),
    Column("precio_unitario", Float),
    Column("fecha_venta", DateTime),
    # Column("fecha", DateTime)  ← ELIMINAR ESTA LÍNEA (campo duplicado)
)

meta.create_all(engine)