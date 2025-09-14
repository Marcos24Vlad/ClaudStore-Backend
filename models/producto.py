from sqlalchemy import Table, Column, Integer, String, DECIMAL, Boolean, DateTime
from backend.config.db import meta, engine
from datetime import datetime

productos = Table(
    "productos", meta,
    Column("id_producto", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(255), nullable=False),
    Column("costo", DECIMAL(10, 2), nullable=False),
    Column("precio_venta", DECIMAL(10, 2), nullable=False),
    Column("stock", Integer, nullable=False),
    Column("imagen_url", String(255), nullable=True),
    Column("inversion_acumulada", DECIMAL(10, 2), default=0),
    Column("activo", Boolean, default=True),
    Column("fecha_registro", DateTime, default=datetime.now)
)

meta.create_all(engine)
