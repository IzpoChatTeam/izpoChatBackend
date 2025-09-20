# chat_app/schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    pass


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


# Room Schemas
class RoomBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None


class RoomInDB(RoomBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Room(RoomInDB):
    owner: User
    members: List[User] = []


# Message Schemas
class MessageBase(BaseModel):
    content: str
    room_id: int


class MessageCreate(MessageBase):
    file_id: Optional[int] = None


class MessageInDB(MessageBase):
    id: int
    sender_id: int
    file_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Message(MessageInDB):
    sender: User
    room: Room
    file: Optional["FileUpload"] = None


# File Upload Schemas
class FileUploadBase(BaseModel):
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: str
    public_url: str


class FileUploadCreate(FileUploadBase):
    uploader_id: int


class FileUploadInDB(FileUploadBase):
    id: int
    uploader_id: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class FileUpload(FileUploadInDB):
    uploader: User


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    type: str  # "message", "join", "leave", "error"
    content: Optional[str] = None
    room_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    timestamp: Optional[datetime] = None
    file: Optional[FileUpload] = None


class ChatMessage(BaseModel):
    message: str
    room_id: int
    file_id: Optional[int] = None


# Response Schemas
class MessageResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    per_page: int
    pages: int


# Room Members Schema
class RoomMemberAction(BaseModel):
    room_id: int
    user_id: int


# Forward references
Message.model_rebuild()
FileUpload.model_rebuild()
