from flask import request, jsonify
from services.auth_service import AuthService
from utils.validators import validate_email, validate_password

class AuthController:
    def __init__(self):
        self.auth_service = AuthService()
    
    def login(self):
        """
        Endpoint para login de usuarios
        """
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'No data provided'}, 400
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'error': 'Username and password required'}, 400
            
            # Validar credenciales
            result = self.auth_service.validate_user_credentials(username, password)
            
            if result['is_valid']:
                print("Login successful, preparing response...")
                response_data = {
                    'success': True,
                    'message': 'Login successful',
                    'token': result['token'],
                    'user': {
                        'id': result['user_id'],
                        'name': result['user_name']
                    }
                }
                return response_data, 200
            else:
                return {'error': 'Invalid credentials'}, 401
                
        except Exception as e:
            print(f"Login error: {e}")
            return {'error': 'Internal server error'}, 500
    
    def register(self):
        """
        Endpoint para registro de nuevos usuarios
        """
        try:
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400

            # Validar campos requeridos
            required_fields = ['name', 'surname', 'username', 'email', 'password', 'user_type', 'language']
            for field in required_fields:
                if not data.get(field):
                    return {'error': f'{field} is required'}, 400

            # Validar user_type
            user_type = data.get('user_type')
            if user_type not in ['glove_user', 'regular_user']:
                return {'error': 'Invalid user_type. Must be either "glove_user" or "regular_user"'}, 400

            # Validar language
            language = data.get('language')
            if language not in ['es', 'en']:
                return {'error': 'Invalid language. Must be either "es" or "en"'}, 400

            # Crear usuario
            result = self.auth_service.create_user(
                data['name'],
                data['surname'],
                data['username'],
                data['email'],
                data['password'],
                user_type,
                language
            )

            if result and result.get('success'):
                return result, 201
            else:
                return {'error': 'Failed to create user'}, 400
                
        except Exception as e:
            print(f"Register error: {e}")
            return {'error': 'Internal server error'}, 500