from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import socketio
from werkzeug.utils import secure_filename
import os
import uuid
import httpx
from models import db, FileUpload, Message
from config import Config

uploads_bp = Blueprint('uploads', __name__)

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           '.' + filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in Config.UPLOAD_EXTENSIONS]

def upload_to_supabase(file_content, filename, content_type):
    """Subir archivo a Supabase Storage de forma síncrona"""
    try:
        unique_filename = f"{uuid.uuid4()}_{secure_filename(filename)}"
        upload_url = f"{Config.SUPABASE_URL}/storage/v1/object/{Config.SUPABASE_STORAGE_BUCKET}/{unique_filename}"
        
        headers = {
            'Authorization': f'Bearer {Config.SUPABASE_ANON_KEY}',
            'Content-Type': content_type
        }
        
        # --- CAMBIO IMPORTANTE: Usamos el cliente síncrono httpx.Client ---
        with httpx.Client() as client:
            response = client.post(upload_url, content=file_content, headers=headers)
            
            if response.status_code == 200:
                public_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{Config.SUPABASE_STORAGE_BUCKET}/{unique_filename}"
                return {
                    'success': True,
                    'url': public_url,
                    'filename': unique_filename
                }
            else:
                return {
                    'success': False,
                    'error': f'Error uploading to Supabase: {response.text}'
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': f'Error en upload: {str(e)}'
        }

@uploads_bp.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id) # Obtenemos el objeto User
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        room_id = request.form.get('room_id')
        
        # ... (tus otras validaciones están bien)
        if not room_id:
            return jsonify({'error': 'room_id is required'}), 400

        file_content = file.read()
        
        # --- CAMBIO IMPORTANTE: Llamamos a la nueva función síncrona ---
        upload_result = upload_to_supabase(
            file_content,
            file.filename,
            file.content_type
        )
        
        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 500
        
        file_upload = FileUpload(
            filename=upload_result['filename'],
            original_filename=file.filename,
            file_size=len(file_content),
            content_type=file.content_type,
            file_url=upload_result['url'],
            user_id=user_id,
            room_id=int(room_id)
        )
        db.session.add(file_upload)
        
        # Crear el mensaje asociado al archivo
        message_content = f"📎 Archivo: {file.filename}"
        message = Message(
            content=message_content,
            user_id=user_id,
            room_id=int(room_id),
            file_url=upload_result['url']
        )
        db.session.add(message)
        db.session.commit()
        
        # --- NUEVO: Emitir el mensaje a la sala a través de WebSocket ---
        message_data = {
            'id': message.id,
            'content': message.content,
            'room_id': message.room_id,
            'created_at': message.created_at.isoformat(),
            'file_url': message.file_url,
            'sender': {  # El frontend espera un objeto 'sender' anidado
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name
            }
        }
        socketio.emit('new_message', message_data, room=str(room_id))
        
        return jsonify({
            'message': 'File uploaded and message sent successfully',
            'file_url': upload_result['url'],
            'message_id': message.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@uploads_bp.route('/api/files/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    try:
        file_upload = FileUpload.query.get(file_id)
        
        if not file_upload:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'id': file_upload.id,
            'filename': file_upload.original_filename,
            'file_size': file_upload.file_size,
            'content_type': file_upload.content_type,
            'file_url': file_upload.file_url,
            'user_id': file_upload.user_id,
            'room_id': file_upload.room_id,
            'created_at': file_upload.created_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/api/rooms/<int:room_id>/files', methods=['GET'])
@jwt_required()
def get_room_files(room_id):
    try:
        files = FileUpload.query.filter_by(room_id=room_id).order_by(FileUpload.created_at.desc()).all()
        
        return jsonify([{
            'id': file.id,
            'filename': file.original_filename,
            'file_size': file.file_size,
            'content_type': file.content_type,
            'file_url': file.file_url,
            'user_id': file.user_id,
            'created_at': file.created_at.isoformat()
        } for file in files]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500