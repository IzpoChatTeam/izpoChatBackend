# uploads.py - Router para subir archivos usando Supabase Storage

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
from datetime import datetime
import httpx
import mimetypes

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_current_active_user
from ..core.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Tipos de archivos permitidos
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain", "text/csv",
    "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


async def upload_to_supabase(file: UploadFile, file_path: str) -> str:
    """Subir archivo a Supabase Storage"""
    try:
        # Leer contenido del archivo
        file_content = await file.read()
        
        # URL del endpoint de Supabase Storage
        upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{file_path}"
        
        # Headers para autenticación
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": file.content_type or "application/octet-stream"
        }
        
        # Subir archivo
        async with httpx.AsyncClient() as client:
            response = await client.post(
                upload_url,
                content=file_content,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error subiendo a Supabase: {response.text}"
                )
        
        # URL pública del archivo
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{file_path}"
        return public_url
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )


@router.post("/", response_model=schemas.FileUpload)
async def upload_file(
    file: UploadFile = File(...),
    room_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Subir archivo a Supabase Storage"""
    
    # Validar tipo de archivo
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: {file.content_type}"
        )
    
    # Validar tamaño (FastAPI no lee todo el archivo en memoria automáticamente)
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo muy grande. Máximo {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Resetear el puntero del archivo
    await file.seek(0)
    
    # Generar nombre único
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Crear path en bucket
    timestamp = datetime.now().strftime("%Y/%m/%d")
    file_path = f"uploads/{current_user.id}/{timestamp}/{unique_filename}"
    
    # Subir a Supabase
    public_url = await upload_to_supabase(file, file_path)
    
    # Guardar metadata en base de datos
    file_data = schemas.FileUploadCreate(
        filename=file.filename or unique_filename,
        file_path=file_path,
        file_url=public_url,
        file_size=len(file_content),
        content_type=file.content_type,
        room_id=room_id,
        description=description
    )
    
    db_file = crud.create_file_upload(db, file_data, current_user.id)
    return db_file


@router.get("/", response_model=List[schemas.FileUpload])
def list_user_files(
    skip: int = 0,
    limit: int = 50,
    room_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener archivos del usuario actual"""
    files = crud.get_user_files(db, current_user.id, skip=skip, limit=limit, room_id=room_id)
    return files


@router.get("/{file_id}", response_model=schemas.FileUpload)
def get_file(
    file_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener información de un archivo específico"""
    file = crud.get_file_upload(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Verificar que el usuario tenga acceso al archivo
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este archivo")
    
    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Eliminar archivo"""
    file = crud.get_file_upload(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Verificar que el usuario tenga acceso al archivo
    if file.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este archivo")
    
    try:
        # Eliminar de Supabase Storage
        delete_url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{file.file_path}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url, headers=headers)
            # No fallar si el archivo ya no existe en storage
            if response.status_code not in [200, 204, 404]:
                print(f"Warning: Error eliminando de Supabase: {response.text}")
        
        # Eliminar de base de datos
        crud.delete_file_upload(db, file_id)
        
        return {"message": "Archivo eliminado correctamente"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando archivo: {str(e)}"
        )


@router.get("/types/allowed")
def get_allowed_file_types():
    """Obtener tipos de archivos permitidos"""
    return {
        "message": "Supabase Storage configured",
        "allowed_types": list(ALLOWED_MIME_TYPES),
        "max_size_mb": MAX_FILE_SIZE // (1024*1024),
        "storage_provider": "Supabase",
        "bucket": settings.SUPABASE_STORAGE_BUCKET
    }