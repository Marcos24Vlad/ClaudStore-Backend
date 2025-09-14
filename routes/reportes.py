from fastapi import APIRouter, Query, HTTPException
from backend.config.db import conn
from backend.models.producto import productos
from backend.models.venta import ventas
from sqlalchemy import func, extract, and_, select
from datetime import datetime

router = APIRouter(prefix="/reportes", tags=["Reportes"])

# 🔹 Reportes por rango de fechas (listo para frontend)
@router.get("/rango")
def reportes_por_rango(
    desde: datetime = Query(..., description="Fecha inicio"),
    hasta: datetime = Query(..., description="Fecha fin"),
    periodo: str = Query("mes", enum=["dia", "semana", "mes", "anio"])
):
    # Definimos agrupador según periodo
    if periodo == "dia":
        agrupador = [
            extract("year", ventas.c.fecha_venta).label("anio"),
            extract("month", ventas.c.fecha_venta).label("mes"),
            extract("day", ventas.c.fecha_venta).label("dia")
        ]
    elif periodo == "semana":
        agrupador = [
            extract("year", ventas.c.fecha_venta).label("anio"),
            extract("week", ventas.c.fecha_venta).label("semana")
        ]
    elif periodo == "mes":
        agrupador = [
            extract("year", ventas.c.fecha_venta).label("anio"),
            extract("month", ventas.c.fecha_venta).label("mes")
        ]
    else:  # anio
        agrupador = [extract("year", ventas.c.fecha_venta).label("anio")]

    # 🔹 Consulta principal filtrando por fechas
    stmt = (
        select(
            *agrupador,
            func.sum(productos.c.costo * ventas.c.cantidad).label("inversion"),
            func.sum(ventas.c.precio_total).label("generado")
        )
        .select_from(ventas.join(productos, ventas.c.id_producto == productos.c.id_producto))
        .where(and_(ventas.c.fecha_venta >= desde, ventas.c.fecha_venta <= hasta))
        .group_by(*agrupador)
        .order_by(*agrupador)
    )
    result = conn.execute(stmt).fetchall()

    # Métricas generales
    inversion_total = float(sum(row.inversion or 0 for row in result))
    generado_total = float(sum(row.generado or 0 for row in result))
    ganancia_neta = generado_total - inversion_total

    # 🔹 Top 5 productos en ese rango
    stmt_top5 = (
        select(
            productos.c.nombre,
            func.sum(ventas.c.cantidad).label("vendidos")
        )
        .select_from(ventas.join(productos, ventas.c.id_producto == productos.c.id_producto))
        .where(and_(ventas.c.fecha_venta >= desde, ventas.c.fecha_venta <= hasta))
        .group_by(productos.c.nombre)
        .order_by(func.sum(ventas.c.cantidad).desc())
        .limit(5)
    )
    top5 = conn.execute(stmt_top5).fetchall()

    # Transformamos ventas por periodo a lista de dicts
    ventas_por_periodo = [
        {
            "periodo": dict(row._mapping),
            "inversion": float(row.inversion or 0),
            "generado": float(row.generado or 0),
            "ganancia_neta": float(row.generado or 0) - float(row.inversion or 0)
        }
        for row in result
    ]

    return {
        "inversion_total": inversion_total,
        "generado_total": generado_total,
        "ganancia_neta": ganancia_neta,
        "top5": [{"nombre": row.nombre, "vendidos": int(row.vendidos or 0)} for row in top5],
        "ventas_por_periodo": ventas_por_periodo
    }

# 🔹 Reiniciar reportes por rango de fechas
@router.delete("/reiniciar")
def reiniciar_reportes(
    desde: datetime = Query(..., description="Fecha inicio"),
    hasta: datetime = Query(..., description="Fecha fin")
):
    # Validación de fechas
    if desde > hasta:
        raise HTTPException(status_code=400, detail="La fecha 'desde' no puede ser mayor que 'hasta'.")

    # Eliminamos las ventas en el rango especificado
    delete_stmt = ventas.delete().where(and_(ventas.c.fecha_venta >= desde, ventas.c.fecha_venta <= hasta))
    result = conn.execute(delete_stmt)
    conn.commit()

    return {
        "mensaje": f"Se eliminaron {result.rowcount} ventas entre {desde} y {hasta}."
    }
