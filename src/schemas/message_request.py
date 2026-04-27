from flask_restx import Model, fields

message_request = Model('MessageRequest', {
    'text': fields.String(required=True, description='El texto del mensaje'),
    'type': fields.String(required=True, enum=['text', 'audio'], description='Tipo de mensaje')
})

message_update_request = Model('MessageUpdateRequest', {
    'text': fields.String(required=True, description='El nuevo texto del mensaje')
})