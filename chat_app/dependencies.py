# chat_app/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from .database import get_db
from .core.config import settings
from . import crud, models, schemas

# Security
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    """Verificar y decodificar JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
        return token_data
    except JWTError:
        raise credentials_exception


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Obtener usuario actual desde JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = verify_token(token, credentials_exception)
    
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Obtener usuario activo actual"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_room_access(room_id: int, current_user: models.User, db: Session) -> models.Room:
    """Verificar si el usuario tiene acceso a la sala"""
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Si la sala es privada, verificar que el usuario sea miembro
    if room.is_private and not crud.is_user_in_room(db, room_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this room"
        )
    
    return room


def check_room_ownership(room_id: int, current_user: models.User, db: Session) -> models.Room:
    """Verificar si el usuario es dueño de la sala"""
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if room.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room owner can perform this action"
        )
    
    return room


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Obtener usuario si está autenticado, None si no"""
    if not credentials:
        return None
    
    try:
        token_data = verify_token(credentials.credentials, None)
        if not token_data:
            return None
        
        user = crud.get_user_by_username(db, username=token_data.username)
        return user if user and user.is_active else None
    except:
        return None


# Dependencias para WebSocket
async def get_token_from_query(token: str) -> str:
    """Obtener token desde query parameters (para WebSocket)"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is required"
        )
    return token


async def get_user_from_token(
    token: str = Depends(get_token_from_query),
    db: Session = Depends(get_db)
) -> models.User:
    """Obtener usuario desde token (para WebSocket)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    
    token_data = verify_token(token, credentials_exception)
    user = crud.get_user_by_username(db, username=token_data.username)
    
    if not user or not user.is_active:
        raise credentials_exception
    
    return user
