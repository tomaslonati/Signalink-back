from config.database import DatabaseConfig
from services.database_service import DatabaseService

class UserContactModel:
    def __init__(self):
        connection = DatabaseConfig.get_connection()
        self.db_service = DatabaseService(connection)

    def add_contact(self, user_id, contact_id):
        """
        Añade un contacto a un usuario
        """
        try:
            # Validar que no se añada a sí mismo como contacto
            if user_id == contact_id:
                return {
                    'success': False,
                    'error': 'Cannot add yourself as a contact'
                }

            result = self.db_service.call_stored_proc('AddContact', (user_id, contact_id))
            return {
                'success': bool(result['success']),
                'message': 'Contact added successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def remove_contact(self, user_id, contact_id):
        """
        Elimina un contacto de un usuario
        """
        try:
            result = self.db_service.call_stored_proc('RemoveContact', (user_id, contact_id))
            return {
                'success': bool(result['deleted']),
                'message': 'Contact removed successfully' if result['deleted'] else 'Contact not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_contacts(self, user_id):
        """
        Obtiene todos los contactos de un usuario
        """
        try:
            return self.db_service.call_stored_proc('GetUserContacts', (user_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting user contacts: {e}")
            return []

    def get_users_who_have_contact(self, contact_id):
        """
        Obtiene todos los usuarios que tienen a este usuario como contacto
        """
        try:
            return self.db_service.call_stored_proc('GetUsersWhoHaveContact', (contact_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting users who have contact: {e}")
            return []

    def check_contact_status(self, user_id, contact_id):
        """
        Verifica el estado de contacto entre dos usuarios
        """
        try:
            result = self.db_service.call_stored_proc('CheckContactStatus', (user_id, contact_id))
            return {
                'is_contact': bool(result['is_contact']),
                'is_mutual': bool(result['is_mutual'])
            }
        except Exception as e:
            print(f"Error checking contact status: {e}")
            return {'is_contact': False, 'is_mutual': False}

    def get_mutual_contacts(self, user_id):
        """
        Obtiene todos los contactos mutuos de un usuario
        """
        try:
            return self.db_service.call_stored_proc('GetMutualContacts', (user_id,), fetch_all=True)
        except Exception as e:
            print(f"Error getting mutual contacts: {e}")
            return []

    def search_contacts(self, user_id, search_term):
        """
        Busca contactos de un usuario por nombre, apellido, username o email
        """
        try:
            return self.db_service.call_stored_proc('SearchContacts', 
                (user_id, search_term), fetch_all=True)
        except Exception as e:
            print(f"Error searching contacts: {e}")
            return []

    def get_contact_count(self, user_id):
        """
        Obtiene el número total de contactos de un usuario
        """
        try:
            result = self.db_service.call_stored_proc('GetContactCount', (user_id,))
            return result['count'] if result else 0
        except Exception as e:
            print(f"Error getting contact count: {e}")
            return 0
