# extension.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
# Async_mode 'eventlet' es crucial para el rendimiento en producción con Gunicorn
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
jwt = JWTManager()