# uploads.py - Router simplificado para subir archivos

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_current_active_user

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/")
def list_user_files(
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener archivos del usuario actual"""
    files = crud.get_user_files(db, current_user.id, skip=skip, limit=limit)
    return files


@router.get("/types/allowed")
def get_allowed_file_types():
    """Obtener tipos de archivos permitidos"""
    return {
        "message": "Upload feature will be implemented later",
        "allowed_types": ["text/plain", "application/pdf", "image/jpeg"],
        "max_size_mb": 50
    }