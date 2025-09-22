# test_connection.py
"""
Script para probar la conectividad a Supabase y diagnosticar problemas
"""

import socket
import sys
import psycopg2
from urllib.parse import urlparse
from chat_app.core.config import settings

def test_dns_resolution(hostname):
    """Probar resolución DNS"""
    print(f"🔍 Probando resolución DNS para {hostname}...")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resuelto: {hostname} -> {ip}")
        return True, ip
    except socket.gaierror as e:
        print(f"❌ Error DNS: {e}")
        return False, None

def test_tcp_connection(hostname, port, timeout=10):
    """Probar conexión TCP"""
    print(f"🔌 Probando conexión TCP a {hostname}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Conexión TCP exitosa")
            return True
        else:
            print(f"❌ Error de conexión TCP: código {result}")
            return False
    except Exception as e:
        print(f"❌ Error TCP: {e}")
        return False

def test_postgres_connection():
    """Probar conexión directa a PostgreSQL"""
    print(f"🗄️ Probando conexión a PostgreSQL...")
    try:
        # Extraer componentes de la URL
        parsed_url = urlparse(settings.DATABASE_URL)
        
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path[1:],  # Remover '/' inicial
            user=parsed_url.username,
            password=parsed_url.password,
            connect_timeout=10
        )
        
        # Probar query simple
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ Conexión PostgreSQL exitosa")
        print(f"📋 Versión: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
        return False

def test_internet_connectivity():
    """Probar conectividad general a internet"""
    print("🌐 Probando conectividad a internet...")
    test_hosts = [
        ("google.com", 80),
        ("cloudflare.com", 80),
        ("github.com", 443)
    ]
    
    for host, port in test_hosts:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Internet OK (conectado a {host})")
                return True
        except:
            continue
    
    print("❌ Sin conectividad a internet")
    return False

def main():
    print("🔧 IzpoChat - Diagnóstico de Conectividad")
    print("=" * 50)
    
    # Mostrar configuración (sin contraseña)
    parsed_url = urlparse(settings.DATABASE_URL)
    print(f"🎯 Host objetivo: {parsed_url.hostname}")
    print(f"🚪 Puerto: {parsed_url.port or 5432}")
    print(f"📊 Base de datos: {parsed_url.path[1:]}")
    print(f"👤 Usuario: {parsed_url.username}")
    print()
    
    all_tests_passed = True
    
    # 1. Probar internet
    print("1️⃣ CONECTIVIDAD A INTERNET")
    print("-" * 30)
    if not test_internet_connectivity():
        print("💡 Verifica tu conexión a internet")
        all_tests_passed = False
    print()
    
    # 2. Probar DNS
    print("2️⃣ RESOLUCIÓN DNS")
    print("-" * 30)
    dns_ok, ip = test_dns_resolution(parsed_url.hostname)
    if not dns_ok:
        print("💡 Posibles soluciones DNS:")
        print("  - Cambiar DNS a 8.8.8.8 y 8.8.4.4")
        print("  - Verificar firewall/proxy corporativo")
        print("  - Verificar que el hostname sea correcto")
        all_tests_passed = False
    print()
    
    # 3. Probar TCP solo si DNS funciona
    if dns_ok:
        print("3️⃣ CONEXIÓN TCP")
        print("-" * 30)
        if not test_tcp_connection(parsed_url.hostname, parsed_url.port or 5432):
            print("💡 Posibles soluciones TCP:")
            print("  - Verificar firewall local")
            print("  - Verificar proxy corporativo")
            print("  - Verificar que Supabase esté activo")
            all_tests_passed = False
        print()
        
        # 4. Probar PostgreSQL solo si TCP funciona
        print("4️⃣ CONEXIÓN POSTGRESQL")
        print("-" * 30)
        if not test_postgres_connection():
            print("💡 Posibles soluciones PostgreSQL:")
            print("  - Verificar credenciales (usuario/contraseña)")
            print("  - Verificar nombre de base de datos")
            print("  - Verificar permisos en Supabase")
            print("  - Revisar logs en dashboard de Supabase")
            all_tests_passed = False
        print()
    
    # Resumen final
    print("📋 RESUMEN")
    print("=" * 50)
    if all_tests_passed:
        print("🎉 ¡Todos los tests pasaron! La conexión debería funcionar.")
        print("💡 Si init_db.py aún falla, puede ser un problema temporal.")
    else:
        print("⚠️ Se encontraron problemas. Revisa las soluciones sugeridas.")
        print("🔗 Enlaces útiles:")
        print("  - Dashboard Supabase: https://app.supabase.com")
        print("  - Documentación: https://supabase.com/docs")
    
    return all_tests_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)