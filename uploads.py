from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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

async def upload_to_supabase(file_content, filename, content_type):
    """Subir archivo a Supabase Storage"""
    try:
        # Generar nombre único para el archivo
        unique_filename = f"{uuid.uuid4()}_{secure_filename(filename)}"
        
        # URL del API de Supabase Storage
        upload_url = f"{Config.SUPABASE_URL}/storage/v1/object/{Config.SUPABASE_STORAGE_BUCKET}/{unique_filename}"
        
        headers = {
            'Authorization': f'Bearer {Config.SUPABASE_ANON_KEY}',
            'Content-Type': content_type
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(upload_url, content=file_content, headers=headers)
            
            if response.status_code == 200:
                # URL pública del archivo
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
        
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        room_id = request.form.get('room_id')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not room_id:
            return jsonify({'error': 'room_id is required'}), 400
        
        # Verificar tipo de archivo
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {Config.UPLOAD_EXTENSIONS}'}), 400
        
        # Verificar tamaño del archivo
        file.seek(0, 2)  # Ir al final del archivo
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > Config.MAX_CONTENT_LENGTH:
            return jsonify({'error': f'File too large. Max size: {Config.MAX_CONTENT_LENGTH // (1024*1024)}MB'}), 400
        
        # Leer contenido del archivo
        file_content = file.read()
        
        # Subir a Supabase
        import asyncio
        upload_result = asyncio.run(upload_to_supabase(
            file_content,
            file.filename,
            file.content_type
        ))
        
        if not upload_result['success']:
            return jsonify({'error': upload_result['error']}), 500
        
        # Guardar información del archivo en la base de datos
        file_upload = FileUpload(
            filename=upload_result['filename'],
            original_filename=file.filename,
            file_size=file_size,
            content_type=file.content_type,
            file_url=upload_result['url'],
            user_id=user_id,
            room_id=int(room_id)
        )
        
        db.session.add(file_upload)
        
        # Crear mensaje con el archivo
        message_content = f"📎 Archivo compartido: {file.filename}"
        message = Message(
            content=message_content,
            user_id=user_id,
            room_id=int(room_id),
            file_url=upload_result['url']
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': file_upload.id,
            'file_url': upload_result['url'],
            'filename': file.filename,
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