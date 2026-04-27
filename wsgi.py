import sys
import os

project_root = os.path.dirname(__file__)
src_path = os.path.join(project_root, 'src')

sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.app import create_app

app, socketio = create_app()

application = app