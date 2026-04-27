import unittest
import sys
import os

# Agregar el directorio src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.auth_service import AuthService

class TestAuthService(unittest.TestCase):


    def setUp(self):
        self.auth_service = AuthService()

    def test_validate_user_credentials_success(self):
        """
        Test que valida credenciales correctas
        Nota: Este test requiere que exista un usuario de prueba en la BD
        """
        username = "test_user"
        password = "test_password"
        result = self.auth_service.validate_user_credentials(username, password)
        
        # Verificar que el resultado tenga la estructura esperada
        self.assertIsInstance(result, dict)
        self.assertIn('is_valid', result)
        self.assertIn('user_id', result)
        self.assertIn('user_name', result)

    def test_validate_user_credentials_failure(self):
        """
        Test que valida credenciales incorrectas
        """
        username = "invalid_user"
        password = "wrong_password"
        result = self.auth_service.validate_user_credentials(username, password)
        
        # Verificar que el resultado indique credenciales inválidas
        self.assertIsInstance(result, dict)
        self.assertFalse(result['is_valid'])
        self.assertIsNone(result['user_id'])
        self.assertIsNone(result['user_name'])

    def test_hash_password(self):
        """
        Test para verificar que el hash de contraseñas funciona
        """
        password = "test_password_123"
        hashed = self.auth_service.hash_password(password)
        
        # Verificar que se genera un hash
        self.assertIsNotNone(hashed)
        self.assertNotEqual(password, hashed)
        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith('$2b$'))  # Verificar que es un hash bcrypt
        
        # Verificar que bcrypt puede verificar el password con el hash
        import bcrypt
        self.assertTrue(
            bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        )

if __name__ == '__main__':
    unittest.main()