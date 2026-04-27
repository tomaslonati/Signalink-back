import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app

if __name__ == '__main__':
    app, socketio = create_app()  # Desempaquetar tupla
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Signalink API on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    socketio.run(app, debug=debug, host=host, port=port)  # Usar socketio.run()