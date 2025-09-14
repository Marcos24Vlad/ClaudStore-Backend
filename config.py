import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="api_user",
        password="",  # ahora vacío
        database="inventario_db"
    )