from fastapi import APIRouter, HTTPException
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from backend.config.db import conn
from backend.models.venta import ventas
from backend.models.producto import productos
from backend.models.historial_ventas import historial_ventas
from backend.schemas.venta import VentaCreate, VentaResponse
from datetime import datetime
import logging
import traceback

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ventas", tags=["Ventas"])


# 🔹 Función auxiliar: registrar en historial (con manejo de errores)
def _registrar_historial_venta(venta_registro):
    try:
        logger.info(f"🔍 Registrando historial para venta: {venta_registro}")
        
        # Verificar que venta_registro tenga los atributos necesarios
        required_attrs = ['id_venta', 'id_producto', 'cantidad', 'precio_unitario', 'precio_total', 'fecha_venta']
        for attr in required_attrs:
            if not hasattr(venta_registro, attr):
                logger.error(f"❌ Atributo faltante en venta_registro: {attr}")
                return False
        
        registro = {
            "id_venta": venta_registro.id_venta,
            "id_producto": venta_registro.id_producto,
            "cantidad": venta_registro.cantidad,
            "precio_unitario": venta_registro.precio_unitario,
            "precio_total": venta_registro.precio_total,
            "fecha_venta": venta_registro.fecha_venta
        }
        
        logger.info(f"🔍 Datos del historial: {registro}")
        conn.execute(historial_ventas.insert().values(registro))
        conn.commit()
        logger.info("✅ Historial registrado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error registrando historial: {str(e)}")
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        return False


# 🔹 Crear venta con manejo de errores exhaustivo
@router.post("/", response_model=VentaResponse)
def create_venta(venta: VentaCreate):
    logger.info(f"🚀 INICIO - Creando venta: {venta.dict()}")
    
    try:
        # PASO 1: Validar entrada
        logger.info(f"🔍 PASO 1 - Validando datos de entrada")
        if not venta.id_producto or venta.id_producto <= 0:
            raise HTTPException(status_code=400, detail="ID de producto inválido")
        if not venta.cantidad or venta.cantidad <= 0:
            raise HTTPException(status_code=400, detail="Cantidad inválida")
        
        # PASO 2: Buscar producto
        logger.info(f"🔍 PASO 2 - Buscando producto ID: {venta.id_producto}")
        producto = conn.execute(
            select(productos).where(productos.c.id_producto == venta.id_producto)
        ).fetchone()

        if not producto:
            logger.error(f"❌ Producto {venta.id_producto} no encontrado")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        producto_data = dict(producto._mapping)
        logger.info(f"✅ Producto encontrado: {producto_data}")

        # PASO 3: Verificar stock
        logger.info(f"🔍 PASO 3 - Verificando stock")
        stock_actual = producto_data["stock"]
        logger.info(f"Stock actual: {stock_actual}, Cantidad solicitada: {venta.cantidad}")
        
        if stock_actual < venta.cantidad:
            logger.error(f"❌ Stock insuficiente")
            raise HTTPException(status_code=400, detail=f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {venta.cantidad}")

        # PASO 4: Calcular precios
        logger.info(f"🔍 PASO 4 - Calculando precios")
        precio_unitario = float(producto_data["precio_venta"])
        precio_total = precio_unitario * venta.cantidad
        logger.info(f"Precio unitario: {precio_unitario}, Precio total: {precio_total}")

        # PASO 5: Actualizar stock
        logger.info(f"🔍 PASO 5 - Actualizando stock")
        nuevo_stock = stock_actual - venta.cantidad
        logger.info(f"Nuevo stock será: {nuevo_stock}")
        
        conn.execute(
            update(productos)
            .where(productos.c.id_producto == venta.id_producto)
            .values(stock=nuevo_stock)
        )
        logger.info("✅ Stock actualizado")

        # PASO 6: Crear registro de venta
        logger.info(f"🔍 PASO 6 - Insertando venta en BD")
        fecha_actual = datetime.now()
        nueva_venta = {
            "id_producto": venta.id_producto,
            "cantidad": venta.cantidad,
            "precio_unitario": precio_unitario,
            "precio_total": precio_total,
            "fecha_venta": fecha_actual
        }
        
        logger.info(f"Datos a insertar: {nueva_venta}")
        result = conn.execute(insert(ventas).values(**nueva_venta))
        conn.commit()
        
        venta_id = result.inserted_primary_key[0]
        logger.info(f"✅ Venta insertada con ID: {venta_id}")

        # PASO 7: Obtener venta creada
        logger.info(f"🔍 PASO 7 - Obteniendo venta creada")
        venta_creada = conn.execute(
            select(ventas).where(ventas.c.id_venta == venta_id)
        ).fetchone()
        
        if not venta_creada:
            logger.error("❌ No se pudo obtener la venta recién creada")
            raise HTTPException(status_code=500, detail="Error al obtener venta creada")
        
        venta_creada_data = dict(venta_creada._mapping)
        logger.info(f"✅ Venta creada obtenida: {venta_creada_data}")

        # PASO 8: Registrar en historial (opcional - si falla no interrumpe)
        logger.info(f"🔍 PASO 8 - Registrando historial")
        try:
            _registrar_historial_venta(venta_creada)
        except Exception as hist_error:
            logger.warning(f"⚠️ Error en historial (no crítico): {str(hist_error)}")

        # PASO 9: Preparar respuesta
        logger.info(f"🔍 PASO 9 - Preparando respuesta")
        respuesta = {
            "id_venta": venta_id,
            "id_producto": venta.id_producto,
            "cantidad": venta.cantidad,
            "precio_unitario": precio_unitario,
            "precio_total": precio_total,
            "fecha_venta": fecha_actual
        }
        
        logger.info(f"✅ Respuesta preparada: {respuesta}")
        logger.info(f"🎉 ÉXITO - Venta creada exitosamente")
        
        return respuesta

    except HTTPException as he:
        logger.error(f"❌ HTTPException: {he.detail}")
        conn.rollback()
        raise he
        
    except SQLAlchemyError as se:
        logger.error(f"❌ Error de base de datos: {str(se)}")
        logger.error(f"❌ Traceback SQLAlchemy: {traceback.format_exc()}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(se)}")
        
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# 🔹 Listar todas las ventas
@router.get("/", response_model=list[VentaResponse])
def listar_ventas():
    try:
        logger.info("🔍 Obteniendo todas las ventas")
        result = conn.execute(select(ventas)).fetchall()
        ventas_list = [dict(row._mapping) for row in result]
        logger.info(f"✅ {len(ventas_list)} ventas obtenidas")
        return ventas_list
    except Exception as e:
        logger.error(f"❌ Error listando ventas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Obtener venta por ID
@router.get("/{id_venta}", response_model=VentaResponse)
def obtener_venta(id_venta: int):
    try:
        logger.info(f"🔍 Obteniendo venta ID: {id_venta}")
        venta = conn.execute(
            select(ventas).where(ventas.c.id_venta == id_venta)
        ).fetchone()
        
        if not venta:
            logger.error(f"❌ Venta {id_venta} no encontrada")
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        
        venta_data = dict(venta._mapping)
        logger.info(f"✅ Venta obtenida: {venta_data}")
        return venta_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo venta: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Consultar historial de ventas
@router.get("/historial/", tags=["Historial"])
def historial():
    try:
        logger.info("🔍 Obteniendo historial de ventas")
        result = conn.execute(select(historial_ventas)).fetchall()
        historial_list = [dict(row._mapping) for row in result]
        logger.info(f"✅ {len(historial_list)} registros de historial obtenidos")
        return historial_list
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 Eliminar una venta
@router.delete("/{id_venta}")
def eliminar_venta(id_venta: int):
    try:
        logger.info(f"🔍 Eliminando venta ID: {id_venta}")
        
        venta = conn.execute(
            select(ventas).where(ventas.c.id_venta == id_venta)
        ).fetchone()

        if not venta:
            logger.error(f"❌ Venta {id_venta} no encontrada")
            raise HTTPException(status_code=404, detail="Venta no encontrada")

        # Restaurar stock
        logger.info("🔍 Restaurando stock")
        producto = conn.execute(
            select(productos).where(productos.c.id_producto == venta.id_producto)
        ).fetchone()

        if producto:
            stock_actual = producto._mapping["stock"]
            nuevo_stock = stock_actual + venta.cantidad
            conn.execute(
                update(productos)
                .where(productos.c.id_producto == venta.id_producto)
                .values(stock=nuevo_stock)
            )
            logger.info(f"✅ Stock restaurado: {stock_actual} + {venta.cantidad} = {nuevo_stock}")

        # Eliminar la venta
        conn.execute(delete(ventas).where(ventas.c.id_venta == id_venta))
        conn.commit()
        
        logger.info(f"✅ Venta {id_venta} eliminada exitosamente")
        return {"mensaje": f"Venta {id_venta} eliminada correctamente y stock restaurado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando venta: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))