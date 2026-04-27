from flask import request
from flask_restx import Resource, Namespace
from src.controllers.group_message_controller_new import MessageController
from src.middleware.auth_middleware import token_required
from datetime import datetime
import logging
from src.schemas.message_request import message_request, message_update_request

logger = logging.getLogger(__name__)
api = Namespace('messages', description='Operaciones de mensajes')
api.models[message_request.name] = message_request
api.models[message_update_request.name] = message_update_request
message_controller = MessageController()

@api.route('/<int:group_id>/messages')
class GroupMessages(Resource):
    @token_required
    def get(self, current_user, group_id: int):
        """Lista los mensajes de un grupo"""
        try:
            # Obtener parámetros
            before = request.args.get('before')
            after = request.args.get('after')
            limit = request.args.get('limit', 50, type=int)

            # Convertir fechas si existen
            if before:
                before = datetime.fromisoformat(before)
            if after:
                after = datetime.fromisoformat(after)

            # Ensure MongoDB is initialized
            message_controller._ensure_mongodb()
            
            # Get messages
            messages, error = message_controller.list_messages(
                group_id,
                current_user['user_id'],
                before=before,
                after=after,
                limit=limit
            )

            if error == "access_denied":
                return {"error": "No tiene acceso a este grupo"}, 403
            elif error:
                return {"error": f"Error interno del servidor: {error}"}, 500
            elif messages is None:
                return {"error": "Error interno del servidor - respuesta vacía"}, 500
            
            return {"messages": messages}, 200
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            return {"error": str(e)}, 500

    @token_required
    @api.expect(message_request)
    def post(self, current_user, group_id: int):
        """
        Crea un nuevo mensaje en el grupo
        
        Requiere un JSON con el siguiente formato:
        {
            "text": "El texto del mensaje",
            "type": "text"
        }
        """
        try:
            # Validar body
            if not request.is_json:
                return {"error": "Content-Type debe ser application/json"}, 400

            data = request.get_json()
            if not data or "text" not in data or "type" not in data:
                return {"error": "Debe proveer el texto y tipo del mensaje"}, 400

            if data["type"] not in ["text", "audio"]:
                return {"error": "El tipo de mensaje debe ser 'text' o 'audio'"}, 400
                
            # Ensure MongoDB is initialized
            message_controller._ensure_mongodb()
            
            # Create message
            message = message_controller.create_message(
                group_id,
                current_user['user_id'],
                data["text"]
            )

            if message is None:
                return {"error": "No tiene acceso a este grupo"}, 403
            return message, 201
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return {"error": str(e)}, 500

@api.route('/<int:group_id>/messages/<string:message_id>')
class GroupMessage(Resource):
    @token_required
    @api.expect(message_update_request)
    def patch(self, current_user, group_id: int, message_id: str):
        """
        Actualiza un mensaje existente
        
        Requiere un JSON con el siguiente formato:
        {
            "text": "El nuevo texto del mensaje"
        }
        
        El message_id debe ser el ID de MongoDB del mensaje (24 caracteres hexadecimales)
        """
        try:
            # Validar body
            if not request.is_json:
                return {"error": "Content-Type debe ser application/json"}, 400

            data = request.get_json()
            if not data or "text" not in data:
                return {"error": "Debe proveer el texto del mensaje"}, 400

            # Validar formato del message_id
            if not message_id or len(message_id) != 24:
                return {"error": "ID de mensaje inválido. Debe ser un ObjectId de MongoDB (24 caracteres hexadecimales)"}, 400

            # Ensure MongoDB is initialized
            message_controller._ensure_mongodb()
            
            try:
                # Update message
                message = message_controller.update_message(
                    group_id,
                    message_id,
                    current_user['user_id'],
                    data["text"]
                )

                if message is None:
                    return {"error": "No tiene acceso al mensaje o no existe"}, 403
                return message, 200
                
            except Exception as update_error:
                error_msg = str(update_error)
                logger.error(f"Error updating message: {error_msg}")
                
                if "Invalid ObjectId" in error_msg:
                    return {"error": "ID de mensaje inválido. Debe ser un ObjectId de MongoDB (24 caracteres hexadecimales)"}, 400
                elif "no field" in error_msg.lower():
                    return {"error": "Error interno del servidor: Estructura del mensaje inválida"}, 500
                else:
                    return {"error": "Error al actualizar el mensaje: " + error_msg}, 500
                    
        except Exception as e:
            logger.error(f"Error general en la ruta: {e}")
            return {"error": "Error interno del servidor"}, 500