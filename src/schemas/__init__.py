from marshmallow import Schema, fields, validate

class LoginRequestSchema(Schema):
    """Schema para la request de login"""
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50), 
                          description="Username o email del usuario")
    password = fields.Str(required=True, validate=validate.Length(min=6), 
                          description="Contraseña del usuario")

class LoginResponseSchema(Schema):
    """Schema para la response de login exitoso"""
    success = fields.Bool(description="Indica si el login fue exitoso")
    message = fields.Str(description="Mensaje de respuesta")
    user = fields.Nested('UserSchema', description="Datos del usuario")

class RegisterRequestSchema(Schema):
    """Schema para la request de registro"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=30), 
                      description="Nombre del usuario")
    surname = fields.Str(required=True, validate=validate.Length(min=2, max=30), 
                         description="Apellido del usuario")
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50), 
                          description="Nombre de usuario único")
    email = fields.Email(required=True, description="Email del usuario")
    password = fields.Str(required=True, validate=validate.Length(min=6), 
                          description="Contraseña del usuario")

class RegisterResponseSchema(Schema):
    """Schema para la response de registro exitoso"""
    success = fields.Bool(description="Indica si el registro fue exitoso")
    message = fields.Str(description="Mensaje de respuesta")
    user_id = fields.Int(description="ID del usuario creado")

class UserSchema(Schema):
    """Schema para los datos del usuario"""
    id = fields.Int(description="ID único del usuario")
    name = fields.Str(description="Nombre del usuario")

class ErrorResponseSchema(Schema):
    """Schema para respuestas de error"""
    error = fields.Str(description="Mensaje de error")

class HealthResponseSchema(Schema):
    """Schema para el health check"""
    status = fields.Str(description="Estado del servicio")
    database = fields.Str(description="Estado de la base de datos", missing=None)
    module = fields.Str(description="Módulo específico", missing=None)
    timestamp = fields.Str(description="Timestamp del check", missing=None)