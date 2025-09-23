# chat_app/models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# Tabla de asociación para usuarios en salas (muchos a muchos)
user_room_association = Table(
    'user_rooms',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('room_id', Integer, ForeignKey('rooms.id'))
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    messages = relationship("Message", back_populates="sender")
    uploaded_files = relationship("FileUpload", back_populates="uploader")
    rooms = relationship("Room", secondary=user_room_association, back_populates="members")
    owned_rooms = relationship("Room", back_populates="owner")


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    owner = relationship("User", back_populates="owned_rooms")
    members = relationship("User", secondary=user_room_association, back_populates="rooms")
    messages = relationship("Message", back_populates="room")
    files = relationship("FileUpload", back_populates="room")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    sender = relationship("User", back_populates="messages")
    room = relationship("Room", back_populates="messages")
    file = relationship("FileUpload", back_populates="message")


class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)  # Nombre original del archivo
    file_path = Column(String, nullable=False)  # Path en Supabase Storage
    file_url = Column(String, nullable=False)  # URL pública del archivo
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Descripción opcional
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)  # Archivo asociado a una sala
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="uploaded_files")
    room = relationship("Room", back_populates="files")
    message = relationship("Message", back_populates="file", uselist=False)
