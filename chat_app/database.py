# chat_app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .core.config import settings

# Crear el engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Mostrar queries SQL en desarrollo
    pool_pre_ping=True,   # Verificar conexiones antes de usarlas
    pool_recycle=300      # Reciclar conexiones cada 5 minutos
)

# Crear SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency para obtener una sesión de base de datos.
    Se usa como dependencia en FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Crear todas las tablas en la base de datos.
    Usar esto en desarrollo o para inicialización.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Eliminar todas las tablas de la base de datos.
    ¡Usar con cuidado!
    """
    from .models import Base
    Base.metadata.drop_all(bind=engine)
