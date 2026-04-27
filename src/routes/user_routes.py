from flask import Blueprint
from flask_restx import Namespace, Resource, fields
from controllers.user_controller import UserController

# Crear blueprint para compatibilidad
user_bp = Blueprint('users', __name__)

# Crear namespace para Swagger
user_api = Namespace('users', description='Operaciones de usuarios')

# Instanciar controlador
user_controller = UserController()

# Modelos para Swagger
user_response_model = user_api.model('User', {
    'id': fields.Integer(description='ID único del usuario'),
    'name': fields.String(description='Nombre del usuario'),
    'surname': fields.String(description='Apellido del usuario'),
    'username': fields.String(description='Username del usuario'),
    'email': fields.String(description='Email del usuario'),
    'status': fields.String(description='Estado del usuario'),
    'user_type': fields.String(description='Tipo de usuario'),
    'created_at': fields.String(description='Fecha de creación')
})

error_model = user_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})


@user_api.route('/search')
class UserSearch(Resource):
    @user_api.doc('get_user_by_identifier')
    # @user_api.marshal_with(user_response_model)
    @user_api.param('identifier', 'Username o email del usuario', required=True, type='string')
    @user_api.response(404, 'Usuario no encontrado', error_model)
    @user_api.response(400, 'Parámetro identifier requerido', error_model)
    def get(self):
        """
        Buscar usuario por username o email
        
        Retorna los detalles de un usuario buscando por su username o email.
        """
        return user_controller.get_user_by_identifier()


@user_api.route('/<int:user_id>')
class User(Resource):
    @user_api.doc('get_user')
    # @user_api.marshal_with(user_response_model)
    @user_api.response(404, 'Usuario no encontrado', error_model)
    def get(self, user_id):
        """
        Obtener información de un usuario
        
        Retorna los detalles de un usuario específico por su ID.
        """
        return user_controller.get_user(user_id)