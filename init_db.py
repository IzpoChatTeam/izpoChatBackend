# init_db.py
"""
Script para inicializar la base de datos y crear las tablas
"""

from chat_app.database import create_tables, engine
from chat_app.models import Base

def main():
    print("Creando tablas de base de datos...")
    create_tables()
    print("✅ Tablas creadas exitosamente!")
    
    # Verificar conexión
    try:
        with engine.connect() as conn:
            print("✅ Conexión a la base de datos exitosa!")
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")

if __name__ == "__main__":
    main()