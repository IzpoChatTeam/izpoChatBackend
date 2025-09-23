#!/bin/bash
# fix_deployment.sh - Script para aplicar correcciones y redesplegar

echo "🔧 Aplicando correcciones críticas para IzpoChat..."

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌]${NC} $1"
}

# 1. Detener servicios actuales
print_status "Deteniendo servicios actuales..."
docker-compose down

# 2. Limpiar imágenes y contenedores antiguos
print_status "Limpiando contenedores e imágenes anteriores..."
docker system prune -f

# 3. Reconstruir desde cero
print_status "Reconstruyendo aplicación desde cero..."
docker-compose build --no-cache

# 4. Verificar que el archivo .env existe
if [ ! -f .env ]; then
    print_warning "Archivo .env no encontrado. Copiando desde .env.production..."
    cp .env.production .env
fi

# 5. Iniciar servicios
print_status "Iniciando servicios..."
docker-compose up -d

# 6. Esperar a que los servicios estén listos
print_status "Esperando a que los servicios estén listos..."
sleep 30

# 7. Verificar estado de los servicios
print_status "Verificando estado de los servicios..."
docker-compose ps

# 8. Verificar logs para errores
print_status "Verificando logs de la aplicación..."
docker-compose logs --tail=20 app

# 9. Probar endpoints básicos
print_status "Probando endpoints básicos..."

# Health check
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" http://localhost/health)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -c 4)

if [ "$HTTP_CODE" = "200" ]; then
    print_status "Health check: OK (200)"
else
    print_error "Health check: FAILED ($HTTP_CODE)"
fi

# Probar rooms sin redirect
ROOMS_RESPONSE=$(curl -s -w "%{http_code}" http://localhost/api/rooms/)
HTTP_CODE_ROOMS=$(echo "$ROOMS_RESPONSE" | tail -c 4)

if [ "$HTTP_CODE_ROOMS" = "401" ]; then
    print_status "Rooms endpoint: OK (401 - sin auth)"
elif [ "$HTTP_CODE_ROOMS" = "307" ]; then
    print_error "Rooms endpoint: REDIRECT 307 - AÚN HAY PROBLEMA"
else
    print_status "Rooms endpoint: $HTTP_CODE_ROOMS"
fi

# 10. Mostrar información final
echo
echo "================================================"
print_status "Despliegue completado"
echo
echo "📊 Información del despliegue:"
echo "  - Health Check: http://localhost/health"
echo "  - API Docs: http://localhost/docs"
echo "  - Rooms: http://localhost/api/rooms/"
echo
echo "🔍 Para ver logs en tiempo real:"
echo "  docker-compose logs -f app"
echo
echo "🧪 Para probar la API:"
echo "  ./test_api_endpoints.sh"
echo "================================================"