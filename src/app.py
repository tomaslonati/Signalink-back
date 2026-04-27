import sys
import os

# Agregar rutas necesarias para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.routes.group_messages_routes import api as group_messages_api
from src.routes.calibration_routes import calibration_bp, calibration_api
from src.routes.user_contact_routes import user_contact_bp, user_contact_api
from src.routes.device_routes import device_bp, device_api
from src.routes.group_routes import group_bp, group_api
from src.routes.user_routes import user_bp, user_api
from src.routes.auth_routes import auth_bp, auth_api
from src.routes.messages_routes import message_api
from src.config.database import DatabaseConfig
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api
from flask_socketio import SocketIO
from dotenv import load_dotenv
import asyncio
from src.config.cloudinary_config import CloudinaryConfig

# Path ya agregado arriba
# Agregar directorio padre para imports relativos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar configuración y rutas


# Cargar variables de entorno
load_dotenv()


def create_app():
    """
    Factory function para crear la aplicación Flask con Swagger.
    """
    app = Flask(__name__)

    # Configuración de CORS
    CORS(app, origins=["*"])  # En producción, limitar a dominios específicos

    # Configuración básica de la app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

    # Inicializar Cloudinary
    CloudinaryConfig.init_cloudinary()

    try:
        # Inicializar modelos de Beanie usando AsyncManager
        from beanie import init_beanie
        from src.models.message_model import Message
        from src.utils.async_manager import run_async_safe

        async def init_db():
            mongo_db = DatabaseConfig.get_mongo_database()
            await init_beanie(
                database=mongo_db,
                document_models=[Message]
            )

        # Usar AsyncManager para inicialización thread-safe
        try:
            # Pasar una callable para que la corrutina se cree dentro del thread
            run_async_safe(lambda: init_db())
            print("✅ Conexión a MongoDB y modelos inicializados")
        except Exception as e:
            print(f"❌ Error de conexión a MongoDB: {e}")
            raise e
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {e}")

     # Inicializar SocketIO con CORS
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Permitir todas las conexiones
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25,
        transports=['websocket', 'polling']
    )

    # Inicializar el servicio de mensajes (Whisper o Realtime)
    use_whisper = os.getenv('USE_WHISPER', 'true').lower() == 'true'

    if use_whisper:
        print("🎤 Inicializando WhisperMessageService...")
        from src.services.whisper_service import WhisperMessageService
        message_service = WhisperMessageService(socketio=socketio)
    else:
        print("🎤 Inicializando MessageService (Realtime)...")
        from src.services.message_service import MessageService
        message_service = MessageService(socketio=socketio)

    # Crear el controlador de mensajes
    from src.controllers.MessageController import MessageController
    message_controller = MessageController(message_service)

    # Registrar eventos de SocketIO para mensajes de audio
    from src.routes.messages_routes import set_message_controller, register_socketio_events
    set_message_controller(message_controller)
    register_socketio_events(socketio)
    print("✅ Eventos de SocketIO registrados para mensajes de audio")

    # Configuración de autenticación para Swagger
    authorizations = {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Pega tu token JWT aquí (sin el prefijo 'Bearer')"
        }
    }

    # Configuración de la documentación Swagger
    api = Api(
        app,
        version='1.0.0',
        title='Signalink API',
        description='API REST para la aplicación React Native de Signalink\n\nPara autenticarte:\n1. Haz login en /auth/login\n2. Copia el token del response\n3. Click en el botón "Authorize" arriba\n4. Pega el token directamente\n5. Click en "Authorize"',
        doc='/docs/',
        prefix='/api',
        authorizations=authorizations,
        # Esto hace que todos los endpoints requieran autorización por defecto
        security=[{'Bearer': []}]
    )

    # Registrar todos los namespaces
    api.add_namespace(auth_api, path='/auth')
    api.add_namespace(user_api, path='/users')
    api.add_namespace(group_api, path='/groups')
    api.add_namespace(device_api, path='/devices')
    api.add_namespace(user_contact_api, path='/contacts')
    api.add_namespace(calibration_api, path='/calibrations')
    api.add_namespace(group_messages_api, path='/groups')
    api.add_namespace(message_api, path='/messages')

    # Registrar blueprint de debug
    try:
        from src.routes.debug_routes import debug_bp
        app.register_blueprint(debug_bp)
        print("✅ Debug routes registered successfully")
    except Exception as e:
        print(f"❌ Error registering debug routes: {e}")

    # Rutas principales fuera del namespace
    @app.route('/', methods=['GET'])
    def home():
        return jsonify({
            'message': 'Signalink API',
            'version': '1.0.0',
            'status': 'active',
            'documentation': '/docs/'
        }), 200

    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Endpoint de verificación de estado general.
        """
        try:
            db_status = DatabaseConfig.test_connection()
            cloudinary_status = CloudinaryConfig.test_connection()
            return jsonify({
                'status': 'healthy',
                'database': 'connected' if db_status else 'disconnected',
                'cloudinary': 'connected' if cloudinary_status else 'disconnected',
                'timestamp': 'now'
            }), 200 if db_status else 503
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503

    # Manejo de errores global
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app, socketio


if __name__ == '__main__':
    app, socketio = create_app()
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print(f"Starting Signalink API on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Swagger documentation: http://{host}:{port}/docs/")

    socketio.run(app, debug=debug, host=host, port=port)
