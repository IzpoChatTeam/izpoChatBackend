# init_tables.py - Script para crear tablas en Supabase PostgreSQL

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from models import db, User, Room, Message, FileUpload

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL no encontrada en variables de entorno")
    exit(1)

print(f"🔗 Conectando a base de datos: {DATABASE_URL[:50]}...")

# Crear engine
engine = create_engine(DATABASE_URL, echo=True)

def create_tables():
    """Crear todas las tablas en Supabase"""
    try:
        # Probar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version}")
        
        # Crear todas las tablas basadas en los modelos SQLAlchemy
        print("\n📝 Creando tablas...")
        
        # Importar Base desde models
        from models import db
        db.metadata.bind = engine
        db.metadata.create_all(engine)
        
        print("\n🎉 ¡Tablas creadas exitosamente!")
        
        # Listar tablas creadas
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print("\n📋 Tablas en la base de datos:")
            for table in tables:
                print(f"  ✓ {table[0]}")
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False
    
    return True

def insert_sample_data():
    """Insertar datos de ejemplo para testing"""
    try:
        print("\n🌱 Insertando datos de ejemplo...")
        
        with engine.connect() as conn:
            # Insertar usuario de prueba
            conn.execute(text("""
                INSERT INTO users (username, email, password_hash, full_name, created_at) 
                VALUES ('admin', 'admin@izpochat.com', '$2b$12$example.hash.here', 'Administrador', NOW())
                ON CONFLICT (username) DO NOTHING
            """))
            
            # Insertar sala de prueba
            conn.execute(text("""
                INSERT INTO rooms (name, description, created_by, created_at)
                VALUES ('Sala General', 'Sala principal para conversaciones', 1, NOW())
                ON CONFLICT DO NOTHING
            """))
            
            conn.commit()
            print("✅ Datos de ejemplo insertados")
            
    except Exception as e:
        print(f"⚠️ Error insertando datos de ejemplo: {e}")

if __name__ == "__main__":
    print("🚀 Inicializando base de datos Supabase...")
    
    if create_tables():
        insert_sample_data()
        print("\n🎯 Base de datos lista para usar!")
        print("\n📱 Puedes probar los endpoints:")
        print("  POST /api/users/register - Registrar usuarios")
        print("  POST /api/users/login - Login")
        print("  GET  /api/rooms - Ver salas")
        print("  POST /api/rooms - Crear salas")
    else:
        print("\n❌ Error en la inicialización")
        exit(1)