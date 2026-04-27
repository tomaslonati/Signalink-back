from flask import request, jsonify
import logging
from typing import Optional, Any

# Import here for type only (to avoid import cycles at module import time)
try:
    from src.services.message_service import MessageService  # type: ignore
except Exception:
    MessageService = Any  # fallback for typing

# Configurar logging
logger = logging.getLogger(__name__)


class MessageController:
    def __init__(self, message_service: Optional[Any] = None):
        """Controller that receives socketio events and HTTP requests related to messages.

        The MessageService should be created once (in app.py) and injected here so the
        WebSocket connection and event loop are shared across the app.
        """
        if message_service is None and MessageService is not None:
            # Fallback: create an instance without socketio (not recommended)
            self.message_service = MessageService()
        else:
            self.message_service = message_service

    def create_text_message(self, data):
        """Crear un mensaje de texto"""
        try:
            if not data.get('transmitter_id') or not data.get('receiver_id') or not data.get('content'):
                return {'error': 'All fields are required'}, 400
            
            return self.message_service.create_text_message(
                transmitter_id=data['transmitter_id'],
                receiver_id=data['receiver_id'],
                content=data['content']
            )
        except Exception as e:
            logger.error(f"Error creating text message: {str(e)}")
            return {'error': 'Failed to create text message'}, 500

    def handle_connect(self):
        """Maneja la conexión de un cliente a Socket.IO"""
        try:
            logger.info("Client connected to Socket.IO")
            return {'success': True}
        except Exception as e:
            logger.error(f"Error handling connect: {str(e)}")
            return {'error': str(e)}, 500

    def handle_disconnect(self):
        """Maneja la desconexión de un cliente de Socket.IO"""
        try:
            logger.info("Client disconnected from Socket.IO")
            return {'success': True}
        except Exception as e:
            logger.error(f"Error handling disconnect: {str(e)}")
            return {'error': str(e)}, 500

    def handle_audio_chunk(self, data, socketio):
        """
        Recibe el audio del frontend y lo reenvía al servicio de OpenAI
        """
        try:
            audio_b64 = data.get("audio") or data.get("chunk")
            transmitter_id = data.get("transmitter_id")
            receiver_id = data.get("receiver_id")
            
            # Log de lo que llega del frontend  
            chunk_size = len(audio_b64) if audio_b64 else 0
            print(f"🎤 Controller: Recibido chunk de {chunk_size} caracteres")
            print(f"👥 IDs: {transmitter_id} -> {receiver_id}")
            
            # Solo mostrar una muestra del chunk si es muy largo
            if chunk_size > 100:
                print(f"🔍 Muestra del chunk: {audio_b64[:50]}...{audio_b64[-10:]}")
            else:
                print(f"🔍 Chunk completo: {audio_b64}")
            
            print("=" * 80)
            
            if not audio_b64:
                logger.error("No audio data provided")
                return {'error': 'No audio data provided'}, 400
            
            # Enviar chunk de audio al servicio
            # The service exposes a thread-safe send_audio_chunk method
            self.message_service.send_audio_chunk(audio_b64)
            return {'success': True}
        except Exception as e:
            logger.error(f"Error handling audio chunk: {str(e)}")
            return {'error': str(e)}, 500

    def handle_stop_recording(self, data, socketio):
        """
        Cuando el usuario deja de grabar, cierra el buffer
        y envía el texto resultante al frontend
        """
        try:
            transmitter_id = data.get("transmitter_id")
            receiver_id = data.get("receiver_id")
            
            # Finalizar grabación y obtener transcripción
            # We pass optional metadata which can be used to tag the transcription
            metadata = {
                'transmitter_id': transmitter_id,
                'receiver_id': receiver_id,
            }
            self.message_service.commit_audio(metadata)
            return {'success': True}
        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return {'error': str(e)}, 500

    def get_conversation(self, group_id):
        """Obtener conversación en un grupo"""
        try:
            if not group_id:
                return {'error': 'Group ID is required'}, 400

            return self.message_service.get_conversation(group_id)
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return {'error': 'Failed to retrieve conversation'}, 500
        
    def textToSpeech(self, text: str):
        """Genera audio a partir de texto utilizando Hume TTS"""
        try:
            if not text:
                raise ValueError('Text is required')
            audio_bytes = self.message_service.generate_audio(text)
            return audio_bytes
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise e
            raise e
