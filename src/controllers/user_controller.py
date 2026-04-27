from flask import request
from models.user_model import UserModel
from utils.serializers import serialize_dict

class UserController:
    def __init__(self):
        self.user_model = UserModel()

    def get_user(self, user_id):
        """
        Obtener un usuario por su ID
        """
        try:
            user = self.user_model.get_user_by_id(user_id)
            
            if user:
                return serialize_dict(user), 200
            else:
                return {'error': 'User not found'}, 404
                
        except Exception as e:
            return {'error': str(e)}, 500

    def get_user_by_identifier(self):
        """
        Obtener un usuario por username o email
        """
        try:
            identifier = request.args.get('identifier')
            
            if not identifier:
                return {'error': 'identifier parameter is required'}, 400
            
            user = self.user_model.get_user_by_username(identifier)
            
            if user:
                return serialize_dict(user), 200
            else:
                return {'error': 'User not found'}, 404
                
        except Exception as e:
            return {'error': str(e)}, 500

    def update_user_details(self, user_id):
        try:
            data = request.get_json()

            # Validar campos requeridos
            required_fields = ['name', 'surname', 'email']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}, 400

            # Validar user_type si está presente
            user_type = data.get('user_type', None)
            if user_type and user_type not in ['glove_user', 'regular_user']:
                return {'error': 'Invalid user_type. Must be either "glove_user" or "regular_user"'}, 400

            # Si no se proporciona user_type, obtener el actual del usuario
            if not user_type:
                current_user = self.user_model.get_user_by_id(user_id)
                user_type = current_user.get('user_type', 'regular_user')

            updated_user = self.user_model.update_user(
                user_id, 
                data['name'], 
                data['surname'], 
                data['email'],
                user_type
            )

            if updated_user:
                return serialize_dict(updated_user), 200
            return {"message": "Failed to update user"}, 400
        except Exception as e:
            return {'error': str(e)}, 500

    def delete_user(self, user_id):
        success = self.user_model.delete_user(user_id)
        if success:
            return {"message": "User deleted successfully"}, 200
        return {"message": "Failed to delete user"}, 400