import eventlet
eventlet.monkey_patch()

import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from config import Config
from extension import db, socketio, jwt

from dotenv import load_dotenv
import jwt as pyjwt
from datetime import timedelta
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    logging.info("🚀 Iniciando IzpoChat Backend")

    CORS(app, resources={r"/*": {"origins": "*"}})
    logging.info("✅ CORS configurado para todos los orígenes")

    # --- CAMBIO: Inicializar extensiones con el método init_app ---
    db.init_app(app)
    logging.info("✅ SQLAlchemy inicializado")

    jwt.init_app(app)
    logging.info("✅ JWT Manager inicializado")

    # La configuración de SocketIO se pasa aquí
    socketio.init_app(app, 
                      cors_allowed_origins="*",
                      async_mode='eventlet',
                      logger=True,
                      engineio_logger=False)
    logging.info("✅ SocketIO configurado con eventlet")

    # --- CAMBIO: Importar y registrar blueprints DENTRO de la función ---
    with app.app_context():
        from uploads import uploads_bp
        app.register_blueprint(uploads_bp)
        logging.info("✅ Blueprint de uploads registrado")

        # Crear tablas
        try:
            db.create_all()
            logging.info("✅ Tablas de base de datos creadas/verificadas")
        except Exception as e:
            logging.error(f"❌ Error creando tablas: {e}")

    # Configurar rutas y WebSocket events
    # NOTA: Debes pasar la instancia 'jwt' si tus rutas la necesitan.
    setup_routes(app) 
    setup_websocket_events(socketio, app)

    logging.info("✅ IzpoChat Backend listo")
    return app, socketio

connected_users = {}

# Función auxiliar para verificar token JWT en WebSocket
# Diccionario para trackear usuarios conectados
connected_users = {}

def verify_jwt_token(token):
    """Función auxiliar para verificar token JWT en WebSocket"""
    try:
        if not token:
            return None
        
        # Remover 'Bearer ' si está presente
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Obtener la clave secreta desde las variables de entorno
        secret_key = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
        
        # Decodificar el token
        decoded = pyjwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = decoded.get('sub')  # 'sub' es el campo estándar para user_id en JWT
        
        if user_id:
            from models import User
            user = User.query.get(user_id)
            return user
        
    except pyjwt.ExpiredSignatureError:
        logging.warning("Token JWT expirado")
    except pyjwt.InvalidTokenError as e:
        logging.warning(f"Token JWT inválido: {e}")
    except Exception as e:
        logging.error(f"Error verificando token JWT: {e}")
    
    return None

def setup_routes(app):
    """Configurar todas las rutas HTTP"""
    from models import db, User, Room, Message, FileUpload
    
    # Rutas públicas (sin autenticación requerida)
    @app.route('/')
    def home():
        """Ruta principal para Render"""
        port = os.environ.get('PORT', '5000')
        return {
            "message": "💬 IzpoChat Backend API",
            "version": "2.0 - Optimizado para Render",
            "status": "✅ RUNNING",
            "port": port,
            "render_ready": True,
            "endpoints": {
                "register": "POST /api/users/register",
                "login": "POST /api/users/login", 
                "rooms": "GET /api/rooms",
                "health": "GET /health",
                "status": "GET /api/status",
                "websocket_info": "GET /api/websocket-info",
                "debug_connections": "GET /api/debug-connections",
                "websocket": "WebSocket connection available"
            }
        }

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check para Render con diagnóstico mejorado"""
        try:
            # Test database connection con timeout
            import sqlalchemy
            from sqlalchemy import text
            
            start_time = datetime.utcnow()
            result = db.session.execute(text('SELECT 1'))
            end_time = datetime.utcnow()
            
            query_time = (end_time - start_time).total_seconds() * 1000  # en ms
            
            db_status = "✅ connected"
            db_info = {
                "status": "connected",
                "query_time_ms": round(query_time, 2),
                "engine": str(db.engine.url).split('@')[1] if '@' in str(db.engine.url) else "unknown"
            }
            
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            db_status = "⚠️ disconnected"
            db_info = {
                "status": "disconnected", 
                "error": str(e),
                "database_url": os.environ.get('DATABASE_URL', 'not_set')[:50] + "..." if os.environ.get('DATABASE_URL') else 'not_set'
            }
        
        return jsonify({
            "status": "healthy" if db_status == "✅ connected" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "database_info": db_info,
            "service": "izpochat-backend"
        })

    @app.route('/api/status', methods=['GET'])
    def api_status():
        return jsonify({
            "status": "running",
            "version": "2.0.0",
            "cors_enabled": True,
            "websocket_enabled": True,
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route('/api/websocket-info', methods=['GET'])
    def websocket_info():
        """Endpoint para obtener información del WebSocket para debugging"""
        
        # Detectar el dominio y protocolo actual
        host = request.host
        is_https = request.is_secure or 'render.com' in host
        
        # Construir URLs del WebSocket
        ws_protocol = 'wss' if is_https else 'ws'
        websocket_url = f"{ws_protocol}://{host}"
        
        # Información del entorno
        environment_info = {
            "render_deployment": bool(os.environ.get('RENDER')),
            "port": os.environ.get('PORT', 'not_set'),
            "host": host,
            "is_https": is_https,
            "user_agent": request.headers.get('User-Agent', 'unknown')
        }
        
        # Estado de usuarios conectados
        connected_count = len(connected_users) if 'connected_users' in globals() else 0
        
        return jsonify({
            "websocket": {
                "url": websocket_url,
                "protocol": ws_protocol,
                "cors_origins": "*",
                "async_mode": "eventlet",
                "status": "enabled" if socketio else "disabled"
            },
            "connection": {
                "host": host,
                "is_secure": is_https,
                "connected_users": connected_count
            },
            "environment": environment_info,
            "authentication": {
                "method": "JWT token required",
                "token_locations": ["auth.token", "query.token"],
                "example_connection": {
                    "javascript": f"io('{websocket_url}', {{ auth: {{ token: 'your-jwt-token' }} }})",
                    "query_param": f"io('{websocket_url}?token=your-jwt-token')"
                }
            },
            "events": {
                "client_events": ["connect", "join_room", "leave_room", "send_message"],
                "server_events": ["connected", "disconnected", "joined_room", "left_room", "new_message", "error"]
            },
            "debugging": {
                "health_endpoint": f"{'https' if is_https else 'http'}://{host}/health",
                "status_endpoint": f"{'https' if is_https else 'http'}://{host}/api/status",
                "websocket_endpoint": f"{'https' if is_https else 'http'}://{host}/api/websocket-info"
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route('/api/debug-connections', methods=['GET'])
    def debug_connections():
        """Endpoint para debugging de conexiones WebSocket"""
        
        # Estado de usuarios conectados
        connected_count = len(connected_users) if 'connected_users' in globals() else 0
        
        # Información detallada de usuarios conectados
        users_info = []
        if 'connected_users' in globals():
            for sid, user_info in connected_users.items():
                users_info.append({
                    "session_id": sid[:10] + "...",  # Solo mostrar parte del SID por seguridad
                    "user_id": user_info.get('user_id'),
                    "username": user_info.get('username')
                })
        
        return jsonify({
            "websocket_status": {
                "connected_users_count": connected_count,
                "connected_users": users_info,
                "socketio_enabled": socketio is not None
            },
            "database_status": {
                "users_table": User.query.count() if 'User' in globals() else "unknown",
                "rooms_table": Room.query.count() if 'Room' in globals() else "unknown", 
                "messages_table": Message.query.count() if 'Message' in globals() else "unknown"
            },
            "debugging_info": {
                "note": "This endpoint helps debug WebSocket connection issues",
                "check_logs": "Look at server logs for 'Usuario X se unió a la sala Y' messages",
                "verify_frontend": "Ensure frontend is calling socket.emit('join_room', {room_id: X})",
                "message_flow": [
                    "1. Frontend: socket.emit('send_message', {room_id: X, content: 'text'})",
                    "2. Backend: Saves message to database", 
                    "3. Backend: socketio.emit('new_message', data, room=str(room_id))",
                    "4. Frontend: socket.on('new_message', callback) should receive it"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    # Manejar solicitudes OPTIONS para CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,Accept,Origin,X-Requested-With")
            response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS,HEAD,PATCH")
            return response

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
            
            logging.info(f"Usuario registrado: {user.username}")
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
            logging.error(f"Error en registro: {e}")
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
            
            logging.info(f"Usuario logueado: {user.username}")
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
            logging.error(f"Error en login: {e}")
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
            logging.error(f"Error obteniendo usuario: {e}")
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
            logging.error(f"Error obteniendo salas: {e}")
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
            
            logging.info(f"Sala creada: {room.name} por usuario {user_id}")
            return jsonify({
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "created_at": room.created_at.isoformat(),
                "created_by": room.created_by
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creando sala: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/conversations', methods=['POST'])
    @jwt_required()
    def create_or_get_private_conversation():
        """Crear o encontrar una conversación privada entre dos usuarios"""
        try:
            current_user_id = get_jwt_identity()
            data = request.get_json()
            
            recipient_id = data.get('recipient_id')
            if not recipient_id:
                return jsonify({"error": "recipient_id es requerido"}), 400
            
            if recipient_id == current_user_id:
                return jsonify({"error": "No puedes crear una conversación contigo mismo"}), 400
            
            # Verificar que el destinatario existe
            recipient = User.query.get(recipient_id)
            if not recipient:
                return jsonify({"error": "Usuario destinatario no encontrado"}), 404
            
            current_user = User.query.get(current_user_id)
            
            # Buscar si ya existe una conversación privada entre estos dos usuarios
            existing_room = Room.find_private_conversation(current_user_id, recipient_id)
            
            if existing_room:
                # Retornar la conversación existente
                return jsonify({
                    "id": existing_room.id,
                    "name": existing_room.name,
                    "description": existing_room.description,
                    "is_private": existing_room.is_private,
                    "created_at": existing_room.created_at.isoformat(),
                    "created_by": existing_room.created_by,
                    "members": [{
                        "id": member.id,
                        "username": member.username,
                        "full_name": member.full_name
                    } for member in existing_room.members],
                    "status": "existing_conversation"
                }), 200
            
            # Crear nueva conversación privada
            conversation_name = f"Conversación entre {current_user.username} y {recipient.username}"
            
            new_room = Room(
                name=conversation_name,
                description=f"Conversación privada entre {current_user.full_name or current_user.username} y {recipient.full_name or recipient.username}",
                is_private=True,
                created_by=current_user_id
            )
            
            # Agregar ambos usuarios como miembros
            new_room.members.append(current_user)
            new_room.members.append(recipient)
            
            db.session.add(new_room)
            db.session.commit()
            
            logging.info(f"Conversación privada creada entre {current_user.username} y {recipient.username}")
            
            return jsonify({
                "id": new_room.id,
                "name": new_room.name,
                "description": new_room.description,
                "is_private": new_room.is_private,
                "created_at": new_room.created_at.isoformat(),
                "created_by": new_room.created_by,
                "members": [{
                    "id": member.id,
                    "username": member.username,
                    "full_name": member.full_name
                } for member in new_room.members],
                "status": "new_conversation"
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creando conversación: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/debug/test-supabase', methods=['GET'])
    def test_supabase_connection():
        """Endpoint para probar la conexión con Supabase Storage"""
        try:
            import httpx
            
            # Obtener configuraciones de Supabase
            supabase_url = app.config.get('SUPABASE_URL')
            supabase_key = app.config.get('SUPABASE_ANON_KEY')
            bucket_name = app.config.get('SUPABASE_STORAGE_BUCKET')
            
            if not all([supabase_url, supabase_key, bucket_name]):
                return jsonify({
                    "status": "error",
                    "message": "Configuración de Supabase incompleta",
                    "missing_configs": {
                        "SUPABASE_URL": bool(supabase_url),
                        "SUPABASE_ANON_KEY": bool(supabase_key),
                        "SUPABASE_STORAGE_BUCKET": bool(bucket_name)
                    }
                }), 500
            
            # URL para listar objetos del bucket
            storage_url = f"{supabase_url}/storage/v1/object/{bucket_name}"
            
            headers = {
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Realizar petición síncrona con httpx
            with httpx.Client(timeout=30.0) as client:
                response = client.get(storage_url, headers=headers)
                
                success = response.status_code in [200, 201]
                
                return jsonify({
                    "status": "success" if success else "error",
                    "connection": {
                        "supabase_url": supabase_url,
                        "bucket_name": bucket_name,
                        "storage_endpoint": storage_url
                    },
                    "response": {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "content_length": len(response.content),
                        "response_preview": response.text[:500] if response.text else "No content"
                    },
                    "test_result": {
                        "can_connect": success,
                        "bucket_accessible": success,
                        "error_message": None if success else f"HTTP {response.status_code}: {response.text}"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }), 200 if success else 500
                
        except ImportError:
            return jsonify({
                "status": "error",
                "message": "httpx library not available",
                "install_command": "pip install httpx"
            }), 500
            
        except Exception as e:
            logging.error(f"Error testing Supabase connection: {e}")
            return jsonify({
                "status": "error",
                "message": f"Connection test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }), 500

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
            logging.error(f"Error obteniendo mensajes: {e}")
            return jsonify({"error": str(e)}), 500

def setup_websocket_events(socketio, app):
    """Configurar todos los eventos WebSocket"""
    from models import db, User, Room, Message
    
    # WebSocket events con autenticación manual
    @socketio.on('connect')
    def handle_connect(auth):
        try:
            # Obtener token de los datos de autenticación
            token = None
            if auth and isinstance(auth, dict):
                token = auth.get('token')
            
            # Si no hay token en auth, intentar obtenerlo de la query string
            if not token:
                token = request.args.get('token')
            
            user = verify_jwt_token(token)
            if not user:
                emit('error', {'message': 'Token de autenticación requerido o inválido'})
                return False
            
            connected_users[request.sid] = {
                'user_id': user.id,
                'username': user.username
            }
            
            emit('connected', {
                'message': f'{user.username} se conectó',
                'user_id': user.id,
                'username': user.username
            })
            logging.info(f'Usuario {user.username} conectado via WebSocket')
            
        except Exception as e:
            logging.error(f'Error en conexión WebSocket: {e}')
            emit('error', {'message': f'Error de conexión: {str(e)}'})
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        try:
            if request.sid in connected_users:
                user_info = connected_users.pop(request.sid)
                emit('disconnected', {'message': f'{user_info["username"]} se desconectó'}, broadcast=True)
                logging.info(f'Usuario {user_info["username"]} desconectado')
            
        except Exception as e:
            logging.error(f'Error en desconexión: {e}')

    @socketio.on('join_room')
    def handle_join_room(data):
        try:
            # Verificar que el usuario esté autenticado
            if request.sid not in connected_users:
                emit('error', {'message': 'Usuario no autenticado'})
                return
            
            user_info = connected_users[request.sid]
            user = User.query.get(user_info['user_id'])
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
            
            logging.info(f'Usuario {user.username} se unió a la sala {room.name} (room_id={room_id})')
            logging.info(f'Usuarios conectados en total: {len(connected_users)}')
            
        except Exception as e:
            logging.error(f'Error al unirse a la sala: {e}')
            emit('error', {'message': f'Error al unirse a la sala: {str(e)}'})

    @socketio.on('leave_room')
    def handle_leave_room(data):
        try:
            # Verificar que el usuario esté autenticado
            if request.sid not in connected_users:
                emit('error', {'message': 'Usuario no autenticado'})
                return
                
            user_info = connected_users[request.sid]
            user = User.query.get(user_info['user_id'])
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
                    logging.info(f'Usuario {user.username} salió de la sala {room.name}')
            
        except Exception as e:
            logging.error(f'Error al salir de la sala: {e}')
            emit('error', {'message': f'Error al salir de la sala: {str(e)}'})

    @socketio.on('send_message')
    def handle_send_message(data):
        try:
            if request.sid not in connected_users:
                emit('error', {'message': 'Usuario no autenticado'})
                return
                
            user_info = connected_users[request.sid]
            user = User.query.get(user_info['user_id'])
            room_id = data.get('room_id')
            content = data.get('content', '').strip()
            
            if not room_id or not content:
                emit('error', {'message': 'room_id y content son requeridos'})
                return
            
            room = Room.query.get(room_id)
            if not room:
                emit('error', {'message': 'Sala no encontrada'})
                return
            
            message = Message(
                content=content,
                user_id=user.id,
                room_id=room_id
            )
            db.session.add(message)
            db.session.commit()
            
    
            message_data = {
                'id': message.id,
                'content': message.content,
                'room_id': message.room_id,
                'created_at': message.created_at.isoformat(),
                'file_url': message.file_url, # Será null para mensajes de texto
                'sender': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name
                }
            }
            
            emit('new_message', message_data, room=str(room_id))
            logging.info(f'Mensaje de texto enviado por {user.username} en sala {room.name}')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error al enviar mensaje: {e}')
            emit('error', {'message': f'Error al enviar mensaje: {str(e)}'})

# Crear la aplicación
app, socketio = create_app()

# Importar db para que esté disponible para run.py
from models import db

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    logging.info(f"🚀 IzpoChat Backend iniciando en {host}:{port}")
    
    if socketio:
        socketio.run(app, 
                    host=host, 
                    port=port, 
                    debug=False,
                    use_reloader=False)
    else:
        app.run(host=host, 
                port=port, 
                debug=False,
                threaded=True,
                use_reloader=False)