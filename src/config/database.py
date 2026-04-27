import mysql.connector
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()


class DatabaseConfig:
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', '136.113.227.213'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER', 'signalinkUser'),
                password=os.getenv('DB_PASSWORD', 'U4d32025!'),
                database=os.getenv('DB_NAME', 'signalink'),
                autocommit=False
            )
            return connection
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            raise e

    @staticmethod
    def test_connection():
        """Test database connection"""
        try:
            connection = DatabaseConfig.get_connection()
            if connection.is_connected():
                connection.close()
                return True
            return False
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    # MongoDB

    @staticmethod
    def get_mongo_database():
        """Obtiene la base de datos de MongoDB (async)"""
        try:
            mongo_uri = os.getenv(
                'MONGO_URI', 'mongodb://localhost:27017/messages')
            client = AsyncIOMotorClient(mongo_uri)
            # Extraer nombre de DB de la URI (antes del ? de los query params)
            db_path = mongo_uri.split('/')[-1]
            db_name = db_path.split('?')[0] if '?' in db_path else db_path
            db_name = db_name or 'messages'
            return client[db_name]
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e
