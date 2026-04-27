from config.database import DatabaseConfig
import bcrypt
import hashlib
import jwt
import os
from datetime import datetime, timedelta

class AuthService:
    def __init__(self):
        self.db_config = DatabaseConfig()
    
    def validate_user_credentials(self, username, password):
        """
        Valida las credenciales del usuario directamente en la base de datos
        """
        connection = None
        cursor = None
        try:
            connection = self.db_config.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            print(f"Validating credentials for user: {username}")
            
            # Llamar al stored procedure de login
            cursor.callproc('sp_auth_login', [username])
            
            # Obtener el resultado
            for result in cursor.stored_results():
                user = result.fetchone()
            
            if user:
                print(f"User found: ID={user['id']}, Name={user['name']}")
                stored_password = user['password']
                
                # Verificar contraseña
                password_valid = False
                
                if stored_password.startswith('$2b$'):
                    # Es bcrypt
                    password_valid = bcrypt.checkpw(
                        password.encode('utf-8'), 
                        stored_password.encode('utf-8')
                    )
                    print("Checking bcrypt password...")
                else:
                    # Podría ser SHA256 o texto plano
                    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                    password_valid = (stored_password == sha256_hash or stored_password == password)
                    print(f"Checking SHA256/plain password. Input: {password}, Stored: {stored_password[:20]}...")
                
                if password_valid:
                    print("✅ Password is valid")
                    try:
                        # Generar token JWT
                        print("Generating JWT token...")
                        token = self.generate_token(user['id'], user['name'])
                        print(f"Complete token generated: {token}")
                        return {
                            'is_valid': True,
                            'user_id': user['id'],
                            'user_name': user['name'],
                            'token': token
                        }
                    except Exception as e:
                        print(f"Error generating token: {str(e)}")
                        raise
                else:
                    print("❌ Password is invalid")
                    return {'is_valid': False, 'user_id': None, 'user_name': None}
            else:
                print("❌ User not found")
                return {'is_valid': False, 'user_id': None, 'user_name': None}
            
        except Exception as e:
            print(f"Error validating credentials: {e}")
            return {'is_valid': False, 'user_id': None, 'user_name': None}
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def generate_token(self, user_id, user_name):
        """
        Genera un token JWT para el usuario
        """
        try:
            print(f"Generating token for user_id: {user_id}, user_name: {user_name}")
            payload = {
                'user_id': user_id,
                'user_name': user_name,
                'exp': datetime.utcnow() + timedelta(days=1)  # Token expira en 24 horas
            }
            print("Payload created")
            
            secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
            print(f"Using secret key: {secret_key[:5]}...")
            
            token = jwt.encode(
                payload,
                secret_key,
                algorithm='HS256'
            )
            print("Token encoded successfully")
            return token
        except Exception as e:
            print(f"Error in generate_token: {str(e)}")
            raise

    def decode_token(self, token):
        """
        Decodifica y valida un token JWT
        """
        try:
            payload = jwt.decode(
                token,
                os.getenv('SECRET_KEY', 'dev-secret-key'),
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None

    def hash_password(self, password):
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def create_user(self, name, surname, username, email, password, user_type='regular_user', language='es'):
        """
        Crea un nuevo usuario en la base de datos usando el stored procedure
        """
        connection = None
        cursor = None
        try:
            connection = self.db_config.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Hash the password
            hashed_password = self.hash_password(password)
            
            # Llamar al stored procedure
            cursor.callproc('CreateUser', 
                          (name, surname, username, email, hashed_password, user_type, language))
            
            # Hacer commit de la transacción antes de obtener resultados
            connection.commit()
            
            # Obtener el resultado
            result = None
            for result_cursor in cursor.stored_results():
                result = result_cursor.fetchone()

            print(f"CreateUser SP result: {result}")

            if not result or 'user_id' not in result:
                return {
                    'success': False,
                    'error': 'Failed to create user'
                }

            # Generar token para el nuevo usuario
            token = self.generate_token(result['user_id'], result.get('name', ''))
            
            return {
                'success': True,
                'message': 'User registered successfully',
                'token': token,
                'user': {
                    'id': result['user_id'],
                    'name': result.get('name', ''),
                    'user_type': result.get('user_type', 'regular_user')
                }
            }
            
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Error registering user: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()