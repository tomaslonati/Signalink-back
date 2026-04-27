from flask import request, jsonify
from models.group_model import GroupModel, GroupMemberModel
from services.auth_service import AuthService
from utils.serializers import serialize_list, serialize_dict


class GroupController:
    def __init__(self):
        self.group_model = GroupModel()
        self.group_member_model = GroupMemberModel()

    def create_group(self):
        """
        Crear un nuevo grupo
        """
        try:
            data = request.get_json()

            if not data:
                return {'error': 'No data provided'}, 400

            owner_id = data.get('owner_id')
            name = data.get('name')

            if not owner_id or not name:
                return {'error': 'owner_id and name are required'}, 400

            # Crear el grupo
            result = self.group_model.create_group(owner_id, name)

            if result['success']:
                # Añadir al creador como miembro del grupo
                group_id = result.get('group_id')
                member_result = self.group_member_model.add_member(group_id, owner_id)
                
                if member_result['success']:
                    return {
                        'success': True,
                        'message': 'Group created and owner added as member',
                        'group_id': group_id
                    }, 201
                else:
                    # Si falla al añadir al miembro, eliminar el grupo creado
                    self.group_model.delete_group(group_id, owner_id)
                    return {'error': 'Failed to add owner as member'}, 500
            else:
                return {'error': result['error']}, 400

        except Exception as e:
            return {'error': str(e)}, 500

    def get_group(self, group_id):
        """
        Obtener información de un grupo
        """
        try:
            group = self.group_model.get_group_by_id(group_id)

            if group:
                return serialize_dict(group), 200
            else:
                return {'error': 'Group not found'}, 404

        except Exception as e:
            return {'error': str(e)}, 500

    def update_group(self, group_id):
        """
        Actualizar información de un grupo
        """
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400

            name = data.get('name')
            if not name:
                return {'error': 'name is required'}, 400

            # Obtener el user_id del request (puesto por el middleware)
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return {'error': 'User ID not found in token'}, 401

            # Verificar que el grupo existe y el usuario es el propietario
            group = self.group_model.get_group_by_id(group_id)
            if not group:
                return {'error': 'Group not found'}, 404

            # Verificar que el usuario es el propietario
            if str(group['owner_id']) != str(user_id):
                return {'error': 'You are not authorized to update this group'}, 403

            result = self.group_model.update_group(group_id, name)
            
            return {
                'success': True,
                'message': 'Group updated successfully'
            }

        except Exception as e:
            return {'error': str(e)}, 500

    def delete_group(self, group_id):
        """
        Eliminar un grupo (solo el propietario puede hacerlo)
        """
        try:
            # Obtener el user_id del token (puesto por el middleware)
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return {'error': 'User ID not found in token'}, 401

            # Verificar que el grupo existe
            group = self.group_model.get_group_by_id(group_id)
            if not group:
                return {'error': 'Group not found'}, 404

            # Verificar que el usuario es el propietario
            if str(group['owner_id']) != str(user_id):
                return {'error': 'You are not authorized to delete this group'}, 403

            # Intentar eliminar el grupo
            result = self.group_model.delete_group(group_id, user_id)
            
            if result['success']:
                return result, 200
            else:
                return {'error': result['error']}, 400

        except Exception as e:
            print(f"Error in delete_group: {e}")
            return {'error': str(e)}, 500

    def get_groups_by_owner(self, owner_id):
        """
        Obtener todos los grupos de un propietario
        """
        try:
            groups = self.group_model.get_groups_by_owner(owner_id)
            return serialize_list(groups), 200

        except Exception as e:
            return {'error': str(e)}, 500

    def get_group_members(self, group_id):
        """
        Obtener miembros de un grupo
        """
        try:
            # Verificar que el grupo existe
            group = self.group_model.get_group_by_id(group_id)
            if not group:
                return {'error': 'Group not found'}, 404

            members = self.group_member_model.get_group_members(group_id)
            return serialize_list(members), 200

        except Exception as e:
            return {'error': str(e)}, 500

    def add_member(self, group_id):
        """
        Añadir un miembro al grupo
        """
        try:
            data = request.get_json()

            if not data:
                return {'error': 'No data provided'}, 400

            user_id = data.get('user_id')

            if not user_id:
                return {'error': 'user_id is required'}, 400

            # Verificar que el grupo existe
            group = self.group_model.get_group_by_id(group_id)
            if not group:
                return {'error': 'Group not found'}, 404

            result = self.group_member_model.add_member(group_id, user_id)

            if result['success']:
                return result, 201
            else:
                return {'error': result['error']}, 400

        except Exception as e:
            return {'error': str(e)}, 500

    def remove_member(self, group_id, user_id):
        """
        Eliminar un miembro del grupo
        """
        try:
            # Verificar que el grupo existe
            group = self.group_model.get_group_by_id(group_id)
            if not group:
                return {'error': 'Group not found'}, 404

            result = self.group_member_model.remove_member(group_id, user_id)

            if result['success']:
                return result, 200
            else:
                return {'error': result['error']}, 404

        except Exception as e:
            return {'error': str(e)}, 500

    def get_user_groups(self, user_id):
        """
        Obtener grupos donde es miembro un usuario
        """
        try:
            groups = self.group_member_model.get_user_groups(user_id)
            return serialize_list(groups), 200

        except Exception as e:
            return {'error': str(e)}, 500
