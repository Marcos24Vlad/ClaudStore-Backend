from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import productos, ventas, reportes
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ En producción, restringir al dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta uploads
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# Routers con prefijo
app.include_router(productos.router, prefix="/api/productos", tags=["Productos"])
app.include_router(ventas.router, prefix="/api/ventas", tags=["Ventas"])
app.include_router(reportes.router, prefix="/api/reportes", tags=["Reportes"])

@app.get("/")
def root():
    return {"mensaje": "API de Inventario funcionando"}

# Ejecutar local o en Render
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import productos, ventas, reportes
from backend.routes import productos as productos_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
load_dotenv()  # Esto carga las variables del .env


app = FastAPI()

# Configuración de CORS para poder acceder desde cualquier dispositivo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # en producción, restringe a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carpeta para imágenes (ahora "uploads")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Montar carpeta para servir imágenes de manera pública
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# Rutas de la API
app.include_router(productos_router.router)
app.include_router(ventas.router)
app.include_router(reportes.router)

@app.get("/")
def root():
    return {"mensaje": "API de Inventario funcionando"}
