import unittest
from src.services.auth_service import AuthService
from src.config.database import DatabaseConfig

class TestAuthService(unittest.TestCase):

    def setUp(self):
        self.auth_service = AuthService()
        self.db_config = DatabaseConfig()
        # Create a test user
        self.create_test_user()

    def create_test_user(self):
        connection = self.db_config.get_connection()
        cursor = connection.cursor()
        try:
            # Hash the test password
            hashed_password = self.auth_service.hash_password('valid_password')
            # Delete test user if exists
            cursor.execute("DELETE FROM user WHERE username = 'valid_username'")
            # Create test user
            cursor.execute("""
                INSERT INTO user (username, password, email, name, surname, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('valid_username', hashed_password, 'test@test.com', 'Test', 'User', 'active'))
            connection.commit()
        finally:
            cursor.close()
            if connection.is_connected():
                connection.close()

    def tearDown(self):
        # Clean up test user
        connection = self.db_config.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM user WHERE username = 'valid_username'")
            connection.commit()
        finally:
            cursor.close()
            if connection.is_connected():
                connection.close()

    def test_validate_user_credentials_success(self):
        # Test with valid credentials
        result = self.auth_service.validate_user_credentials('valid_username', 'valid_password')
        self.assertIsInstance(result, dict)
        self.assertTrue(result['is_valid'])

    def test_validate_user_credentials_failure(self):
        # Test with invalid credentials
        result = self.auth_service.validate_user_credentials('invalid_username', 'invalid_password')
        self.assertIsInstance(result, dict)
        self.assertFalse(result['is_valid'])

if __name__ == '__main__':
    unittest.main()