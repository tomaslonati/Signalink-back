from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document
from pydantic import Field


class Message(Document):
    """
    Modelo de documento MongoDB para mensajes.
    Todos los mensajes pertenecen a un grupo.
    """
    group_id: int
    sender: int
    type: Literal["text", "audio"]
    text: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None  # Duración del audio en segundos
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "messages"  # Nombre de la colección en MongoDB
        indexes = [
            "group_id",
            "sender",
            [("group_id", 1), ("created_at", -1)],  # Índice compuesto para consultas eficientes
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "group_id": 1,
                "sender": 123,
                "type": "text",
                "text": "Hola, este es un mensaje de prueba",
                "created_at": "2025-10-24T10:30:00"
            }
        }


class MessageCreate(Document):
    """
    Schema para crear un nuevo mensaje.
    No incluye el id ni created_at (se generan automáticamente).
    """
    group_id: int
    sender: int
    type: Literal["text", "audio"]
    text: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "group_id": 1,
                "sender": 123,
                "type": "text",
                "text": "Hola, este es un mensaje"
            }
        }


class MessageResponse(Document):
    """
    Schema para la respuesta de un mensaje.
    Incluye el ID de MongoDB convertido a string.
    """
    id: str = Field(alias="_id")
    group_id: int
    sender: int
    type: Literal["text", "audio"]
    text: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class GroupConversationResponse(Document):
    """
    Schema para obtener la conversación completa de un grupo.
    """
    group_id: int
    group_name: Optional[str] = None
    messages: List[Message] = []

    class Config:
        json_schema_extra = {
            "example": {
                "group_id": 1,
                "group_name": "Grupo de Trabajo",
                "messages": []
            }
        }


