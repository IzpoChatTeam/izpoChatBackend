import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, decode_token
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt as pyjwt

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def create_app():
    """Factory optimizada para IzpoChat Backend"""
    app = Flask(__name__)
    
    # Configuración básica
    app.config['DEBUG'] = os.environ.get('FLASK_ENV') != 'production'
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'izpochat-secret-key')
    
    # Configuración de base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///izpochat.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración JWT
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    # Configuración de Supabase Storage
    app.config['SUPABASE_URL'] = os.environ.get('SUPABASE_URL')
    app.config['SUPABASE_ANON_KEY'] = os.environ.get('SUPABASE_ANON_KEY')
    app.config['SUPABASE_STORAGE_BUCKET'] = os.environ.get('SUPABASE_STORAGE_BUCKET', 'izpochat-bucket')
    
    # Configuración de archivos
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    logging.info("🚀 Iniciando IzpoChat Backend")
    
    # Configurar CORS
    CORS(app, 
         resources={
             r"/*": {
                 "origins": "*",
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
                 "allow_headers": ["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
                 "supports_credentials": False
             }
         },
         supports_credentials=False)
    logging.info("✅ CORS configurado para todos los orígenes")
    
    # Inicializar extensiones
    try:
        from models import db, User, Room, Message, FileUpload
        db.init_app(app)
        logging.info("✅ SQLAlchemy inicializado")
    except Exception as e:
        logging.error(f"❌ Error inicializando base de datos: {e}")
    
    try:
        jwt_manager = JWTManager(app)
        logging.info("✅ JWT Manager inicializado")
    except Exception as e:
        logging.error(f"❌ Error inicializando JWT: {e}")
    
    # Configurar SocketIO
    try:
        socketio = SocketIO(app, 
                           cors_allowed_origins="*",
                           async_mode='eventlet',
                           logger=True,
                           engineio_logger=False)
        logging.info("✅ SocketIO configurado con eventlet")
    except Exception as e:
        logging.error(f"❌ Error configurando SocketIO: {e}")
        socketio = None
    
    # Registrar blueprints
    try:
        from uploads import uploads_bp
        app.register_blueprint(uploads_bp)
        logging.info("✅ Blueprint de uploads registrado")
    except Exception as e:
        logging.warning(f"⚠️ Error registrando uploads blueprint: {e}")
    
    # Crear tablas
    with app.app_context():
        try:
            db.create_all()
            logging.info("✅ Tablas de base de datos creadas/verificadas")
        except Exception as e:
            logging.error(f"❌ Error creando tablas: {e}")
    
    # Configurar rutas y WebSocket events
    setup_routes(app)
    if socketio:
        setup_websocket_events(socketio, app)
    
    logging.info("✅ IzpoChat Backend listo")
    return app, socketio# Diccionario para trackear usuarios conectados
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
                "websocket": "WebSocket connection available"
            }
        }

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check para Render"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            db_status = "✅ connected"
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            db_status = "⚠️ disconnected"
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
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
            
            logging.info(f'Usuario {user.username} se unió a la sala {room.name}')
            
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
            # Verificar que el usuario esté autenticado
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
            
            # Verificar que la sala existe
            room = Room.query.get(room_id)
            if not room:
                emit('error', {'message': 'Sala no encontrada'})
                return
            
            # Crear mensaje en la base de datos
            message = Message(
                content=content,
                user_id=user.id,
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
            logging.info(f'Mensaje enviado por {user.username} en sala {room.name}: {content[:50]}...')
            
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error al enviar mensaje: {e}')
            emit('error', {'message': f'Error al enviar mensaje: {str(e)}'})

# Crear la aplicación
app, socketio = create_app()

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