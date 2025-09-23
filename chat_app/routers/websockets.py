# chat_app/routers/websockets.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
import json
import asyncio
from datetime import datetime

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import get_user_from_token, check_room_access

router = APIRouter()

class ConnectionManager:
    """Gestor de conexiones WebSocket para chat en tiempo real"""
    
    def __init__(self):
        # {room_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """Conectar usuario a una sala"""
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
            
        self.active_connections[room_id][user_id] = websocket
        
        # Notificar a otros usuarios que alguien se unió
        await self.broadcast_to_room(
            room_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            },
            exclude_user=user_id
        )
    
    def disconnect(self, room_id: int, user_id: int):
        """Desconectar usuario de una sala"""
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
                
            # Si no quedan usuarios en la sala, eliminar la sala
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def send_personal_message(self, message: dict, room_id: int, user_id: int):
        """Enviar mensaje a un usuario específico"""
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                websocket = self.active_connections[room_id][user_id]
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    # Si hay error, desconectar
                    self.disconnect(room_id, user_id)
    
    async def broadcast_to_room(self, room_id: int, message: dict, exclude_user: int = None):
        """Enviar mensaje a todos los usuarios de una sala"""
        if room_id not in self.active_connections:
            return
            
        # Lista de usuarios a desconectar (si hay errores)
        users_to_disconnect = []
        
        for user_id, websocket in self.active_connections[room_id].items():
            if exclude_user and user_id == exclude_user:
                continue
                
            try:
                await websocket.send_text(json.dumps(message))
            except:
                # Marcar para desconectar
                users_to_disconnect.append(user_id)
        
        # Desconectar usuarios con problemas
        for user_id in users_to_disconnect:
            self.disconnect(room_id, user_id)
    
    def get_room_users(self, room_id: int) -> List[int]:
        """Obtener lista de usuarios conectados en una sala"""
        if room_id in self.active_connections:
            return list(self.active_connections[room_id].keys())
        return []

# Instancia global del gestor de conexiones
manager = ConnectionManager()


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint para chat en tiempo real"""
    try:
        # Validar que room_id sea válido
        if room_id <= 0:
            await websocket.close(code=1008, reason="ID de sala inválido")
            return
        
        # Verificar token y obtener usuario
        user = await get_user_from_token(token, db)
        
        # Verificar que la sala existe
        room = crud.get_room(db, room_id)
        if not room:
            await websocket.close(code=1008, reason="Sala no encontrada")
            return
        
        # Conectar al usuario
        await manager.connect(websocket, room_id, user.id)
        
        # Enviar mensaje de bienvenida
        await manager.send_personal_message(
            {
                "type": "welcome",
                "message": f"Conectado a la sala: {room.name}",
                "room_id": room_id,
                "user_id": user.id,
                "timestamp": datetime.now().isoformat()
            },
            room_id,
            user.id
        )
        
        # Enviar lista de usuarios conectados
        connected_users = manager.get_room_users(room_id)
        await manager.send_personal_message(
            {
                "type": "users_online",
                "users": connected_users,
                "count": len(connected_users),
                "timestamp": datetime.now().isoformat()
            },
            room_id,
            user.id
        )
        
        # Bucle principal para recibir mensajes
        while True:
            try:
                # Recibir mensaje del cliente
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Procesar diferentes tipos de mensajes
                message_type = message_data.get("type", "message")
                
                if message_type == "message":
                    await handle_chat_message(websocket, room_id, user, message_data, db)
                elif message_type == "typing":
                    await handle_typing_indicator(room_id, user, message_data)
                elif message_type == "ping":
                    await handle_ping(websocket, user)
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Tipo de mensaje desconocido: {message_type}"
                    }))
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Formato de mensaje inválido"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error procesando mensaje: {str(e)}"
                }))
                
    except HTTPException as e:
        # Error de autenticación o acceso
        await websocket.close(code=1008, reason=e.detail)
    except Exception as e:
        # Error inesperado
        await websocket.close(code=1011, reason=f"Error interno: {str(e)}")
    finally:
        # Limpiar conexión
        manager.disconnect(room_id, user.id)
        
        # Notificar a otros usuarios que alguien se desconectó
        await manager.broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "user_id": user.id,
                "timestamp": datetime.now().isoformat()
            }
        )


async def handle_chat_message(websocket: WebSocket, room_id: int, user: models.User, message_data: dict, db: Session):
    """Manejar mensaje de chat"""
    try:
        content = message_data.get("content", "").strip()
        file_id = message_data.get("file_id")
        
        if not content and not file_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Mensaje vacío"
            }))
            return
        
        # Crear mensaje en la base de datos
        message_create = schemas.MessageCreate(
            content=content,
            room_id=room_id,
            file_id=file_id
        )
        
        db_message = crud.create_message(db=db, message=message_create, sender_id=user.id)
        
        # Preparar mensaje para broadcast
        broadcast_message = {
            "type": "message",
            "id": db_message.id,
            "content": db_message.content,
            "room_id": room_id,
            "sender": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name
            },
            "file_id": db_message.file_id,
            "timestamp": db_message.created_at.isoformat()
        }
        
        # Si hay archivo, incluir información del archivo
        if db_message.file_id:
            file_info = crud.get_file_upload(db, db_message.file_id)
            if file_info:
                broadcast_message["file"] = {
                    "id": file_info.id,
                    "original_filename": file_info.original_filename,
                    "public_url": file_info.public_url,
                    "content_type": file_info.content_type,
                    "file_size": file_info.file_size
                }
        
        # Enviar mensaje a todos los usuarios de la sala
        await manager.broadcast_to_room(room_id, broadcast_message)
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error enviando mensaje: {str(e)}"
        }))


async def handle_typing_indicator(room_id: int, user: models.User, message_data: dict):
    """Manejar indicador de escritura"""
    typing_status = message_data.get("typing", False)
    
    typing_message = {
        "type": "typing",
        "user_id": user.id,
        "username": user.username,
        "typing": typing_status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Enviar a todos excepto al que está escribiendo
    await manager.broadcast_to_room(room_id, typing_message, exclude_user=user.id)


async def handle_ping(websocket: WebSocket, user: models.User):
    """Manejar ping para mantener conexión activa"""
    await websocket.send_text(json.dumps({
        "type": "pong",
        "user_id": user.id,
        "timestamp": datetime.now().isoformat()
    }))


@router.get("/ws/rooms/{room_id}/online")
async def get_online_users(
    room_id: int,
    current_user: models.User = Depends(get_user_from_token),
    db: Session = Depends(get_db)
):
    """Obtener usuarios conectados en una sala"""
    # Verificar acceso a la sala
    check_room_access(room_id, current_user, db)
    
    # Obtener usuarios conectados
    connected_user_ids = manager.get_room_users(room_id)
    
    # Obtener información completa de los usuarios
    connected_users = []
    for user_id in connected_user_ids:
        user = crud.get_user(db, user_id)
        if user:
            connected_users.append({
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name
            })
    
    return {
        "room_id": room_id,
        "online_users": connected_users,
        "count": len(connected_users)
    }