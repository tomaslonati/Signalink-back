from config.database import DatabaseConfig
from services.database_service import DatabaseService
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DeviceModel:
    def __init__(self):
        connection = DatabaseConfig.get_connection()
        self.db_service = DatabaseService(connection)

    def create_device(self, user_id, name, mac_address=None, manufacturer=None, 
                     model=None, firmware_version=None, ble_enabled=True):
        """
        Crea un nuevo dispositivo usando los campos reales de la tabla
        """
        try:
            result = self.db_service.call_stored_proc('CreateDevice', 
                (user_id, name, mac_address, manufacturer, model, firmware_version, ble_enabled))
            
            if result and 'device_id' in result:
                return {
                    'success': True,
                    'device_id': result['device_id'],
                    'message': 'Device created successfully'
                }
            return {
                'success': False,
                'error': 'Failed to create device'
            }
        except Exception as e:
            logger.error(f"Error creating device: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_device_by_id(self, device_id):
        """
        Obtiene un dispositivo por su ID
        """
        try:
            return self.db_service.call_stored_proc('GetDeviceById', (device_id,))
        except Exception as e:
            logger.error(f"Error getting device: {e}")
            return None

    def get_devices_by_user(self, user_id):
        """
        Obtiene todos los dispositivos de un usuario
        """
        try:
            return self.db_service.call_stored_proc('GetDevicesByUser', 
                (user_id,), fetch_all=True)
        except Exception as e:
            logger.error(f"Error getting devices by user: {e}")
            return []

    def get_device_by_mac(self, mac_address):
        """
        Obtiene un dispositivo por su dirección MAC
        """
        try:
            return self.db_service.call_stored_proc('GetDeviceByMac', (mac_address,))
        except Exception as e:
            logger.error(f"Error getting device by MAC: {e}")
            return None

    def update_device(self, device_id, user_id, name=None, mac_address=None, 
                     manufacturer=None, model=None, firmware_version=None, 
                     ble_enabled=None, last_seen=None):
        """
        Actualiza un dispositivo (solo el propietario puede hacerlo)
        """
        try:
            result = self.db_service.call_stored_proc('UpdateDevice', 
                (device_id, user_id, name, mac_address, manufacturer, 
                 model, firmware_version, ble_enabled, last_seen))
            
            if result and 'success' in result:
                return {
                    'success': bool(result['success']),
                    'message': 'Device updated successfully'
                }
            return {
                'success': False,
                'error': 'Failed to update device'
            }
        except Exception as e:
            logger.error(f"Error updating device: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_device(self, device_id, user_id):
        """
        Elimina un dispositivo (solo el propietario puede hacerlo)
        """
        try:
            result = self.db_service.call_stored_proc('DeleteDevice', 
                (device_id, user_id))
            
            if result and 'success' in result:
                return {
                    'success': bool(result['success']),
                    'message': 'Device deleted successfully'
                }
            return {
                'success': False,
                'error': 'Failed to delete device'
            }
        except Exception as e:
            logger.error(f"Error deleting device: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_all_devices(self):
        """
        Obtiene todos los dispositivos del sistema
        """
        try:
            return self.db_service.call_stored_proc('GetAllDevices', fetch_all=True)
        except Exception as e:
            logger.error(f"Error getting all devices: {e}")
            return []

    def is_mac_unique(self, mac_address, exclude_device_id=None):
        """
        Verifica si una dirección MAC es única en el sistema
        """
        if not mac_address:
            return True  # Permitir valores nulos
            
        try:
            result = self.db_service.call_stored_proc('CheckMacUnique', 
                (mac_address, exclude_device_id))
            return bool(result.get('is_unique', False)) if result else False
        except Exception as e:
            logger.error(f"Error checking MAC uniqueness: {e}")
            return False

    def update_last_seen(self, device_id):
        """
        Actualiza la última vez que se vio el dispositivo
        """
        try:
            from datetime import datetime
            now = datetime.now()
            
            result = self.db_service.call_stored_proc('UpdateLastSeen', 
                (device_id, now))
            
            return result is not None
        except Exception as e:
            logger.error(f"Error updating last seen: {e}")
            return False

    def get_devices_by_manufacturer(self, manufacturer):
        """
        Obtiene dispositivos por fabricante
        """
        try:
            return self.db_service.call_stored_proc('GetDevicesByManufacturer', 
                (manufacturer,), fetch_all=True)
        except Exception as e:
            logger.error(f"Error getting devices by manufacturer: {e}")
            return []

    def get_devices_by_model(self, model):
        """
        Obtiene dispositivos por modelo
        """
        try:
            return self.db_service.call_stored_proc('GetDevicesByModel', 
                (model,), fetch_all=True)
        except Exception as e:
            logger.error(f"Error getting devices by model: {e}")
            return []
