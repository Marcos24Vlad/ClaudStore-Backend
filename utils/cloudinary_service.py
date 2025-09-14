import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image(file) -> str:
    """
    Sube una imagen a Cloudinary y devuelve la URL segura.
    """
    try:
        result = cloudinary.uploader.upload(file)
        return result.get("secure_url")
    except Exception as e:
        raise RuntimeError(f"Error al subir imagen a Cloudinary: {e}")
