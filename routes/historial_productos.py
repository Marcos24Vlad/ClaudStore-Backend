from fastapi import APIRouter, HTTPException
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from backend.config.db import conn
from backend.models.producto import productos
from backend.models.historial_productos import historial_productos
from backend.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from datetime import datetime

router = APIRouter(prefix="/productos", tags=["Productos"])

# 🔹 Función auxiliar: registrar en historial
def _registrar_historial_producto(id_producto, nombre, costo=None, precio_venta=None, stock=None,
                                  imagen_url=None, activo=True, inversion_acumulada=None, accion="actualizacion"):
    registro = {
        "id_producto": id_producto,
        "nombre": nombre,
        "costo": costo,
        "precio_venta": precio_venta,
        "stock": stock,
        "imagen_url": imagen_url,
        "activo": activo,
        "inversion_acumulada": inversion_acumulada,
        "accion": accion,
        "fecha_registro": datetime.now()
    }
    conn.execute(historial_productos.insert().values(registro))
    conn.commit()


# 🔹 Crear producto
@router.post("/", response_model=ProductoResponse)
def create_producto(producto: ProductoCreate):
    try:
        nuevo_producto = {
            "nombre": producto.nombre,
            "costo": producto.costo,
            "precio_venta": producto.precio_venta,
            "stock": producto.stock,
            "imagen_url": producto.imagen_url,
            "fecha_registro": datetime.now()
        }

        result = conn.execute(insert(productos).values(**nuevo_producto))
        conn.commit()
        producto_id = result.inserted_primary_key[0]

        # Registrar historial
        _registrar_historial_producto(
            id_producto=producto_id,
            nombre=producto.nombre,
            costo=producto.costo,
            precio_venta=producto.precio_venta,
            stock=producto.stock,
            imagen_url=producto.imagen_url,
            accion="creacion"
        )

        return {"id_producto": producto_id, **nuevo_producto}

    except SQLAlchemyError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Listar productos
@router.get("/", response_model=list[ProductoResponse])
def listar_productos():
    result = conn.execute(select(productos)).fetchall()
    return [dict(row._mapping) for row in result]


# 🔹 Obtener producto por ID
@router.get("/{id_producto}", response_model=ProductoResponse)
def obtener_producto(id_producto: int):
    producto = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return dict(producto._mapping)


# 🔹 Actualizar producto (soporte parcial)
@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(id_producto: int, producto: ProductoUpdate):
    existente = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    if not existente:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Tomar solo campos enviados
    valores_actualizados = producto.dict(exclude_unset=True)
    valores_actualizados["fecha_registro"] = datetime.now()

    # Actualizar producto
    conn.execute(
        update(productos)
        .where(productos.c.id_producto == id_producto)
        .values(**valores_actualizados)
    )
    conn.commit()

    # Registrar historial
    _registrar_historial_producto(
        id_producto=id_producto,
        nombre=valores_actualizados.get("nombre", existente._mapping["nombre"]),
        costo=valores_actualizados.get("costo", existente._mapping["costo"]),
        precio_venta=valores_actualizados.get("precio_venta", existente._mapping["precio_venta"]),
        stock=valores_actualizados.get("stock", existente._mapping["stock"]),
        imagen_url=valores_actualizados.get("imagen_url", existente._mapping["imagen_url"]),
        activo=existente._mapping.get("activo", True),
        inversion_acumulada=existente._mapping.get("inversion_acumulada", 0),
        accion="actualizacion"
    )

    actualizado = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    return dict(actualizado._mapping)


# 🔹 Eliminar producto
@router.delete("/{id_producto}")
def eliminar_producto(id_producto: int):
    producto = conn.execute(
        select(productos).where(productos.c.id_producto == id_producto)
    ).fetchone()

    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    conn.execute(delete(productos).where(productos.c.id_producto == id_producto))
    conn.commit()

    # Registrar historial
    _registrar_historial_producto(
        id_producto=id_producto,
        nombre=producto._mapping["nombre"],
        costo=producto._mapping["costo"],
        precio_venta=producto._mapping["precio_venta"],
        stock=producto._mapping["stock"],
        imagen_url=producto._mapping["imagen_url"],
        activo=producto._mapping.get("activo", True),
        inversion_acumulada=producto._mapping.get("inversion_acumulada", 0),
        accion="eliminacion"
    )

    return {"mensaje": f"Producto {id_producto} eliminado correctamente"}
