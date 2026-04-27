import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

class CloudinaryConfig:
    """
    Configuración de Cloudinary para manejo de archivos multimedia.
    """
    
    @staticmethod
    def init_cloudinary():
        """
        Inicializa la configuración de Cloudinary con las variables de entorno.
        """
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET'),
            secure=True
        )
    
    @staticmethod
    def test_connection():
        """
        Verifica la conexión con Cloudinary.
        """
        try:
            result = cloudinary.api.ping()
            return result.get('status') == 'ok'
        except Exception as e:
            print(f"Error al conectar con Cloudinary: {e}")
            return False