from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field
from src.config.database import DatabaseConfig
import asyncio

# Inicializar la conexión con MongoDB
async def init_mongodb():
    try:
        # Obtener la base de datos directamente del config
        db = DatabaseConfig.get_mongo_database()
        if db is None:
            raise ValueError("No se pudo obtener la conexión a MongoDB")
            
        # Inicializar Beanie con la base de datos
        await init_beanie(database=db, document_models=[Message])
        print("MongoDB initialized successfully")
    except Exception as e:
        print(f"Error initializing MongoDB: {e}")
        raise e

class Message(Document):
    groupId: int
    senderId: int
    senderUsername: str
    text: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    editedAt: Optional[datetime] = None
    type: Literal["text", "audio"] = "text"
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    deleted: bool = False

    class Settings:
        name = "group_messages"
        indexes = [
            # Un solo índice compuesto que cubre las consultas más comunes
            [
                ("groupId", 1),
                ("createdAt", -1)
            ]
        ]

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# La inicialización de MongoDB se maneja en app.py