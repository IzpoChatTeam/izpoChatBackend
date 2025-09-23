# chat_app/routers/rooms.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import crud, schemas, models
from ..dependencies import (
    get_current_active_user,
    check_room_access,
    check_room_ownership
)

router = APIRouter(tags=["rooms"])  # Sin prefix aquí


@router.get("/", response_model=List[schemas.Room])
def get_public_rooms(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de salas públicas"""
    rooms = crud.get_rooms(db, skip=skip, limit=limit)
    return rooms


@router.get("/{room_id}", response_model=schemas.Room)
def get_room(
    room_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener información de una sala"""
    # Validar que room_id sea válido
    if room_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de sala inválido"
        )
    
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    return room


@router.post("/", response_model=schemas.Room, status_code=status.HTTP_201_CREATED)
def create_room(
    room: schemas.RoomCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear nueva sala"""
    return crud.create_room(db=db, room=room, owner_id=current_user.id)


@router.put("/{room_id}", response_model=schemas.Room)
def update_room(
    room_id: int,
    room_update: schemas.RoomUpdate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualizar sala (solo el propietario)"""
    check_room_ownership(room_id, current_user, db)
    
    updated_room = crud.update_room(db, room_id, room_update)
    if not updated_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    return updated_room


@router.post("/{room_id}/join")
def join_room(
    room_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Unirse a una sala"""
    # Validar que room_id sea válido
    if room_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de sala inválido"
        )
    
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Verificar si ya está en la sala
    if crud.is_user_in_room(db, room_id, current_user.id):
        return {"message": "Ya estás en esta sala", "room_id": room_id}
    
    success = crud.add_user_to_room(db, room_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo unir a la sala"
        )
    
    return {"message": "Te has unido a la sala exitosamente", "room_id": room_id}


@router.post("/{room_id}/leave")
def leave_room(
    room_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Salir de una sala"""
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Verificar si está en la sala
    if not crud.is_user_in_room(db, room_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in this room"
        )
    
    # El propietario no puede salir de su propia sala
    if room.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room owner cannot leave their own room"
        )
    
    success = crud.remove_user_from_room(db, room_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not leave room"
        )
    
    return {"message": "Successfully left room", "room_id": room_id}


@router.get("/{room_id}/messages", response_model=List[schemas.Message])
def get_room_messages(
    room_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener mensajes de una sala"""
    # Validar que room_id sea válido
    if room_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de sala inválido"
        )
    
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    return crud.get_room_messages(db, room_id, skip=skip, limit=limit)


@router.post("/{room_id}/messages", response_model=schemas.Message, status_code=status.HTTP_201_CREATED)
def send_message(
    room_id: int,
    message: schemas.MessageCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enviar mensaje a una sala"""
    # Validar que room_id sea válido
    if room_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de sala inválido"
        )
    
    room = crud.get_room(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sala no encontrada"
        )
    
    # Crear el mensaje con el room_id correcto
    message_data = schemas.MessageCreate(
        content=message.content,
        room_id=room_id
    )
    
    return crud.create_message(db=db, message=message_data, sender_id=current_user.id)


@router.get("/{room_id}/members", response_model=List[schemas.User])
def get_room_members(
    room_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener miembros de una sala"""
    room = check_room_access(room_id, current_user, db)
    return room.members