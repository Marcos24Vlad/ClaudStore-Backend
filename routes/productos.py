from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from sqlalchemy import insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from backend.config.db import conn
from backend.models.producto import productos
from backend.models.historial_productos import historial_productos
from backend.schemas.producto import ProductoResponse
from datetime import datetime
from backend.utils.cloudinary_service import upload_image  # 👈 NUEVO

router = APIRouter(prefix="/productos", tags=["Productos"])

# 📌 Función auxiliar para registrar historial
def _registrar_historial_producto(
    id_producto,
    tipo,
    cantidad,
    costo,
    precio,
    stock_anterior,
    stock_nuevo
):
    registro = {
        "id_producto": id_producto,
        "accion": tipo,
        "costo": costo,
        "precio_venta": precio,
        "stock": stock_nuevo,
        "fecha_registro": datetime.now()
    }
    conn.execute(historial_productos.insert().values(registro))
    conn.commit()

# 🔹 Crear producto
@router.post("", response_model=ProductoResponse)
def create_producto(
    nombre: str = Form(...),
    costo: float = Form(...),
    precio_venta: float = Form(...),
    stock: int = Form(...),
    imagen: UploadFile = File(None)
):
    try:
        imagen_url = None
        if imagen:
            # Subir archivo directamente a Cloudinary
            imagen_url = upload_image(imagen.file)

        nuevo_producto = {
            "nombre": nombre,
            "costo": costo,
            "precio_venta": precio_venta,
            "stock": stock,
            "imagen_url": imagen_url,
            "fecha_registro": datetime.now()
        }

        result = conn.execute(insert(productos).values(**nuevo_producto))
        conn.commit()
        producto_id = result.inserted_primary_key[0]

        _registrar_historial_producto(
            id_producto=producto_id,
            tipo="creacion",
            cantidad=stock,
            costo=costo,
            precio=precio_venta,
            stock_anterior=0,
            stock_nuevo=stock
        )

        return {"id_producto": producto_id, **nuevo_producto}

    except SQLAlchemyError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🔹 Listar productos
@router.get("", response_model=list[ProductoResponse])
def listar_productos():
    result = conn.execute(select(productos)).fetchall()
    return [dict(row._mapping) for row in result]

# 🔹 Actualizar producto
@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    nombre: str = Form(None),
    costo: float = Form(None),
    precio_venta: float = Form(None),
    stock: int = Form(None),
    imagen: UploadFile = File(None)
):
    existente = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    if not existente:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    stock_anterior = existente._mapping["stock"]

    valores_actualizados = {}
    if nombre is not None:
        valores_actualizados["nombre"] = nombre
    if costo is not None:
        valores_actualizados["costo"] = costo
    if precio_venta is not None:
        valores_actualizados["precio_venta"] = precio_venta
    if stock is not None:
        valores_actualizados["stock"] = stock
    if imagen is not None:
        # Subir nueva imagen a Cloudinary
        valores_actualizados["imagen_url"] = upload_image(imagen.file)

    if not valores_actualizados:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    valores_actualizados["fecha_registro"] = datetime.now()

    conn.execute(
        update(productos)
        .where(productos.c.id_producto == id_producto)
        .values(**valores_actualizados)
    )
    conn.commit()

    _registrar_historial_producto(
        id_producto=id_producto,
        tipo="actualizacion",
        cantidad=(valores_actualizados.get("stock", stock_anterior) - stock_anterior)
        if "stock" in valores_actualizados else 0,
        costo=valores_actualizados.get("costo", existente._mapping["costo"]),
        precio=valores_actualizados.get("precio_venta", existente._mapping["precio_venta"]),
        stock_anterior=stock_anterior,
        stock_nuevo=valores_actualizados.get("stock", stock_anterior)
    )

    actualizado = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    return dict(actualizado._mapping)

# 🔹 Desactivar producto
@router.delete("/{id_producto}")
def eliminar_producto(id_producto: int):
    producto = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    conn.execute(
        update(productos)
        .where(productos.c.id_producto == id_producto)
        .values(activo=False, fecha_registro=datetime.now())
    )
    conn.commit()

    _registrar_historial_producto(
        id_producto=id_producto,
        tipo="desactivacion",
        cantidad=-producto._mapping["stock"],
        costo=producto._mapping["costo"],
        precio=producto._mapping["precio_venta"],
        stock_anterior=producto._mapping["stock"],
        stock_nuevo=0
    )

    return {"mensaje": f"Producto {id_producto} desactivado correctamente"}
