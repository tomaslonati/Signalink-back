from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from controllers.user_contact_controller import UserContactController

# Crear blueprint para compatibilidad
user_contact_bp = Blueprint('user_contacts', __name__)

# Crear namespace para Swagger
user_contact_api = Namespace(
    'contacts', description='Operaciones de contactos de usuarios')

# Instanciar controlador
user_contact_controller = UserContactController()

# Modelos para Swagger
add_contact_model = user_contact_api.model('AddContact', {
    'user_id': fields.Integer(required=True, description='ID del usuario que añade el contacto', example=1),
    'contact_id': fields.Integer(required=True, description='ID del usuario a añadir como contacto', example=2)
})

contact_response_model = user_contact_api.model('Contact', {
    'id': fields.Integer(description='ID del contacto'),
    'username': fields.String(description='Username del contacto'),
    'name': fields.String(description='Nombre del contacto'),
    'surname': fields.String(description='Apellido del contacto'),
    'email': fields.String(description='Email del contacto'),
    'created_at': fields.String(description='Fecha de registro del usuario'),
    'contact_added_at': fields.String(description='Fecha cuando se añadió como contacto')
})

mutual_contact_response_model = user_contact_api.model('MutualContact', {
    'id': fields.Integer(description='ID del contacto'),
    'username': fields.String(description='Username del contacto'),
    'name': fields.String(description='Nombre del contacto'),
    'surname': fields.String(description='Apellido del contacto'),
    'email': fields.String(description='Email del contacto'),
    'added_by_user': fields.String(description='Fecha cuando el usuario añadió este contacto'),
    'added_by_contact': fields.String(description='Fecha cuando el contacto añadió al usuario')
})

success_response_model = user_contact_api.model('SuccessResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'message': fields.String(description='Mensaje de respuesta')
})

contact_count_model = user_contact_api.model('ContactCount', {
    'count': fields.Integer(description='Número total de contactos')
})

contact_status_model = user_contact_api.model('ContactStatus', {
    'is_contact': fields.Boolean(description='Indica si es contacto'),
    'is_mutual': fields.Boolean(description='Indica si son contactos mutuos')
})

error_model = user_contact_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})


@user_contact_api.route('/')
class ContactList(Resource):
    @user_contact_api.doc('add_contact')
    @user_contact_api.expect(add_contact_model)
    # @user_contact_api.marshal_with(success_response_model, code=201)
    @user_contact_api.response(400, 'Datos inválidos o contacto ya existe', error_model)
    def post(self):
        """
        Añadir contacto

        Añade un usuario como contacto de otro usuario.
        """
        return user_contact_controller.add_contact()


@user_contact_api.route('/<int:user_id>/<int:contact_id>')
class Contact(Resource):
    @user_contact_api.doc('remove_contact')
    # @user_contact_api.marshal_with(success_response_model)
    @user_contact_api.response(404, 'Contacto no encontrado', error_model)
    def delete(self, user_id, contact_id):
        """
        Eliminar contacto

        Elimina un contacto de la lista de contactos de un usuario.
        """
        return user_contact_controller.remove_contact(user_id, contact_id)

    @user_contact_api.doc('check_contact_status')
    # @user_contact_api.marshal_with(contact_status_model)
    def get(self, user_id, contact_id):
        """
        Verificar estado de contacto

        Verifica si dos usuarios son contactos y si la relación es mutua.
        """
        return user_contact_controller.check_contact_status(user_id, contact_id)


@user_contact_api.route('/user/<int:user_id>')
class UserContacts(Resource):
    @user_contact_api.doc('get_user_contacts')
    # @user_contact_api.marshal_list_with(contact_response_model)
    def get(self, user_id):
        """
        Obtener contactos de usuario

        Retorna todos los contactos de un usuario específico.
        """
        return user_contact_controller.get_user_contacts(user_id)


@user_contact_api.route('/user/<int:user_id>/mutual')
class UserMutualContacts(Resource):
    @user_contact_api.doc('get_mutual_contacts')
    # @user_contact_api.marshal_list_with(mutual_contact_response_model)
    def get(self, user_id):
        """
        Obtener contactos mutuos

        Retorna todos los contactos mutuos de un usuario (contactos bidireccionales).
        """
        return user_contact_controller.get_mutual_contacts(user_id)


@user_contact_api.route('/user/<int:user_id>/count')
class UserContactCount(Resource):
    @user_contact_api.doc('get_contact_count')
    # @user_contact_api.marshal_with(contact_count_model)
    def get(self, user_id):
        """
        Obtener número de contactos

        Retorna el número total de contactos de un usuario.
        """
        return user_contact_controller.get_contact_count(user_id)


@user_contact_api.route('/user/<int:user_id>/search')
class SearchContacts(Resource):
    @user_contact_api.doc('search_contacts')
    # @user_contact_api.marshal_list_with(contact_response_model)
    @user_contact_api.param('q', 'Término de búsqueda', required=True)
    def get(self, user_id):
        """
        Buscar contactos

        Busca contactos de un usuario por nombre, apellido, username o email.
        """
        return user_contact_controller.search_contacts(user_id)


@user_contact_api.route('/contact/<int:contact_id>/users')
class ContactUsers(Resource):
    @user_contact_api.doc('get_users_who_have_contact')
    # @user_contact_api.marshal_list_with(contact_response_model)
    def get(self, contact_id):
        """
        Obtener usuarios que tienen este contacto

        Retorna todos los usuarios que tienen a este usuario como contacto.
        """
        return user_contact_controller.get_users_who_have_contact(contact_id)
