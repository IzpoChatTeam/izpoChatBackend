from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Importar modelos y configuración
from models import db, User, Room, Message, FileUpload
from config import Config
from uploads import uploads_bp

# Cargar variables de entorno
load_dotenv()

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
jwt = JWTManager(app)
cors = CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:4200", "https://*.render.com"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin"],
        "supports_credentials": True
    }
})

# Configuración SocketIO para producción
socketio = SocketIO(app, 
                   cors_allowed_origins=["http://localhost:4200", "https://*.render.com"],
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# Registrar blueprints
app.register_blueprint(uploads_bp)

# Diccionario para trackear usuarios conectados
connected_users = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

# Rutas de autenticación
@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Username, email y password son requeridos"}), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email ya está en uso"}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username ya está en uso"}), 400
        
        # Crear nuevo usuario
        hashed_password = generate_password_hash(data['password'])
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            full_name=data.get('full_name', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Crear token de acceso
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
        
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email y password son requeridos"}), 400
        
        # Buscar usuario
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({"error": "Credenciales inválidas"}), 401
        
        # Crear token de acceso
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
        
        return jsonify({
            "message": "Login exitoso",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rutas de salas
@app.route('/api/rooms', methods=['GET'])
@jwt_required()
def get_rooms():
    try:
        rooms = Room.query.all()
        return jsonify([{
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "created_at": room.created_at.isoformat(),
            "created_by": room.created_by
        } for room in rooms]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rooms', methods=['POST'])
@jwt_required()
def create_room():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({"error": "Nombre de la sala es requerido"}), 400
        
        room = Room(
            name=data['name'],
            description=data.get('description', ''),
            created_by=user_id
        )
        
        db.session.add(room)
        db.session.commit()
        
        return jsonify({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "created_at": room.created_at.isoformat(),
            "created_by": room.created_by
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required()
def get_room_messages(room_id):
    try:
        # Verificar que la sala existe
        room = Room.query.get(room_id)
        if not room:
            return jsonify({"error": "Sala no encontrada"}), 404
        
        # Obtener mensajes de la sala
        messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.desc()).limit(100).all()
        
        return jsonify([{
            "id": msg.id,
            "content": msg.content,
            "user_id": msg.user_id,
            "username": msg.user.username,
            "room_id": msg.room_id,
            "created_at": msg.created_at.isoformat(),
            "file_url": msg.file_url
        } for msg in reversed(messages)]), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# WebSocket events
@socketio.on('connect')
@jwt_required()
def handle_connect():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user:
            connected_users[request.sid] = {
                'user_id': user_id,
                'username': user.username
            }
            emit('connected', {'message': f'{user.username} se conectó'})
            print(f'Usuario {user.username} conectado')
        
    except Exception as e:
        print(f'Error en conexión: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    try:
        if request.sid in connected_users:
            user_info = connected_users.pop(request.sid)
            emit('disconnected', {'message': f'{user_info["username"]} se desconectó'}, broadcast=True)
            print(f'Usuario {user_info["username"]} desconectado')
        
    except Exception as e:
        print(f'Error en desconexión: {e}')

@socketio.on('join_room')
@jwt_required()
def handle_join_room(data):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        room_id = data.get('room_id')
        
        if not room_id:
            emit('error', {'message': 'room_id es requerido'})
            return
        
        # Verificar que la sala existe
        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        join_room(str(room_id))
        emit('joined_room', {
            'message': f'{user.username} se unió a la sala {room.name}',
            'room_id': room_id,
            'username': user.username
        }, room=str(room_id))
        
        print(f'Usuario {user.username} se unió a la sala {room.name}')
        
    except Exception as e:
        emit('error', {'message': f'Error al unirse a la sala: {str(e)}'})

@socketio.on('leave_room')
@jwt_required()
def handle_leave_room(data):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        room_id = data.get('room_id')
        
        if room_id:
            room = Room.query.get(room_id)
            if room:
                leave_room(str(room_id))
                emit('left_room', {
                    'message': f'{user.username} salió de la sala {room.name}',
                    'room_id': room_id,
                    'username': user.username
                }, room=str(room_id))
        
    except Exception as e:
        emit('error', {'message': f'Error al salir de la sala: {str(e)}'})

@socketio.on('send_message')
@jwt_required()
def handle_send_message(data):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        room_id = data.get('room_id')
        content = data.get('content', '').strip()
        
        if not room_id or not content:
            emit('error', {'message': 'room_id y content son requeridos'})
            return
        
        # Verificar que la sala existe
        room = Room.query.get(room_id)
        if not room:
            emit('error', {'message': 'Sala no encontrada'})
            return
        
        # Crear mensaje en la base de datos
        message = Message(
            content=content,
            user_id=user_id,
            room_id=room_id
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Emitir mensaje a todos en la sala
        message_data = {
            'id': message.id,
            'content': message.content,
            'user_id': message.user_id,
            'username': user.username,
            'room_id': message.room_id,
            'created_at': message.created_at.isoformat()
        }
        
        emit('new_message', message_data, room=str(room_id))
        print(f'Mensaje enviado por {user.username} en sala {room.name}: {content}')
        
    except Exception as e:
        db.session.rollback()
        emit('error', {'message': f'Error al enviar mensaje: {str(e)}'})

# Crear tablas al inicio de la aplicación
with app.app_context():
    db.create_all()
    print("Tablas de base de datos creadas")

if __name__ == '__main__':
    # Para desarrollo local
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))