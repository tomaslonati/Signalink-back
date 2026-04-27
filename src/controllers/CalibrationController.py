from flask import request, jsonify
from services.calibrate_service import calibrateService


class CalibrationController:
    def __init__(self):
        self.calibrate_service = calibrateService()

    def create_calibration(self, device_id, data):
        """
        Crear una nueva calibración para un dispositivo
        """
        try:
            # Validar datos requeridos
            sign_label = data.get('sign_label')
            
            # Datos de coordenadas
            sign_type = data.get('sign_type')
            axis_x = data.get('axis_x')
            axis_y = data.get('axis_y')
            axis_z = data.get('axis_z')
            flex_index = data.get('flex_index')
            flex_ring = data.get('flex_ring')
            flex_pinky = data.get('flex_pinky')
            flex_middle = data.get('flex_middle')
            repetitions = data.get('repetitions', 1)
            notes = data.get('notes')

            if not sign_label or not sign_type or axis_x is None or axis_y is None or axis_z is None or flex_index is None or flex_ring is None or flex_pinky is None or flex_middle is None:
                return {'error': 'All fields are required'}, 400
            
            result = self.calibrate_service.createCalibration(device_id, sign_label, sign_type, axis_x, axis_y, axis_z, flex_index, flex_ring, flex_pinky, flex_middle, repetitions, notes)
            return result
        except Exception as e:
            return {'error': str(e)}, 500


    def get_calibrations_by_id(self, device_id):
        """
        Obtener todas las calibraciones de un dispositivo
        """
        try:
            if not device_id:
                return {'error': 'device_id is required'}, 400
            
            result = self.calibrate_service.getCalibrationByDeviceId(device_id)
            if result:
                return result,200
        except Exception as e:
            return {'error': str(e)}, 500
        

    def update_calibration(self, device_id, data):
        """
        Actualizar una calibración existente
        Nota: Se actualiza la última calibración del dispositivo con el sign_label especificado
        """
        try:
            if not device_id:
                return {'error': 'device_id is required'}, 400
            
            sign_label = data.get('sign_label')
            sign_type = data.get('sign_type')
            axis_x = data.get('axis_x')
            axis_y = data.get('axis_y')
            axis_z = data.get('axis_z')
            flex_index = data.get('flex_index')
            flex_ring = data.get('flex_ring')
            flex_pinky = data.get('flex_pinky')
            flex_middle = data.get('flex_middle')
            repetitions = data.get('repetitions', 1)
            notes = data.get('notes')

            if not sign_label or not sign_type or not axis_x or not axis_y or not axis_z or not flex_index or not flex_ring or not flex_pinky or not flex_middle:
                return {'error': 'All fields are required'}, 400

            
            result = self.calibrate_service.updateCalibration(device_id, sign_label, sign_type, axis_x, axis_y, axis_z, flex_index, flex_ring, flex_pinky, flex_middle, repetitions, notes)
            return result

        except Exception as e:
            return {'error': str(e)}, 500

    def delete_calibration(self, device_id, data):
        """
        Eliminar calibrations de un dispositivo
        """
        try:
            if not device_id:
                return {'error': 'device_id is required to identify the device'}, 400

            sign_label = data.get('sign_label')
            if not sign_label:
                return {'error': 'sign_label is required to identify the calibration to delete'}, 400

            result = self.calibrate_service.deleteCalibration(device_id, sign_label)
            return result
        except Exception as e:
            return {'error': str(e)}, 500