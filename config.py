import os
import pymysql
from urllib.parse import urlparse

def get_connection():
    # 🔹 Usar variables de entorno para producción
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # 🌐 Para producción - MySQL remoto
        url = urlparse(database_url)
        return pymysql.connect(
            host=url.hostname,
            port=url.port or 3306,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # Quitar el '/' inicial
            charset='utf8mb4'
        )
    else:
        # 🏠 Para desarrollo local - fallback
        return pymysql.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'api_user'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'inventario_db'),
            charset='utf8mb4'
        )