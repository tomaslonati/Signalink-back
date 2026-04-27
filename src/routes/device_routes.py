from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields
from controllers.device_controller import DeviceController

# Crear blueprint para compatibilidad
device_bp = Blueprint('devices', __name__)

# Crear namespace para Swagger
device_api = Namespace('devices', description='Operaciones de dispositivos')

# Instanciar controlador
device_controller = DeviceController()

# ✅ MODELOS CORREGIDOS para coincidir con tu base de datos
create_device_model = device_api.model('CreateDevice', {
    'user_id': fields.Integer(required=True, description='ID del propietario del dispositivo', example=1),
    'name': fields.String(required=False, description='Nombre del dispositivo', example='Mi Guante'),
    'mac_address': fields.String(required=False, description='Dirección MAC', example='AA:BB:CC:DD:EE:FF'),
    'manufacturer': fields.String(required=False, description='Fabricante', example='Signalink'),
    'model': fields.String(required=False, description='Modelo', example='Glove v1.0'),
    'firmware_version': fields.String(required=False, description='Versión de firmware', example='1.2.3'),
    'ble_enabled': fields.Boolean(required=False, description='BLE habilitado', example=True, default=True)
})

update_device_model = device_api.model('UpdateDevice', {
    'name': fields.String(required=False, description='Nombre del dispositivo', example='Mi Guante Actualizado'),
    'mac_address': fields.String(required=False, description='Dirección MAC', example='AA:BB:CC:DD:EE:FF'),
    'manufacturer': fields.String(required=False, description='Fabricante', example='Signalink'),
    'model': fields.String(required=False, description='Modelo', example='Glove v2.0'),
    'firmware_version': fields.String(required=False, description='Versión de firmware', example='1.3.0'),
    'ble_enabled': fields.Boolean(required=False, description='BLE habilitado', example=True)
})

# ✅ MODELO DE RESPUESTA que coincide con tu base de datos
device_response_model = device_api.model('Device', {
    'id': fields.Integer(description='ID único del dispositivo'),
    'user_id': fields.Integer(description='ID del propietario'),
    'name': fields.String(description='Nombre del dispositivo'),                    # ✅ Correcto
    'mac_address': fields.String(description='Dirección MAC'),                      # ✅ Correcto
    'manufacturer': fields.String(description='Fabricante'),                        # ✅ Correcto
    'model': fields.String(description='Modelo'),                                   # ✅ Correcto
    'firmware_version': fields.String(description='Versión de firmware'),          # ✅ Correcto
    'ble_enabled': fields.Boolean(description='BLE habilitado'),                    # ✅ Correcto
    'last_seen': fields.String(description='Última vez visto'),                    # ✅ Correcto
    'created_at': fields.String(description='Fecha de creación'),                  # ✅ Correcto
    'username': fields.String(description='Username del propietario'),             # ✅ Correcto
    'user_name': fields.String(description='Nombre del propietario'),              # ✅ Correcto
    'user_surname': fields.String(description='Apellido del propietario')          # ✅ Correcto
})

# ✅ MODELO DE RESPUESTA DE LISTA
device_list_response_model = device_api.model('DeviceListResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'devices': fields.List(fields.Nested(device_response_model), description='Lista de dispositivos'),
    'count': fields.Integer(description='Número de dispositivos')
})

success_response_model = device_api.model('SuccessResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'message': fields.String(description='Mensaje de respuesta'),
    'device_id': fields.Integer(description='ID del dispositivo (en creación)')
})

error_model = device_api.model('Error', {
    'error': fields.String(description='Mensaje de error')
})

# ✅ MODELO PARA RESPUESTA SIMPLE CON DEVICE
device_single_response_model = device_api.model('DeviceSingleResponse', {
    'success': fields.Boolean(description='Indica si la operación fue exitosa'),
    'device': fields.Nested(device_response_model, description='Datos del dispositivo')
})

@device_api.route('/')
class DeviceList(Resource):
    @device_api.doc('create_device')
    @device_api.expect(create_device_model)
    @device_api.marshal_with(success_response_model, code=201)
    @device_api.response(400, 'Datos inválidos', error_model)
    def post(self):
        """
        Crear nuevo dispositivo

        Registra un nuevo dispositivo en el sistema.
        """
        return device_controller.create_device()

    @device_api.doc('get_all_devices')
    @device_api.marshal_with(device_list_response_model)  # ✅ Usar modelo de lista
    def get(self):
        """
        Obtener todos los dispositivos

        Retorna la lista de todos los dispositivos del sistema.
        """
        return device_controller.get_all_devices()


@device_api.route('/<int:device_id>')
class Device(Resource):
    @device_api.doc('get_device')
    @device_api.marshal_with(device_single_response_model)  # ✅ Usar modelo de respuesta individual
    @device_api.response(404, 'Dispositivo no encontrado', error_model)
    def get(self, device_id):
        """
        Obtener información de un dispositivo

        Retorna los detalles de un dispositivo específico.
        """
        return device_controller.get_device(device_id)

    @device_api.doc('update_device')
    @device_api.expect(update_device_model)
    @device_api.marshal_with(success_response_model)
    @device_api.response(404, 'Dispositivo no encontrado', error_model)
    @device_api.response(403, 'No autorizado', error_model)
    def put(self, device_id):
        """
        Actualizar dispositivo

        Actualiza la información del dispositivo. Solo el propietario puede realizar esta acción.
        """
        return device_controller.update_device(device_id)

    @device_api.doc('delete_device')
    @device_api.marshal_with(success_response_model)
    @device_api.response(404, 'Dispositivo no encontrado', error_model)
    @device_api.response(403, 'No autorizado', error_model)
    def delete(self, device_id):
        """
        Eliminar dispositivo

        Elimina un dispositivo del sistema. Solo el propietario puede realizar esta acción.
        """
        return device_controller.delete_device(device_id)


@device_api.route('/user/<int:user_id>')
class UserDevices(Resource):
    @device_api.doc('get_devices_by_user')
    @device_api.marshal_with(device_list_response_model)  # ✅ Usar modelo de lista
    def get(self, user_id):
        """
        Obtener dispositivos por usuario

        Retorna todos los dispositivos que pertenecen a un usuario específico.
        """
        return device_controller.get_devices_by_user(user_id)


@device_api.route('/mac/<string:mac_address>')  # ✅ Cambiar parámetro a mac_address
class DeviceByMac(Resource):
    @device_api.doc('get_device_by_mac')
    @device_api.marshal_with(device_single_response_model)  # ✅ Usar modelo de respuesta individual
    @device_api.response(404, 'Dispositivo no encontrado', error_model)
    def get(self, mac_address):  # ✅ Cambiar parámetro
        """
        Obtener dispositivo por MAC

        Busca un dispositivo por su dirección MAC.
        """
        return device_controller.get_device_by_mac(mac_address)  # ✅ Pasar mac_address


@device_api.route('/manufacturer/<string:manufacturer>')  # ✅ Ruta más útil
class DevicesByManufacturer(Resource):
    @device_api.doc('get_devices_by_manufacturer')
    @device_api.marshal_with(device_list_response_model)
    def get(self, manufacturer):
        """
        Obtener dispositivos por fabricante

        Retorna todos los dispositivos de un fabricante específico.
        """
        return device_controller.get_devices_by_manufacturer(manufacturer)