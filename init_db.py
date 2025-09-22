# init_db.py
"""
Script para inicializar la base de datos y crear las tablas
"""

import sys
import socket
from urllib.parse import urlparse
from sqlalchemy import text
from chat_app.database import create_tables, engine
from chat_app.models import Base
from chat_app.core.config import settings

def check_network_connectivity(url: str) -> bool:
    """Verificar conectividad de red al hostname de la base de datos"""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 5432
        
        print(f"🔍 Verificando conectividad a {hostname}:{port}...")
        
        # Intentar conexión TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 segundos timeout
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Conectividad de red OK")
            return True
        else:
            print(f"❌ No se puede conectar a {hostname}:{port}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando conectividad: {e}")
        return False

def main():
    print("🚀 Inicializando base de datos IzpoChat...")
    print(f"📍 URL de base de datos: {settings.DATABASE_URL[:50]}...")
    
    # Verificar conectividad de red primero
    if not check_network_connectivity(settings.DATABASE_URL):
        print("\n💡 Posibles soluciones:")
        print("1. Verificar tu conexión a internet")
        print("2. Verificar que la URL de Supabase sea correcta en .env")
        print("3. Verificar que el proyecto Supabase esté activo")
        print("4. Verificar que no haya firewall bloqueando la conexión")
        sys.exit(1)
    
    # Intentar crear las tablas
    try:
        print("\n📊 Creando tablas de base de datos...")
        create_tables()
        print("✅ Tablas creadas exitosamente!")
        
        # Verificar conexión a la base de datos
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos verificada!")
            
    except Exception as e:
        print(f"❌ Error con la base de datos: {e}")
        print("\n💡 Posibles soluciones:")
        print("1. Verificar que el password en DATABASE_URL sea correcto")
        print("2. Verificar que el nombre de la base de datos sea correcto")
        print("3. Verificar permisos de usuario en Supabase")
        print("4. Revisar los logs de Supabase para más detalles")
        sys.exit(1)
    
    print("\n🎉 Inicialización completada exitosamente!")

if __name__ == "__main__":
    main()