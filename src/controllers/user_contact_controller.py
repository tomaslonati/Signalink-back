from flask import request, jsonify
from models.user_contact_model import UserContactModel
from utils.serializers import serialize_list, serialize_dict


class UserContactController:
    def __init__(self):
        self.user_contact_model = UserContactModel()

    def add_contact(self):
        """
        Añadir un contacto
        """
        try:
            data = request.get_json()

            if not data:
                return {'error': 'No data provided'}, 400

            user_id = data.get('user_id')
            contact_id = data.get('contact_id')

            if not user_id or not contact_id:
                return {'error': 'user_id and contact_id are required'}, 400

            result = self.user_contact_model.add_contact(user_id, contact_id)

            if result['success']:
                return result, 201
            else:
                return {'error': result['error']}, 400

        except Exception as e:
            return {'error': str(e)}, 500

    def remove_contact(self, user_id, contact_id):
        """
        Eliminar un contacto
        """
        try:
            result = self.user_contact_model.remove_contact(
                user_id, contact_id)

            if result['success']:
                return result, 200
            else:
                return {'error': result['error']}, 404

        except Exception as e:
            return {'error': str(e)}, 500

    def get_user_contacts(self, user_id):
        """
        Obtener todos los contactos de un usuario
        """
        try:
            contacts = self.user_contact_model.get_user_contacts(user_id)
            return serialize_list(contacts), 200

        except Exception as e:
            return {'error': str(e)}, 500

    def get_users_who_have_contact(self, contact_id):
        """
        Obtener usuarios que tienen a este usuario como contacto
        """
        try:
            users = self.user_contact_model.get_users_who_have_contact(
                contact_id)
            return serialize_list(users), 200

        except Exception as e:
            return {'error': str(e)}, 500

    def check_contact_status(self, user_id, contact_id):
        """
        Verificar estado de contacto entre dos usuarios
        """
        try:
            is_contact = self.user_contact_model.is_contact(
                user_id, contact_id)
            is_mutual = self.user_contact_model.are_mutual_contacts(
                user_id, contact_id)

            return {
                'is_contact': is_contact,
                'is_mutual': is_mutual
            }, 200

        except Exception as e:
            return {'error': str(e)}, 500

    def get_mutual_contacts(self, user_id):
        """
        Obtener contactos mutuos de un usuario
        """
        try:
            contacts = self.user_contact_model.get_mutual_contacts(user_id)
            return serialize_list(contacts), 200

        except Exception as e:
            return {'error': str(e)}, 500

    def get_contact_count(self, user_id):
        """
        Obtener número total de contactos
        """
        try:
            count = self.user_contact_model.get_contact_count(user_id)
            return {'count': count}, 200

        except Exception as e:
            return {'error': str(e)}, 500

    def search_contacts(self, user_id):
        """
        Buscar contactos de un usuario
        """
        try:
            search_term = request.args.get('q', '')

            if not search_term:
                return {'error': 'Search term (q parameter) is required'}, 400

            contacts = self.user_contact_model.search_contacts(
                user_id, search_term)
            return serialize_list(contacts), 200

        except Exception as e:
            return {'error': str(e)}, 500
