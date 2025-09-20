# chat_app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from passlib.context import CryptContext
from typing import List, Optional
from . import models, schemas
from datetime import datetime

# Configuración para hashear passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hashear una contraseña"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar una contraseña contra su hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== USER CRUD ====================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Obtener usuario por ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Obtener usuario por email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Obtener usuario por username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Obtener lista de usuarios"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Crear nuevo usuario"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    """Actualizar usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    """Autenticar usuario"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ==================== ROOM CRUD ====================

def get_room(db: Session, room_id: int) -> Optional[models.Room]:
    """Obtener sala por ID"""
    return db.query(models.Room).filter(models.Room.id == room_id).first()


def get_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[models.Room]:
    """Obtener lista de salas públicas"""
    return db.query(models.Room).filter(models.Room.is_private == False).offset(skip).limit(limit).all()


def get_user_rooms(db: Session, user_id: int) -> List[models.Room]:
    """Obtener salas donde el usuario es miembro"""
    user = get_user(db, user_id)
    if not user:
        return []
    return user.rooms


def create_room(db: Session, room: schemas.RoomCreate, owner_id: int) -> models.Room:
    """Crear nueva sala"""
    db_room = models.Room(
        name=room.name,
        description=room.description,
        is_private=room.is_private,
        owner_id=owner_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    # Agregar al owner como miembro
    add_user_to_room(db, db_room.id, owner_id)
    
    return db_room


def update_room(db: Session, room_id: int, room_update: schemas.RoomUpdate) -> Optional[models.Room]:
    """Actualizar sala"""
    db_room = get_room(db, room_id)
    if not db_room:
        return None
    
    update_data = room_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_room, field, value)
    
    db.commit()
    db.refresh(db_room)
    return db_room


def add_user_to_room(db: Session, room_id: int, user_id: int) -> bool:
    """Agregar usuario a sala"""
    room = get_room(db, room_id)
    user = get_user(db, user_id)
    
    if not room or not user:
        return False
    
    if user not in room.members:
        room.members.append(user)
        db.commit()
    
    return True


def remove_user_from_room(db: Session, room_id: int, user_id: int) -> bool:
    """Remover usuario de sala"""
    room = get_room(db, room_id)
    user = get_user(db, user_id)
    
    if not room or not user:
        return False
    
    if user in room.members:
        room.members.remove(user)
        db.commit()
    
    return True


def is_user_in_room(db: Session, room_id: int, user_id: int) -> bool:
    """Verificar si usuario está en sala"""
    room = get_room(db, room_id)
    user = get_user(db, user_id)
    
    if not room or not user:
        return False
    
    return user in room.members


# ==================== MESSAGE CRUD ====================

def get_message(db: Session, message_id: int) -> Optional[models.Message]:
    """Obtener mensaje por ID"""
    return db.query(models.Message).filter(models.Message.id == message_id).first()


def get_room_messages(
    db: Session, 
    room_id: int, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.Message]:
    """Obtener mensajes de una sala"""
    return (
        db.query(models.Message)
        .filter(models.Message.room_id == room_id)
        .order_by(desc(models.Message.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_message(db: Session, message: schemas.MessageCreate, sender_id: int) -> models.Message:
    """Crear nuevo mensaje"""
    db_message = models.Message(
        content=message.content,
        room_id=message.room_id,
        sender_id=sender_id,
        file_id=message.file_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


# ==================== FILE UPLOAD CRUD ====================

def get_file_upload(db: Session, file_id: int) -> Optional[models.FileUpload]:
    """Obtener archivo subido por ID"""
    return db.query(models.FileUpload).filter(models.FileUpload.id == file_id).first()


def create_file_upload(db: Session, file_upload: schemas.FileUploadCreate) -> models.FileUpload:
    """Crear registro de archivo subido"""
    db_file = models.FileUpload(
        original_filename=file_upload.original_filename,
        stored_filename=file_upload.stored_filename,
        file_size=file_upload.file_size,
        content_type=file_upload.content_type,
        public_url=file_upload.public_url,
        uploader_id=file_upload.uploader_id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_user_files(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[models.FileUpload]:
    """Obtener archivos subidos por un usuario"""
    return (
        db.query(models.FileUpload)
        .filter(models.FileUpload.uploader_id == user_id)
        .order_by(desc(models.FileUpload.uploaded_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
