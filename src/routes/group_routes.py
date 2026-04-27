from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from controllers.group_controller import GroupController
from middleware.auth_middleware import token_required

# Crear blueprint para compatibilidad
group_bp = Blueprint('groups', __name__)

# Crear namespace para Swagger
group_api = Namespace(
    'groups', description='Operaciones de grupos de usuarios')

# Instanciar controlador
group_controller = GroupController()

# Modelos para Swagger
create_group_model = group_api.model('CreateGroup', {
    'name': fields.String(required=True, description='Nombre del grupo', example='Familia'),
    'owner_id': fields.Integer(required=True, description='ID del propietario del grupo', example=1)
})

update_group_model = group_api.model('UpdateGroup', {
    'name': fields.String(required=True, description='Nuevo nombre del grupo', example='Familia Rodriguez')
})

group_response_model = group_api.model('Group', {
    'id': fields.Integer(description='ID único del grupo'),
    'owner_id': fields.Integer(description='ID del propietario'),
    'name': fields.String(description='Nombre del grupo'),
    'owner_username': fields.String(description='Username del propietario')
})

group_member_model = group_api.model('GroupMember', {
    'user_id': fields.Integer(required=True, description='ID del usuario a añadir', example=2)
})

member_response_model = group_api.model('Member', {
    'id': fields.Integer(description='ID del usuario'),
    'username': fields.String(description='Username del usuario'),
    'name': fields.String(description='Nombre del usuario'),
    'surname': fields.String(description='Apellido del usuario'),
    'email': fields.String(description='Email del usuario')
})

success_response_model = group_api.model('SuccessResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'message': fields.String(description='Mensaje de respuesta'),
    'group_id': fields.Integer(description='ID del grupo (en creación)')
})

error_model = group_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})


@group_api.route('/')
class GroupList(Resource):
    @group_api.doc('create_group')
    @group_api.expect(create_group_model)
    # @group_api.marshal_with(success_response_model, code=201)
    @group_api.response(400, 'Datos inválidos', error_model)
    def post(self):
        """
        Crear nuevo grupo

        Crea un nuevo grupo con el usuario especificado como propietario.
        """
        return group_controller.create_group()


@group_api.route('/<int:group_id>')
@group_api.param('Authorization', 'Token JWT', _in='header', required=True)
class Group(Resource):
    @group_api.doc('get_group')
    @token_required
    @group_api.response(404, 'Grupo no encontrado', error_model)
    @group_api.response(401, 'No autorizado - Token faltante o inválido', error_model)
    def get(self, group_id, current_user=None):
        """
        Obtener información de un grupo

        Retorna los detalles de un grupo específico. Requiere autenticación.
        """
        # El parámetro current_user vendrá del decorador token_required
        request.user_id = current_user['user_id'] if current_user else None
        return group_controller.get_group(group_id)

    @group_api.doc('update_group', security='Bearer')
    @token_required
    @group_api.expect(update_group_model)
    # @group_api.marshal_with(success_response_model)
    @group_api.response(404, 'Grupo no encontrado', error_model)
    @group_api.response(401, 'No autorizado - Token faltante o inválido', error_model)
    @group_api.response(403, 'No autorizado - No eres el propietario del grupo', error_model)
    def put(self, group_id, current_user=None):
        """
        Actualizar grupo

        Actualiza el nombre del grupo. Solo el propietario puede realizar esta acción.
        """
        request.user_id = current_user['user_id']  # Pasar el user_id al request
        return group_controller.update_group(group_id)

    @group_api.doc('delete_group', security='Bearer')
    @token_required
    # @group_api.marshal_with(success_response_model)
    @group_api.response(404, 'Grupo no encontrado', error_model)
    @group_api.response(401, 'No autorizado - Token faltante o inválido', error_model)
    @group_api.response(403, 'No autorizado - No eres el propietario del grupo', error_model)
    def delete(self, group_id, current_user=None):
        """
        Eliminar grupo

        Elimina un grupo y todos sus miembros. Solo el propietario puede realizar esta acción.
        """
        request.user_id = current_user['user_id']  # Pasar el user_id al request
        return group_controller.delete_group(group_id)


@group_api.route('/owner/<int:owner_id>')
class GroupsByOwner(Resource):
    @group_api.doc('get_groups_by_owner')
    # @group_api.marshal_list_with(group_response_model)
    def get(self, owner_id):
        """
        Obtener grupos por propietario

        Retorna todos los grupos que pertenecen a un usuario específico.
        """
        return group_controller.get_groups_by_owner(owner_id)


@group_api.route('/<int:group_id>/members')
class GroupMembers(Resource):
    @group_api.doc('get_group_members')
    # @group_api.marshal_list_with(member_response_model)
    @group_api.response(404, 'Grupo no encontrado', error_model)
    def get(self, group_id):
        """
        Obtener miembros del grupo

        Retorna la lista de todos los miembros de un grupo.
        """
        return group_controller.get_group_members(group_id)

    @group_api.doc('add_group_member')
    @group_api.expect(group_member_model)
    # @group_api.marshal_with(success_response_model)
    @group_api.response(400, 'Usuario ya es miembro', error_model)
    @group_api.response(404, 'Grupo o usuario no encontrado', error_model)
    def post(self, group_id):
        """
        Añadir miembro al grupo

        Añade un usuario como miembro del grupo.
        """
        return group_controller.add_member(group_id)


@group_api.route('/<int:group_id>/members/<int:user_id>')
class GroupMember(Resource):
    @group_api.doc('remove_group_member')
    # @group_api.marshal_with(success_response_model)
    @group_api.response(404, 'Grupo o miembro no encontrado', error_model)
    def delete(self, group_id, user_id):
        """
        Eliminar miembro del grupo

        Elimina un usuario de la lista de miembros del grupo.
        """
        return group_controller.remove_member(group_id, user_id)


@group_api.route('/user/<int:user_id>')
class UserGroups(Resource):
    @group_api.doc('get_user_groups')
    # @group_api.marshal_list_with(group_response_model)
    def get(self, user_id):
        """
        Obtener grupos del usuario

        Retorna todos los grupos de los que es miembro un usuario.
        """
        return group_controller.get_user_groups(user_id)
