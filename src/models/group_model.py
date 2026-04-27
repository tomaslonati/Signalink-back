from config.database import DatabaseConfig
from services.database_service import DatabaseService


class GroupModel:
    def __init__(self):
        connection = DatabaseConfig.get_connection()
        self.db_service = DatabaseService(connection)

    def create_group(self, owner_id, name):
        """
        Crea un nuevo grupo
        """
        try:
            result = self.db_service.call_stored_proc('sp_groups_create', (owner_id, name))
            
            if result and 'group_id' in result:
                return {
                    'success': True,
                    'group_id': result['group_id'],
                    'message': 'Group created successfully'
                }
            return {
                'success': False,
                'error': 'Failed to create group'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_group_by_id(self, group_id):
        """
        Obtiene un grupo por su ID
        """
        try:
            return self.db_service.call_stored_proc('sp_groups_get_by_id', (group_id,))
        except Exception as e:
            print(f"Error getting group: {e}")
            return None

    def get_groups_by_owner(self, owner_id):
        """
        Obtiene todos los grupos de un propietario
        """
        try:
            return self.db_service.call_stored_proc('GetGroupsByOwner', 
                (owner_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting groups by owner: {e}")
            return []

    def update_group(self, group_id, name):
        """
        Actualiza el nombre de un grupo
        """
        try:
            self.db_service.call_stored_proc('sp_groups_update', 
                (group_id, name))
            
            return True
        except Exception as e:
            print(f"Error updating group: {e}")
            return False

    def delete_group(self, group_id, owner_id):
        """
        Elimina un grupo (solo el propietario puede hacerlo)
        """
        try:
            result = self.db_service.call_stored_proc('sp_groups_delete', 
                (group_id, owner_id))
            
            if result and result.get('deleted', False):
                return {
                    'success': True,
                    'message': 'Group deleted successfully'
                }
            return {
                'success': False,
                'error': 'Failed to delete group or user is not the owner'
            }
        except Exception as e:
            print(f"Error deleting group: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class GroupMemberModel:
    def __init__(self):
        connection = DatabaseConfig.get_connection()
        self.db_service = DatabaseService(connection)

    def add_member(self, group_id, user_id):
        """
        Añade un miembro a un grupo
        """
        try:
            result = self.db_service.call_stored_proc('AddGroupMember', 
                (group_id, user_id))
            
            return {
                'success': bool(result['success']),
                'message': 'Member added successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def remove_member(self, group_id, user_id):
        """
        Elimina un miembro de un grupo
        """
        try:
            result = self.db_service.call_stored_proc('RemoveGroupMember', 
                (group_id, user_id))
            
            if result['deleted']:
                return {
                    'success': True,
                    'message': 'Member removed successfully'
                }
            return {
                'success': False,
                'error': 'Member not found in group'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_group_members(self, group_id):
        """
        Obtiene todos los miembros de un grupo
        """
        try:
            return self.db_service.call_stored_proc('GetGroupMembers', 
                (group_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting group members: {e}")
            return []

    def get_user_groups(self, user_id):
        """
        Obtiene todos los grupos de los que es miembro un usuario
        """
        try:
            return self.db_service.call_stored_proc('sp_groups_list_by_member', 
                (user_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting user groups: {e}")
            return []

    def check_member_status(self, group_id, user_id):
        """
        Verifica si un usuario es miembro de un grupo
        """
        try:
            result = self.db_service.call_stored_proc('CheckMemberStatus', 
                (group_id, user_id))
            return bool(result['is_member'])
        except Exception as e:
            print(f"Error checking membership: {e}")
            return False
