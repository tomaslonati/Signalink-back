import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import base64
import tempfile
import os


def upload_audio_to_cloudinary(audio_b64: str, user_id: int, group_id: int) -> tuple:
    """
    Sube el audio a Cloudinary y retorna la URL y duración.
    
    """
    try:
        # Decodificar el audio de base64
        audio_data = base64.b64decode(audio_b64)
        
        # Crear archivo temporal para subir
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        # Subir a Cloudinary
        result = cloudinary.uploader.upload(
            temp_path,
            resource_type="video",  # Cloudinary trata audios como videos
            folder=f"signalink/audios/group_{group_id}",
            public_id=f"user_{user_id}_{int(cloudinary.utils.now())}",
            format="mp3"  # Convertir a mp3 automáticamente
        )
        
        # Eliminar archivo temporal
        os.unlink(temp_path)
        
        # Retornar URL segura y duración
        return result['secure_url'], result.get('duration', 0)
        
    except Exception as e:
        print(f"Error al subir audio a Cloudinary: {e}")
        raise Exception(f"Error al subir audio: {str(e)}")


def delete_audio_from_cloudinary(audio_url: str) -> bool:
    """
    Elimina un audio de Cloudinary.
    
    Args:
        audio_url: URL del audio a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        # Extraer public_id de la URL
        # Ejemplo: https://res.cloudinary.com/xxx/video/upload/v123/signalink/audios/group_1/user_2_123.mp3
        parts = audio_url.split('/')
        # Buscar el índice de 'upload'
        upload_idx = parts.index('upload')
        # El public_id está después de la versión (v123)
        public_id_parts = parts[upload_idx + 2:]  # Salta 'upload' y 'v123'
        public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]  # Remover extensión
        
        # Eliminar de Cloudinary
        cloudinary.uploader.destroy(public_id, resource_type="video")
        print(f"✓ Audio eliminado de Cloudinary: {public_id}")
        return True
    except Exception as e:
        print(f"Error al eliminar audio de Cloudinary: {e}")
        return False
