from flask import Blueprint, request, jsonify, Response
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from src.controllers.MessageController import MessageController
import uuid
import os

# Crear blueprint para compatibilidad
message_bp = Blueprint('messages', __name__)

# Crear namespace para Swagger
message_api = Namespace('messages', description='Operaciones de mensajes')

# Controller instance will be injected from app.py to avoid import-time side effects    
controller_instance = MessageController()

AUDIO_FOLDER = os.path.join("src", "static", "audios")
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

def set_message_controller(controller: MessageController):
    global controller_instance
    controller_instance = controller


def set_message_controller(controller: MessageController):
    global controller_instance
    controller_instance = controller


def register_socketio_events(socketio):
    """
    Registra los eventos de SocketIO para mensajes de audio
    """
    # Evento cuando un cliente se conecta
    @socketio.on("connect")
    def on_connect():
        print("✅ Cliente conectado a SocketIO")
        if controller_instance:
            controller_instance.handle_connect()

    # Evento cuando un cliente se desconecta
    @socketio.on("disconnect")
    def on_disconnect():
        print("👋 Cliente desconectado de SocketIO")
        if controller_instance:
            controller_instance.handle_disconnect()

    # Evento que recibe un chunk de audio desde el frontend
    @socketio.on("audio_chunk")
    def on_audio_chunk(data):
        # data = {"chunk": "<base64>", "transmitter_id": 123, "receiver_id": 456}
        if controller_instance:
            controller_instance.handle_audio_chunk(data, socketio)
        else:
            socketio.emit(
                'error', {'error': 'message controller not initialized'})

    # Evento cuando el usuario deja de grabar
    @socketio.on("stop_recording")
    def on_stop_recording(data):
        # data = {"transmitter_id": 123, "receiver_id": 456}
        print(f"🎙️ Evento stop_recording recibido: {data}")
        if controller_instance:
            controller_instance.handle_stop_recording(data, socketio)
        else:
            socketio.emit(
                'error', {'error': 'message controller not initialized'})


# Parser para archivos de audio
upload_parser = message_api.parser()
upload_parser.add_argument('transmitter_id', type=int,
                           required=True, location='form', help='ID del remitente')
upload_parser.add_argument(
    'receiver_id', type=int, required=True, location='form', help='ID del receptor')
upload_parser.add_argument('audio_file', type=FileStorage, required=True,
                           location='files', help='Archivo de audio (m4a, mp3, wav)')

# Modelos para Swagger
create_voice_message_model = message_api.model('CreateVoiceMessage', {
    'transmitter_id': fields.Integer(required=True, description='ID del remitente', example=1),
    'receiver_id': fields.Integer(required=True, description='ID del receptor', example=2),
    'audio_file': fields.String(required=True, description='Archivo de audio (m4a,mp3)', example='audio.m4a')
})

success_response_model = message_api.model('SuccessResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'message': fields.String(description='Mensaje de respuesta'),
    'data': fields.Raw(description='Datos adicionales')
})

error_model = message_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})

tts_message_model = message_api.model('text_to_speech', {
    'text': fields.String(required=True, description='Texto a convertir a voz', example='Hola, ¿cómo estás?')
})

# Endpoints
        
@message_api.route('/text-to-speech')
class TextToSpeech(Resource):
    @message_api.expect(tts_message_model, validate=True)
    @message_api.response(200, 'Audio generado exitosamente', success_response_model)
    @message_api.response(400, 'Error en la solicitud', error_model)
    @message_api.response(500, 'Error interno del servidor', error_model)
    @message_api.doc('text_to_speech')
    
    def post(self):
        """Convertir texto a voz utilizando Hume TTS - Devuelve audio directamente"""
        try:
            text = request.json.get('text')
            if not text:
                return {'error': 'Text is required'}, 400
                
            # Generar audio usando Hume TTS
            audio_bytes = controller_instance.textToSpeech(text)
            
            # Devolver directamente el audio como respuesta
            # Esto funciona tanto en desarrollo local como en Cloud Run
            return Response(
                audio_bytes,
                mimetype='audio/mpeg',
                headers={
                    'Content-Disposition': f'attachment; filename="tts_{uuid.uuid4().hex[:8]}.mp3"',
                    'Content-Type': 'audio/mpeg'
                }
            )

        except Exception as e:
            return {'error': str(e)}, 500
