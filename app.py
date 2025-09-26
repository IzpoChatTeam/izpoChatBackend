# app.py
import eventlet
eventlet.monkey_patch()

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from sqlalchemy import or_, desc

# --- Importaciones correctas de flask_jwt_extended ---
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, decode_token

# --- Configuración Inicial ---
from config import Config
from extension import db, socketio, jwt
from models import User, Room, Message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Lógica de la Aplicación ---
connected_users = {} # Almacena {session_id: user_id}

def create_app(config_class=Config):
    """Factory para crear la instancia de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    # --- Inicialización de Extensiones ---
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)

    # --- Registro de Endpoints y Eventos ---
    with app.app_context():
        register_endpoints(app)
        register_socketio_events(socketio)
        
        try:
            db.create_all()
            logging.info("✅ Tablas de la base de datos verificadas/creadas.")
        except Exception as e:
            logging.error(f"❌ Error al crear las tablas: {e}")
            
    return app

def register_endpoints(app):
    """Registra todas las rutas HTTP de la API."""

    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({"status": "healthy", "database": "connected"}), 200
        except Exception as e:
            return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500

    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        if User.query.filter(or_(User.username == data.get('username'), User.email == data.get('email'))).first():
            return jsonify({"error": "El usuario o email ya existe"}), 409
        
        hashed_password = generate_password_hash(data.get('password'))
        new_user = User(username=data.get('username'), email=data.get('email'), password_hash=hashed_password, full_name=data.get('full_name', ''))
        db.session.add(new_user)
        db.session.commit()

        # --- CAMBIO AQUÍ: Usar create_access_token() directamente ---
        access_token = create_access_token(identity=new_user.id, expires_delta=timedelta(days=7))
        return jsonify(access_token=access_token, user_id=new_user.id), 201

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()

        if user and check_password_hash(user.password_hash, data.get('password')):
            # --- CAMBIO AQUÍ: Usar create_access_token() directamente ---
            access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=7))
            return jsonify(access_token=access_token, user_id=user.id), 200
        return jsonify({"error": "Credenciales inválidas"}), 401

    @app.route('/api/users/me', methods=['GET'])
    @jwt_required()
    def get_me():
        # --- CAMBIO AQUÍ: Usar get_jwt_identity() directamente ---
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return jsonify({"id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name})

    @app.route('/api/users/search', methods=['GET'])
    @jwt_required()
    def search_users():
        query = request.args.get('query', '').strip()
        # --- CAMBIO AQUÍ: Usar get_jwt_identity() directamente ---
        current_user_id = get_jwt_identity()
        if not query:
            return jsonify([]), 200
        
        users = User.query.filter(User.username.ilike(f'%{query}%'), User.id != current_user_id).limit(10).all()
        return jsonify([{"id": user.id, "username": user.username, "full_name": user.full_name} for user in users])

    @app.route('/api/conversations/initiate', methods=['POST'])
    @jwt_required()
    def create_or_get_conversation():
        # --- CAMBIO AQUÍ: Usar get_jwt_identity() directamente ---
        current_user_id = get_jwt_identity()
        recipient_id = request.json.get('recipient_id')

        if not recipient_id:
            return jsonify({"error": "recipient_id es requerido"}), 400
        
        conversation = Room.find_private_conversation(current_user_id, recipient_id)
        if conversation:
            return jsonify({"room_id": conversation.id, "status": "existing"}), 200

        user1 = User.query.get(current_user_id)
        user2 = User.query.get(recipient_id)
        if not user2:
            return jsonify({"error": "Usuario destinatario no encontrado"}), 404

        new_conversation = Room(name=f"Chat entre {user1.username} y {user2.username}")
        new_conversation.members.append(user1)
        new_conversation.members.append(user2)
        db.session.add(new_conversation)
        db.session.commit()
        return jsonify({"room_id": new_conversation.id, "status": "created"}), 201
    
    @app.route('/api/conversations', methods=['GET'])
    @jwt_required()
    def get_user_conversations():
        # --- CAMBIO AQUÍ: Usar get_jwt_identity() directamente ---
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        conversations_data = []
        for room in user.conversations:
            other_member = next((member for member in room.members if member.id != current_user_id), None)
            if not other_member:
                continue

            last_message = Message.query.filter_by(room_id=room.id).order_by(desc(Message.created_at)).first()
            
            conversations_data.append({
                "room_id": room.id,
                "other_user": {"id": other_member.id, "username": other_member.username, "full_name": other_member.full_name},
                "last_message": {"content": last_message.content if last_message else "No hay mensajes todavía.", "created_at": last_message.created_at.isoformat() if last_message else None}
            })
        
        conversations_data.sort(key=lambda x: x['last_message']['created_at'] or '1970-01-01T00:00:00', reverse=True)
        return jsonify(conversations_data), 200

    @app.route('/api/conversations/<int:room_id>/messages', methods=['GET'])
    @jwt_required()
    def get_messages(room_id):
        messages = Message.query.filter_by(room_id=room_id).order_by(Message.created_at.asc()).all()
        return jsonify([{"id": msg.id, "content": msg.content, "user_id": msg.user_id, "username": msg.user.username, "created_at": msg.created_at.isoformat()} for msg in messages])

def register_socketio_events(socketio):
    """Registra todos los manejadores de eventos de WebSocket."""

    @socketio.on('connect')
    def handle_connect(auth):
        token = auth.get('token') if auth else None
        if not token:
            return False
        try:
            # --- CAMBIO AQUÍ: Usar decode_token() directamente ---
            decoded_token = decode_token(token)
            user_id = decoded_token['sub']
            connected_users[request.sid] = user_id
            logging.info(f"Usuario {user_id} conectado a WebSocket con SID {request.sid}")
        except Exception as e:
            logging.error(f"Error de autenticación en WebSocket: {e}")
            return False

    # ... resto de la lógica de websockets sin cambios ...
    @socketio.on('disconnect')
    def handle_disconnect():
        if request.sid in connected_users:
            user_id = connected_users.pop(request.sid)
            logging.info(f"Usuario {user_id} desconectado de WebSocket con SID {request.sid}")

    @socketio.on('join_room')
    def handle_join_room(data):
        room_id = str(data.get('room_id'))
        if request.sid in connected_users:
            socketio.join_room(room_id, sid=request.sid)
            logging.info(f"Usuario {connected_users[request.sid]} se unió a la sala {room_id}")

    @socketio.on('send_message')
    def handle_send_message(data):
        user_id = connected_users.get(request.sid)
        if not user_id:
            return
        
        room_id = data.get('room_id')
        content = data.get('content')
        if not all([room_id, content]):
            return

        message = Message(content=content, user_id=user_id, room_id=room_id)
        db.session.add(message)
        db.session.commit()
        
        user = User.query.get(user_id)
        message_data = {
            "id": message.id, "content": content, "user_id": user_id,
            "username": user.username, "room_id": room_id, "created_at": message.created_at.isoformat()
        }
        socketio.emit('new_message', message_data, to=str(room_id))
        logging.info(f"Mensaje enviado por {user_id} a la sala {room_id}")

# --- Punto de Entrada para Ejecución ---
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)