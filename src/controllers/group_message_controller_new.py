from datetime import datetime
from typing import Optional, List, Dict
from bson import ObjectId
from src.models.message_model import Message
from src.services.database_service import execute_procedure
from src.utils.serializers import serialize_dict, serialize_list, serialize_message
from src.utils.async_manager import AsyncManager
import logging

logger = logging.getLogger(__name__)


class MessageController:
    def __init__(self):
        self.async_manager = AsyncManager()

    def _ensure_mongodb(self):
        """Ensures MongoDB is initialized"""
        from src.models.message_model import init_mongodb
        return self.async_manager.run_async(init_mongodb)

    def validate_group_membership(self, group_id: int, user_id: int) -> bool:
        """Valida que el grupo exista y que el usuario sea miembro activo o el owner"""
        try:
            from src.config.database import DatabaseConfig
            connection = DatabaseConfig.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                query = """
                    SELECT g.id as group_id, g.name as group_name, g.owner_id,
                           ugm.user_id as member_user_id,
                           IF(ugm.user_id IS NOT NULL OR g.owner_id = %s, 1, 0) as has_access
                    FROM user_group g 
                    LEFT JOIN user_group_member ugm ON g.id = ugm.group_id AND ugm.user_id = %s
                    WHERE g.id = %s
                """
                logger.info(
                    f"Validating access for user {user_id} in group {group_id}")
                cursor.execute(query, (user_id, user_id, group_id))
                row = cursor.fetchone()

                if row is None:
                    logger.warning(f"Group {group_id} does not exist")
                    return False

                has_access = row["has_access"] == 1
                is_owner = row["owner_id"] == user_id
                is_member = row["member_user_id"] is not None
                logger.info(
                    f"Access validation - Owner: {is_owner}, Member: {is_member}, Has access: {has_access}")
                return has_access

        except Exception as e:
            logger.error(f"Error validating membership: {e}")
            return False
        finally:
            if connection:
                connection.close()

    def list_messages(self, group_id: int, user_id: int, before: Optional[datetime] = None,
                            after: Optional[datetime] = None, limit: int = 50) -> tuple[Optional[List[Dict]], Optional[str]]:
        """Lista los mensajes de un grupo con filtros opcionales. Retorna (mensajes, error)"""
        try:
            # Validar membresía primero (operación síncrona)
            if not self.validate_group_membership(group_id, user_id):
                return None, "access_denied"

            # Definir función async para MongoDB
            async def _list_messages():
                # Asegurar que MongoDB esté inicializado
                from src.models.message_model import init_mongodb
                await init_mongodb()
                
                # Validar límite
                effective_limit = min(limit, 100)

                # Construir query
                query = {"groupId": group_id, "deleted": False}
                if before:
                    query["createdAt"] = {"$lt": before}
                if after:
                    query["createdAt"] = {"$gt": after} if "createdAt" not in query else {
                        **query["createdAt"],
                        "$gt": after
                    }

                # Ordenar por fecha descendente (más nuevos primero)
                messages = await Message.find(query).sort([("createdAt", -1)]).limit(effective_limit).to_list()
                return [serialize_message(msg) for msg in messages]
            
            # Ejecutar la función async
            result = self.async_manager.run_async(_list_messages)
            return result, None
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return None, f"mongodb_error: {str(e)}"

    def create_message(self, group_id: int, user_id: int, text: str) -> Optional[Dict]:
        """Crea un nuevo mensaje en el grupo"""
        try:
            # Validar membresía primero (operación síncrona)
            if not self.validate_group_membership(group_id, user_id):
                logger.error(f"User {user_id} does not have access to group {group_id}")
                return None

            # Obtener el username del usuario (operación síncrona)
            from src.config.database import DatabaseConfig
            connection = DatabaseConfig.get_connection()
            try:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("""
                        SELECT username 
                        FROM user 
                        WHERE id = %s
                    """, (user_id,))
                    user_data = cursor.fetchone()
            finally:
                connection.close()
                
            if not user_data:
                logger.error(f"User {user_id} not found")
                return None

            # Definir función async para MongoDB
            async def _create_message():
                from src.models.message_model import init_mongodb
                from src.utils.serializers import serialize_message

                # Asegurarnos de que MongoDB está inicializado
                await init_mongodb()

                # Crear mensaje
                message = Message(
                    groupId=group_id,
                    senderId=user_id,
                    senderUsername=user_data['username'],
                    type="text",
                    text=text,
                    createdAt=datetime.utcnow()
                )

                await message.insert()
                return serialize_message(message)
            
            # Ejecutar la función async
            return self.async_manager.run_async(_create_message)
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    def update_message(self, group_id: int, message_id: str, user_id: int, text: str) -> Optional[Dict]:
        """Actualiza el texto de un mensaje"""
        try:
            logger.info(f"Attempting to update message {message_id} in group {group_id} by user {user_id}")

            # Validar membresía primero (operación síncrona)
            if not self.validate_group_membership(group_id, user_id):
                logger.error(f"User {user_id} does not have access to group {group_id}")
                return None

            # Validar y convertir el ID del mensaje (operación síncrona)
            try:
                message_object_id = ObjectId(message_id)
                logger.info(f"Valid ObjectId: {message_object_id}")
            except Exception as e:
                logger.error(f"Invalid message ID format: {message_id}. Error: {e}")
                return None

            # Definir función async para MongoDB
            async def _update_message():
                # Buscar el mensaje
                message = await Message.get(message_object_id)
                if not message:
                    logger.error(f"Message {message_id} not found")
                    return None

                if message.groupId != group_id:
                    logger.error(f"Message {message_id} does not belong to group {group_id}")
                    return None

                if message.senderId != user_id:
                    logger.error(f"User {user_id} is not the sender of message {message_id}")
                    return None

                # Actualizar el mensaje
                message.text = text
                message.editedAt = datetime.utcnow()
                try:
                    await message.save()
                    logger.info(f"Message {message_id} updated successfully")
                    return serialize_message(message)
                except Exception as save_error:
                    logger.error(f"Error saving message: {save_error}")
                    raise save_error
            
            # Ejecutar la función async
            return self.async_manager.run_async(_update_message)
        except Exception as e:
            logger.error(f"Error updating message: {e}")
            raise

    def __del__(self):
        """Cleanup del async manager al destruir el controlador"""
        try:
            if hasattr(self, 'async_manager'):
                del self.async_manager
        except Exception as e:
            logger.error(f"Error cleaning up async manager: {e}")
