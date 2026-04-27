from config.database import DatabaseConfig
from services.database_service import DatabaseService

class UserModel:
    def __init__(self):
        connection = DatabaseConfig.get_connection()
        self.db_service = DatabaseService(connection)

    def create_user(self, name, surname, username, email, password, user_type='regular_user', language='es'):
        """
        Crea un nuevo usuario
        """
        try:
            result = self.db_service.call_stored_proc('CreateUser', 
                (name, surname, username, email, password, user_type, language))
            return result['user_id'] if result else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def get_user_by_username(self, username):
        """
        Obtiene un usuario por su username o email
        """
        try:
            return self.db_service.call_stored_proc('GetUserByUsernameOrEmail', (username,))
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    def get_user_by_id(self, user_id):
        """
        Obtiene un usuario por su ID
        """
        try:
            return self.db_service.call_stored_proc('GetUserById', (user_id,))
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def validate_user_credentials(self, username, password):
        """
        Valida las credenciales del usuario
        """
        try:
            result = self.db_service.call_stored_proc('ValidateUserCredentials', 
                (username, password))
            if result:
                return {
                    'is_valid': bool(result['is_valid']),
                    'user_id': result['user_id'],
                    'user_name': result['user_name']
                }
            return {'is_valid': False, 'user_id': None, 'user_name': None}
        except Exception as e:
            print(f"Error validating credentials: {e}")
            return {'is_valid': False, 'user_id': None, 'user_name': None}

    def update_user(self, user_id, name, surname, email, user_type, language='es'):
        """
        Actualiza los datos de un usuario
        """
        try:
            result = self.db_service.call_stored_proc('UpdateUser', 
                (user_id, name, surname, email, user_type, language))
            return bool(result['updated']) if result else False
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, user_id):
        """
        Elimina un usuario (soft delete)
        """
        try:
            result = self.db_service.call_stored_proc('DeleteUser', (user_id,))
            return bool(result['deleted']) if result else False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False