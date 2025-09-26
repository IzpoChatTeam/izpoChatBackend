# config.py
import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

class Config:
    """Clase de configuración centralizada para la aplicación."""
    
    # Claves de seguridad
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # --- Configuración de la Base de Datos ---
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    # URL de conexión para SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
    )

    # Optimización para Supabase PgBouncer (Connection Pooler)
    # Deshabilita el pool de SQLAlchemy para usar el de Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": NullPool,
    }

    # Desactiva una función de Flask-SQLAlchemy que consume recursos
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Configuración de Supabase Storage ---
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET")