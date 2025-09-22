# chat_app/routers/uploads.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from google.cloud import storage
from google.api_core import exceptions
import uuid
import os
import magic
from typing import List

# Importa la configuración y dependencias
from ..core.config import settings
from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_current_active_user

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Configura el cliente de Google Cloud Storage
storage_client = storage.Client()
bucket_name = settings.GCS_BUCKET_NAME

# Tipos de archivos permitidos
ALLOWED_MIME_TYPES = {
    # Documentos
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'text/plain': '.txt',
    'text/csv': '.csv',
    
    # Imágenes
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    
    # Audio
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/ogg': '.ogg',
    
    # Video
    'video/mp4': '.mp4',
    'video/avi': '.avi',
    'video/quicktime': '.mov',
    'video/x-msvideo': '.avi',
    
    # Archivos comprimidos
    'application/zip': '.zip',
    'application/x-rar-compressed': '.rar',
    'application/x-7z-compressed': '.7z',
}

# Tamaño máximo de archivo (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


def validate_file(file: UploadFile) -> dict:
    """Validar archivo subido"""
    # Verificar tamaño
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Archivo muy grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Verificar tipo de archivo
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido: {file.content_type}"
        )
    
    return {
        "valid": True,
        "content_type": file.content_type,
        "extension": ALLOWED_MIME_TYPES[file.content_type]
    }


@router.post("/", response_model=schemas.FileUpload, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Subir archivo a Google Cloud Storage y registrarlo en la base de datos.
    """
    # Validar archivo
    validation = validate_file(file)
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except exceptions.NotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El bucket de almacenamiento no está disponible"
        )

    # Generar nombre único para el archivo
    file_extension = validation["extension"]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Crear path organizado por tipo y fecha
    import datetime
    today = datetime.datetime.now()
    folder_path = f"{today.year}/{today.month:02d}/{today.day:02d}"
    full_path = f"{folder_path}/{unique_filename}"
    
    # Crear el blob en GCS
    blob = bucket.blob(full_path)

    try:
        # Leer el contenido del archivo
        file_content = await file.read()
        file_size = len(file_content)
        
        # Subir archivo
        blob.upload_from_string(
            file_content,
            content_type=file.content_type
        )
        
        # Hacer el archivo público
        blob.make_public()
        
        # Registrar en la base de datos
        file_upload_data = schemas.FileUploadCreate(
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_size=file_size,
            content_type=file.content_type,
            public_url=blob.public_url,
            uploader_id=current_user.id
        )
        
        db_file = crud.create_file_upload(db=db, file_upload=file_upload_data)
        
        return db_file
        
    except Exception as e:
        # Si hay error, intentar limpiar el archivo de GCS
        try:
            blob.delete()
        except:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo: {str(e)}"
        )


@router.get("/{file_id}", response_model=schemas.FileUpload)
def get_file_info(
    file_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener información de un archivo"""
    file_info = crud.get_file_upload(db, file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    return file_info


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar archivo (solo el propietario)"""
    file_info = crud.get_file_upload(db, file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    # Verificar que sea el propietario del archivo
    if file_info.uploader_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este archivo"
        )
    
    try:
        # Eliminar de Google Cloud Storage
        bucket = storage_client.get_bucket(bucket_name)
        
        # Extraer el path del archivo de la URL pública
        # Formato típico: https://storage.googleapis.com/bucket-name/path/to/file
        url_parts = file_info.public_url.split(f'{bucket_name}/')
        if len(url_parts) > 1:
            file_path = url_parts[1]
            blob = bucket.blob(file_path)
            blob.delete()
        
        # Eliminar de la base de datos
        db.delete(file_info)
        db.commit()
        
        return {"message": "Archivo eliminado exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando archivo: {str(e)}"
        )


@router.get("/")
def list_user_files(
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar archivos del usuario actual"""
    files = crud.get_user_files(db, current_user.id, skip=skip, limit=limit)
    return {
        "files": files,
        "total": len(files),
        "skip": skip,
        "limit": limit
    }


@router.post("/multiple", response_model=List[schemas.FileUpload])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Subir múltiples archivos"""
    if len(files) > 10:  # Límite de 10 archivos por vez
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 10 archivos por vez"
        )
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # Usar la función de subida individual
            result = await upload_file(file, current_user, db)
            uploaded_files.append(result)
        except HTTPException as e:
            errors.append({
                "filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    response = {
        "uploaded_files": uploaded_files,
        "total_uploaded": len(uploaded_files),
        "total_files": len(files)
    }
    
    if errors:
        response["errors"] = errors
    
    return response


@router.get("/types/allowed")
def get_allowed_file_types():
    """Obtener tipos de archivos permitidos"""
    return {
        "allowed_types": list(ALLOWED_MIME_TYPES.keys()),
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "categories": {
            "documents": [k for k in ALLOWED_MIME_TYPES.keys() if k.startswith('application/') or k.startswith('text/')],
            "images": [k for k in ALLOWED_MIME_TYPES.keys() if k.startswith('image/')],
            "audio": [k for k in ALLOWED_MIME_TYPES.keys() if k.startswith('audio/')],
            "video": [k for k in ALLOWED_MIME_TYPES.keys() if k.startswith('video/')]
        }
    }