# models.py
from extension import db
from datetime import datetime
from sqlalchemy import func

# Tabla de asociación para miembros de las conversaciones (salas privadas)
room_members = db.Table('room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id', ondelete='CASCADE'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación many-to-many para las conversaciones en las que participa el usuario
    conversations = db.relationship('Room', secondary=room_members, lazy='subquery',
                                   backref=db.backref('members', lazy=True))

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    # Para conversaciones 1-a-1, el nombre puede ser generado automáticamente
    name = db.Column(db.String(150), nullable=False)
    is_private = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')

    @classmethod
    def find_private_conversation(cls, user1_id, user2_id):
        """Encuentra una conversación privada existente entre dos usuarios."""
        return cls.query.filter(cls.is_private == True)\
            .join(room_members)\
            .filter(room_members.c.user_id.in_([user1_id, user2_id]))\
            .group_by(cls.id)\
            .having(func.count(room_members.c.user_id) == 2)\
            .first()

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    file_url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User')