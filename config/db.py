from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import URL

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username="root",
    password="",
    host="localhost",
    database="inventario_db"
)

engine = create_engine(DATABASE_URL)
meta = MetaData()
conn = engine.connect()
