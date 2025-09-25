from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Tabla de asociación para miembros de salas (conversaciones privadas)
room_members = db.Table('room_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('room_id', db.Integer, db.ForeignKey('rooms.id'), primary_key=True),
    db.Column('joined_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    messages = db.relationship('Message', backref='user', lazy=True)
    rooms = db.relationship('Room', backref='creator', lazy=True)
    uploads = db.relationship('FileUpload', backref='user', lazy=True)
    
    # Relación many-to-many para salas donde el usuario es miembro
    joined_rooms = db.relationship('Room', secondary=room_members, lazy='subquery',
                                 backref=db.backref('members', lazy=True))
    
    def __repr__(self):
        return f'<User {self.username}>'

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=True, nullable=False)  # True para conversaciones privadas
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Room {self.name}>'
    
    @classmethod
    def find_private_conversation(cls, user1_id, user2_id):
        """Encuentra una conversación privada entre dos usuarios específicos"""
        return cls.query.filter(
            cls.is_private == True
        ).join(room_members).filter(
            room_members.c.user_id.in_([user1_id, user2_id])
        ).group_by(cls.id).having(
            db.func.count(room_members.c.user_id) == 2
        ).first()

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    file_url = db.Column(db.String(500))  # URL del archivo si es un mensaje con archivo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id} by {self.user_id}>'

class FileUpload(db.Model):
    __tablename__ = 'file_uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    content_type = db.Column(db.String(100))
    file_url = db.Column(db.String(500), nullable=False)  # URL en Supabase
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FileUpload {self.filename}>'