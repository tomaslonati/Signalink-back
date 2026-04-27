from datetime import datetime, date
from decimal import Decimal
from bson import ObjectId

def serialize_datetime(obj):
    """
    Convierte objetos datetime, date, Decimal y ObjectId a formatos serializables en JSON
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

def serialize_message(message):
    """
    Serializa un objeto Message de MongoDB
    """
    if not message:
        return None
        
    return {
        "id": str(message.id),
        "groupId": message.groupId,
        "senderId": message.senderId,
        "senderUsername": message.senderUsername,
        "text": message.text,
        "type": message.type,
        "createdAt": message.createdAt.isoformat(),
        "editedAt": message.editedAt.isoformat() if message.editedAt else None,
        "audio_url": message.audio_url,
        "duration": message.duration
    }

def serialize_dict(data):
    """
    Serializa un diccionario convirtiendo campos datetime, ObjectId, etc a strings
    """
    if hasattr(data, 'dict'):  # Si es un modelo Beanie/Pydantic
        data = data.dict()
    elif not isinstance(data, dict):
        return serialize_datetime(data)
    
    return {key: serialize_datetime(value) for key, value in data.items()}

def serialize_list(data):
    """
    Serializa una lista de objetos
    """
    if not isinstance(data, list):
        return serialize_dict(data)
    
    return [serialize_message(item) if hasattr(item, 'id') else serialize_dict(item) for item in data]
