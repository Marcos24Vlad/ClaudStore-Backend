from sqlalchemy import Table, Column, Integer, String, DECIMAL, DateTime, Boolean
from backend.config.db import meta, engine
from datetime import datetime

# 🔹 Tabla historial_productos
historial_productos = Table(
    "historial_productos", meta,
    Column("id_historial", Integer, primary_key=True, autoincrement=True),
    Column("id_producto", Integer, nullable=False),
    Column("nombre", String(255), nullable=False),
    Column("costo", DECIMAL(10, 2), nullable=True),
    Column("precio_venta", DECIMAL(10, 2), nullable=True),
    Column("stock", Integer, nullable=True),
    Column("imagen_url", String(255), nullable=True),
    Column("activo", Boolean, default=True),
    Column("inversion_acumulada", DECIMAL(12, 2), nullable=True),
    Column("accion", String(50), nullable=False),  # 🔹 crear / actualizar / eliminar / vender
    Column("fecha_registro", DateTime, default=datetime.now)
)

# 🔹 Crear tabla si no existe
meta.create_all(engine)
