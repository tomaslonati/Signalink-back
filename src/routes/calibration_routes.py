from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from src.controllers.CalibrationController import CalibrationController

# Crear blueprint para compatibilidad
calibration_bp = Blueprint('calibration', __name__)

# Crear namespace para Swagger
calibration_api = Namespace('calibration', description='Operaciones de calibración de dispositivos')

# Instanciar controlador
calibration_controller = CalibrationController()

# Modelos para Swagger
create_calibration_model = calibration_api.model('Createcalibration', {
    'sign_label': fields.String(required=True, description='Etiqueta de la seña calibrada', example='A'),
    'sign_type': fields.String(required=False, description='Tipo de seña', example='Oracion', default='Oracion'),
    'axis_x': fields.Float(required=False, description='Eje X del MPU', example=185.5),
    'axis_y': fields.Float(required=False, description='Eje Y del MPU', example=193.2),
    'axis_z': fields.Float(required=False, description='Eje Z del MPU', example=103.8),
    'flex_index': fields.Float(required=False, description='Sensor flex índice', example=26.464),
    'flex_ring': fields.Float(required=False, description='Sensor flex anular', example=28.678),
    'flex_pinky': fields.Float(required=False, description='Sensor flex meñique', example=16.399),
    'flex_middle': fields.Float(required=False, description='Sensor flex mayor', example=24.410),
    'repetitions': fields.Integer(required=False, description='Número de repeticiones', example=1, default=1),
    'notes': fields.String(required=False, description='Notas adicionales', example='Calibración inicial')
})

update_calibration_model = calibration_api.model('Updatecalibration', {
    'sign_label': fields.String(required=False, description='Etiqueta de la seña calibrada', example='A'),
    'sign_type': fields.String(required=False, description='Tipo de seña', example='Oracion'),
    'axis_x': fields.Float(required=False, description='Eje X del MPU', example=185.5),
    'axis_y': fields.Float(required=False, description='Eje Y del MPU', example=193.2),
    'axis_z': fields.Float(required=False, description='Eje Z del MPU', example=103.8),
    'flex_index': fields.Float(required=False, description='Sensor flex índice', example=26.464),
    'flex_ring': fields.Float(required=False, description='Sensor flex anular', example=28.678),
    'flex_pinky': fields.Float(required=False, description='Sensor flex meñique', example=16.399),
    'flex_middle': fields.Float(required=False, description='Sensor flex mayor', example=24.410),
    'repetitions': fields.Integer(required=False, description='Número de repeticiones', example=1),
    'notes': fields.String(required=False, description='Notas adicionales', example='Calibración actualizada')
})

delete_calibration_model = calibration_api.model('Deletecalibration', {
    'sign_label': fields.String(required=True, description='Etiqueta de la seña calibrada a eliminar', example='A')
})

calibration_response_model = calibration_api.model('calibration', {
    'id': fields.Integer(description='ID de la calibración'),
    'sign_label': fields.String(description='Etiqueta de la seña calibrada', example='A'),
    'sign_type': fields.String(description='Tipo de seña', example='Oracion'),
    'calibration_date': fields.DateTime(description='Fecha de calibración'),
    'axis_x': fields.Float(description='Eje X del MPU', example=185.5),
    'axis_y': fields.Float(description='Eje Y del MPU', example=193.2),
    'axis_z': fields.Float(description='Eje Z del MPU', example=103.8),
    'flex_index': fields.Float(description='Sensor flex índice', example=26.464),
    'flex_ring': fields.Float(description='Sensor flex anular', example=28.678),
    'flex_pinky': fields.Float(description='Sensor flex meñique', example=16.399),
    'flex_middle': fields.Float(description='Sensor flex mayor', example=24.410),
    'repetitions': fields.Integer(description='Número de repeticiones', example=1),
    'notes': fields.String(description='Notas adicionales')
})

success_response_model = calibration_api.model('SuccessResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'message': fields.String(description='Mensaje de respuesta'),
    'device_id': fields.String(description='MAC del dispositivo'),
    'sign_label': fields.String(description='Etiqueta de la seña calibrada'),
    'calibration_id': fields.Integer(description='ID de la calibración creada')
})

error_model = calibration_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})



@calibration_api.route('/<string:device_id>')
class CalibrationResource(Resource):
    @calibration_api.doc('get_calibrations')
    @calibration_api.marshal_list_with(calibration_response_model)
    @calibration_api.response(404, 'Dispositivo no encontrado', error_model)
    def get(self, device_id):
        """
        Obtener calibraciones del dispositivo

        Obtiene todas las calibraciones del dispositivo identificado por su ID.
        """
        
        return calibration_controller.get_calibrations_by_id(device_id)

    @calibration_api.doc('create_calibration')
    @calibration_api.expect(create_calibration_model)
    @calibration_api.marshal_with(success_response_model, code=201)
    @calibration_api.response(400, 'Datos inválidos', error_model)
    def post(self, device_id):
        """
        Crear nueva calibración

        Registra una nueva calibración para el dispositivo.
        """
        data = request.json
        
        if not data:
            calibration_api.abort(400, 'No se proporcionaron datos')
        
        return calibration_controller.create_calibration(device_id, data)
        

    @calibration_api.doc('update_calibration')
    @calibration_api.expect(update_calibration_model)
    @calibration_api.marshal_with(success_response_model)
    @calibration_api.response(404, 'Calibración no encontrada', error_model)
    @calibration_api.response(400, 'Datos inválidos', error_model)
    def put(self, device_id):
        """
        Actualizar calibración

        Actualiza la calibración de un dispositivo existente.
        """
        data = request.json

        
        return calibration_controller.update_calibration(device_id, data)
    
    @calibration_api.doc('delete_calibration')
    @calibration_api.expect(delete_calibration_model)
    @calibration_api.marshal_with(success_response_model)
    @calibration_api.response(404, 'Calibración no encontrada', error_model)
    @calibration_api.response(400, 'Datos inválidos', error_model)
    def delete(self, device_id):
        """
        Eliminar calibración

        Elimina la calibración de un dispositivo existente.
        """
        data = request.json
        if not data:
            calibration_api.abort(400, 'No se proporcionaron datos')
        
        return calibration_controller.delete_calibration(device_id, data)