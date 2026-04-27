from flask import request, jsonify
from models.device_model import DeviceModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DeviceController:
    def __init__(self):
        self.device_model = DeviceModel()

    def _serialize_device(self, device):
        """Convertir un device de la DB al formato esperado por Swagger"""
        if not device:
            return None
            
        return {
            'id': device.get('id'),
            'user_id': device.get('user_id'),
            'name': device.get('name'),
            'mac_address': device.get('mac_address'),
            'manufacturer': device.get('manufacturer'),
            'model': device.get('model'),
            'firmware_version': device.get('firmware_version'),
            'ble_enabled': bool(device.get('ble_enabled', 0)),  # ✅ Convertir a boolean
            'last_seen': device.get('last_seen').isoformat() if device.get('last_seen') else None,  # ✅ Convertir datetime
            'created_at': device.get('created_at').isoformat() if device.get('created_at') else None,  # ✅ Convertir datetime
            'username': device.get('username'),
            'user_name': device.get('user_name'),
            'user_surname': device.get('user_surname')
        }

    def _serialize_devices(self, devices):
        """Convertir lista de devices"""
        return [self._serialize_device(device) for device in devices if device]

    def get_all_devices(self):
        """Obtener todos los dispositivos"""
        try:
            devices = self.device_model.get_all_devices()
            
            # ✅ Serializar los datos antes de devolverlos
            serialized_devices = self._serialize_devices(devices)
            
            return {
                'success': True,
                'devices': serialized_devices,
                'count': len(serialized_devices)
            }
            
        except Exception as e:
            logger.error(f"Error in get_all_devices: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def get_devices_by_user(self, user_id):
        """Obtener dispositivos por usuario"""
        try:
            devices = self.device_model.get_devices_by_user(user_id)
            
            # ✅ Serializar los datos
            serialized_devices = self._serialize_devices(devices)
            
            return {
                'success': True,
                'devices': serialized_devices,
                'count': len(serialized_devices)
            }
            
        except Exception as e:
            logger.error(f"Error in get_devices_by_user: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def get_device(self, device_id):
        """Obtener dispositivo por ID"""
        try:
            device = self.device_model.get_device_by_id(device_id)
            
            if device:
                # ✅ Serializar el dispositivo
                serialized_device = self._serialize_device(device)
                return {
                    'success': True,
                    'device': serialized_device
                }
            else:
                from flask_restx import abort
                abort(404, message='Device not found')
                
        except Exception as e:
            logger.error(f"Error in get_device: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def get_device_by_mac(self, mac_address):
        """Obtener dispositivo por MAC"""
        try:
            device = self.device_model.get_device_by_mac(mac_address)
            
            if device:
                serialized_device = self._serialize_device(device)
                return {
                    'success': True,
                    'device': serialized_device
                }
            else:
                from flask_restx import abort
                abort(404, message='Device not found')
                
        except Exception as e:
            logger.error(f"Error in get_device_by_mac: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def create_device(self):
        """Crear dispositivo"""
        try:
            data = request.get_json()
            
            if not data.get('user_id'):
                from flask_restx import abort
                abort(400, message='user_id is required')
            
            result = self.device_model.create_device(
                user_id=data['user_id'],
                name=data.get('name', 'Unnamed Device'),
                mac_address=data.get('mac_address'),
                manufacturer=data.get('manufacturer'),
                model=data.get('model'),
                firmware_version=data.get('firmware_version'),
                ble_enabled=data.get('ble_enabled', True)
            )
            
            if result['success']:
                return result
            else:
                from flask_restx import abort
                abort(400, message=result.get('error', 'Failed to create device'))
                
        except Exception as e:
            logger.error(f"Error in create_device: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def update_device(self, device_id):
        """Actualizar dispositivo"""
        try:
            data = request.get_json()
            
            if not data.get('user_id'):
                from flask_restx import abort
                abort(400, message='user_id is required')
            
            result = self.device_model.update_device(
                device_id=device_id,
                user_id=data['user_id'],
                name=data.get('name'),
                mac_address=data.get('mac_address'),
                manufacturer=data.get('manufacturer'),
                model=data.get('model'),
                firmware_version=data.get('firmware_version'),
                ble_enabled=data.get('ble_enabled'),
                last_seen=data.get('last_seen')
            )
            
            if result['success']:
                return result
            else:
                from flask_restx import abort
                abort(400, message=result.get('error', 'Failed to update device'))
                
        except Exception as e:
            logger.error(f"Error in update_device: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')

    def delete_device(self, device_id):
        """Eliminar dispositivo"""
        try:
            data = request.get_json()
            
            if not data.get('user_id'):
                from flask_restx import abort
                abort(400, message='user_id is required')
            
            result = self.device_model.delete_device(device_id, data['user_id'])
            
            if result['success']:
                return result
            else:
                from flask_restx import abort
                abort(400, message=result.get('error', 'Failed to delete device'))
                
        except Exception as e:
            logger.error(f"Error in delete_device: {e}")
            from flask_restx import abort
            abort(500, message='Internal server error')
