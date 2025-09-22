#!/bin/bash
# deploy.sh - Script de despliegue para Google Cloud VM

set -e

echo "🚀 Iniciando despliegue de IzpoChat Backend en Google Cloud VM..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Instalando Docker..."
    
    # Instalar Docker en Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER
    print_warning "Por favor, cierra sesión y vuelve a iniciar para que los cambios de Docker surtan efecto."
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose no está instalado. Instalando..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Verificar que el archivo .env existe
if [ ! -f .env ]; then
    print_warning "Archivo .env no encontrado. Copiando desde .env.production..."
    cp .env.production .env
    print_error "IMPORTANTE: Edita el archivo .env con tus configuraciones reales antes de continuar."
    print_error "Especialmente DATABASE_URL, SECRET_KEY, y otras credenciales."
    read -p "¿Has configurado el archivo .env? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Por favor configura el archivo .env y ejecuta el script nuevamente."
        exit 1
    fi
fi

# Crear directorios necesarios
print_status "Creando directorios necesarios..."
mkdir -p static/uploads
mkdir -p logs
mkdir -p ssl

# Crear archivo .gitkeep para uploads
touch static/uploads/.gitkeep

# Generar clave secreta si no existe
if ! grep -q "SECRET_KEY=tu-clave-secreta" .env; then
    print_status "Archivo .env ya está configurado."
else
    print_warning "Generando clave secreta aleatoria..."
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/SECRET_KEY=tu-clave-secreta-super-segura-de-64-caracteres-minimo-aqui/SECRET_KEY=${SECRET_KEY}/" .env
fi

# Construir y ejecutar contenedores
print_status "Construyendo imágenes Docker..."
docker-compose build

print_status "Iniciando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
print_status "Esperando a que los servicios estén listos..."
sleep 30

# Verificar que los servicios estén funcionando
print_status "Verificando estado de los servicios..."
docker-compose ps

# Ejecutar inicialización de base de datos
print_status "Inicializando base de datos..."
docker-compose exec app python init_db.py

# Mostrar información final
print_status "🎉 ¡Despliegue completado!"
echo
echo "📋 Información del despliegue:"
echo "  - API: http://localhost:8000"
echo "  - Documentación: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "  - Nginx: http://localhost (puerto 80)"
echo
echo "📊 Para ver logs:"
echo "  docker-compose logs -f app"
echo
echo "🔧 Para detener servicios:"
echo "  docker-compose down"
echo
echo "🔄 Para actualizar la aplicación:"
echo "  git pull && docker-compose build && docker-compose up -d"

print_status "Verificando conectividad..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_status "✅ API está respondiendo correctamente!"
else
    print_warning "⚠️ La API puede tardar unos minutos en estar lista."
fi