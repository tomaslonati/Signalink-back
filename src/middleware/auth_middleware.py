from flask import request, jsonify
from functools import wraps
from src.services.auth_service import AuthService
import asyncio
from asgiref.sync import async_to_sync

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # En modo debug, usar un usuario fijo
        debug_mode = False  # Modo producción activado
        
        if debug_mode:
            print("🔒 Debug mode: bypassing token check")
            current_user = {
                'user_id': 10,  # ID de FacuConde
                'user_name': 'Facundo'
            }
            print(f"👤 Using debug user: {current_user}")
        else:
            # Modo normal con validación de token
            token = request.headers.get('Authorization')
            if not token:
                print("❌ No token found in headers")
                return {'message': 'Token is missing!'}, 401

            # Limpiar el token de cualquier prefijo o espacio
            token = token.strip()
            if token.lower().startswith('bearer'):
                token = token[6:].strip()  # Remover 'bearer' y espacios

            print(f"🔑 Processing token: {token[:20]}...")
            
            print(f"🔍 Processing token: {token[:20]}...")
            auth_service = AuthService()
            payload = auth_service.decode_token(token)
            
            if not payload:
                print("❌ Invalid token!")
                return {'message': 'Invalid token!'}, 401
                
            current_user = {
                'user_id': payload.get('user_id'),
                'user_name': payload.get('user_name')
            }
            print(f"👤 Current user: {current_user}")
        
        # Si la función es async, convertirla a sync
        if asyncio.iscoroutinefunction(f):
            print("⚡ Running async function")
            sync_f = async_to_sync(f)
            return sync_f(current_user=current_user, *args, **kwargs)
        
        # Si es una función normal
        print("🔄 Running sync function")
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated