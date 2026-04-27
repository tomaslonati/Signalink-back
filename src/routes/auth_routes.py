from flask import Blueprint, request, jsonify
from flask_restx import Namespace, Resource, fields
from controllers.auth_controller import AuthController

# Crear blueprint para compatibilidad
auth_bp = Blueprint('auth', __name__)

# Crear namespace para Swagger
auth_api = Namespace('auth', description='Operaciones de autenticación')

# Instanciar controlador
auth_controller = AuthController()

# Modelos para Swagger
login_model = auth_api.model('Login', {
    'username': fields.String(required=True, description='Username o email del usuario', example='usuario@example.com'),
    'password': fields.String(required=True, description='Contraseña del usuario', example='password123')
})

register_model = auth_api.model('Register', {
    'name': fields.String(required=True, description='Nombre del usuario', example='Juan'),
    'surname': fields.String(required=True, description='Apellido del usuario', example='Pérez'),
    'username': fields.String(required=True, description='Nombre de usuario único', example='juanperez'),
    'email': fields.String(required=True, description='Email del usuario', example='juan@example.com'),
    'password': fields.String(required=True, description='Contraseña del usuario', example='password123'),
    'user_type': fields.String(required=True, description='Tipo de usuario', enum=['glove_user', 'regular_user'], example='regular_user'),
    'language': fields.String(required=True, description='Idioma del usuario', enum=['es', 'en'], example='es')
})

user_response_model = auth_api.model('User', {
    'id': fields.Integer(description='ID único del usuario'),
    'name': fields.String(description='Nombre del usuario'),
    'user_type': fields.String(description='Tipo de usuario', enum=['glove_user', 'regular_user'])
})

login_response_model = auth_api.model('LoginResponse', {
    'success': fields.Boolean(description='Indica si el login fue exitoso'),
    'message': fields.String(description='Mensaje de respuesta'),
    'token': fields.String(description='Token JWT de autenticación'),
    'user': fields.Nested(user_response_model, description='Datos del usuario')
})

register_response_model = auth_api.model('RegisterResponse', {
    'success': fields.Boolean(description='Indica si el registro fue exitoso'),
    'message': fields.String(description='Mensaje de respuesta'),
    'token': fields.String(description='Token JWT de autenticación'),
    'user': fields.Nested(user_response_model, description='Datos del usuario creado')
})

error_model = auth_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})

health_model = auth_api.model('Health', {
    'status': fields.String(description='Estado del servicio'),
    'module': fields.String(description='Módulo específico')
})

@auth_api.route('/login')
class Login(Resource):
    @auth_api.doc('login_user')
    @auth_api.expect(login_model)
    @auth_api.marshal_with(login_response_model, code=200)
    @auth_api.response(401, 'Credenciales inválidas', error_model)
    @auth_api.response(400, 'Datos requeridos faltantes', error_model)
    def post(self):
        """
        Autenticar usuario existente
        
        Permite a un usuario autenticarse usando username/email y contraseña.
        Retorna los datos del usuario si las credenciales son válidas.
        """
        return auth_controller.login()

@auth_api.route('/register')
class Register(Resource):
    @auth_api.doc('register_user')
    @auth_api.expect(register_model)
    @auth_api.marshal_with(register_response_model, code=201)
    @auth_api.response(400, 'Datos inválidos o usuario ya existe', error_model)
    def post(self):
        """
        Registrar nuevo usuario
        
        Crea una nueva cuenta de usuario en el sistema.
        Valida que el username y email sean únicos.
        """
        return auth_controller.register()

@auth_api.route('/health')
class AuthHealth(Resource):
    @auth_api.doc('auth_health_check')
    @auth_api.marshal_with(health_model)
    def get(self):
        """
        Health check del módulo de autenticación
        
        Verifica que el módulo de autenticación esté funcionando correctamente.
        """
        return {'status': 'healthy', 'module': 'auth'}, 200