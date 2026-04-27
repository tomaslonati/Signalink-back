import mysql.connector
import logging
from typing import Optional, Union, List, Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos"""
    pass


class DatabaseService:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def call_stored_proc(self, proc_name: str, params: Optional[tuple] = None,
                         fetch_all: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Ejecuta un stored procedure y devuelve el resultado.

        Args:
            proc_name (str): Nombre del stored procedure
            params (tuple, optional): Parámetros para el stored procedure
            fetch_all (bool): Si es True, devuelve todas las filas, si es False, devuelve la primera

        Returns:
            Union[Dict[str, Any], List[Dict[str, Any]], None]: Resultado del stored procedure

        Raises:
            DatabaseError: Si ocurre un error al ejecutar el stored procedure
        """
        cursor = None
        try:
            cursor = self.db_connection.cursor(dictionary=True)

            # Log de la llamada al stored procedure
            param_str = ', '.join(map(str, params)) if params else 'None'
            logger.info(
                f"Calling stored procedure {proc_name} with params: {param_str}")

            # Ejecutar stored procedure
            if params:
                cursor.callproc(proc_name, params)
            else:
                cursor.callproc(proc_name)

            # Obtener resultados
            results = []
            for result in cursor.stored_results():
                if fetch_all:
                    results.extend(result.fetchall())
                else:
                    row = result.fetchone()
                    if row:
                        results.append(row)

            self.db_connection.commit()

            # Log del resultado
            result_count = len(results)
            logger.info(
                f"Stored procedure {proc_name} returned {result_count} results")

            if fetch_all:
                return results
            else:
                return results[0] if results else None

        except mysql.connector.Error as e:
            self.db_connection.rollback()
            logger.error(f"Database error in {proc_name}: {str(e)}")
            raise DatabaseError(
                f"Error executing stored procedure {proc_name}: {str(e)}")
        except Exception as e:
            self.db_connection.rollback()
            logger.error(f"Unexpected error in {proc_name}: {str(e)}")
            raise DatabaseError(
                f"Unexpected error in stored procedure {proc_name}: {str(e)}")
        finally:
            if cursor:
                cursor.close()
                # Limpiar cualquier result set pendiente
                try:
                    while self.db_connection.next_result():
                        pass
                except Exception as e:
                    logger.warning(f"Error cleaning up result sets: {str(e)}")

    def test_connection(self) -> bool:
        """
        Prueba la conexión a la base de datos

        Returns:
            bool: True si la conexión está activa, False en caso contrario
        """
        try:
            return self.db_connection.is_connected()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def close_connection(self) -> None:
        """Cierra la conexión a la base de datos de forma segura"""
        try:
            if self.db_connection and self.db_connection.is_connected():
                self.db_connection.close()
                logger.info("Database connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
            raise DatabaseError("Error closing database connection") from e


# Función de compatibilidad para código legacy
def execute_procedure(proc_name: str, params: Optional[tuple] = None,
                      db_connection=None, fetch_all: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
    """
    Función wrapper para mantener compatibilidad con código que usa execute_procedure.
    Delega a DatabaseService.call_stored_proc
    """
    if db_connection is None:
        from src.config.database import DatabaseConfig
        db_connection = DatabaseConfig.get_db_connection()

    service = DatabaseService(db_connection)
    return service.call_stored_proc(proc_name, params, fetch_all)
