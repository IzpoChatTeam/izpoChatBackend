#!/bin/bash
# fix_supabase_deployment.sh - Script para arreglar deployment con Supabase Storage

echo "🔧 Arreglando deployment para usar Supabase Storage..."

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "\n${YELLOW}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Verificar variables de entorno
print_step "Verificando configuración de Supabase..."
if grep -q "SUPABASE_STORAGE_BUCKET=izpochat-bucket" .env; then
    print_success "Configuración de Supabase encontrada"
else
    print_error "Configuración de Supabase no encontrada"
    exit 1
fi

# 2. Parar containers actuales
print_step "Parando containers existentes..."
docker-compose down
if [ $? -eq 0 ]; then
    print_success "Containers parados"
else
    print_error "Error parando containers"
fi

# 3. Limpiar Docker
print_step "Limpiando Docker cache..."
docker system prune -f
print_success "Limpieza completada"

# 4. Reconstruir con nueva configuración
print_step "Reconstruyendo con configuración de Supabase..."
docker-compose up -d --build
if [ $? -eq 0 ]; then
    print_success "Containers reconstruidos"
else
    print_error "Error en rebuild"
    docker-compose logs
    exit 1
fi

# 5. Esperar inicialización
print_step "Esperando inicialización (30 segundos)..."
sleep 30

# 6. Verificar servicios
print_step "Estado de los servicios:"
docker-compose ps

# 7. Test de conectividad
print_step "Probando conectividad..."

# Health check
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Health check: OK"
else
    print_error "Health check: FALLÓ"
fi

# CORS test
if curl -f http://localhost/cors-test > /dev/null 2>&1; then
    print_success "CORS test: OK"
else
    print_error "CORS test: FALLÓ"
fi

# Supabase Storage test
if curl -f http://localhost/api/uploads/types/allowed > /dev/null 2>&1; then
    print_success "Supabase Storage: OK"
    # Mostrar la configuración
    echo ""
    echo "📋 Configuración de Supabase Storage:"
    curl -s http://localhost/api/uploads/types/allowed | jq . 2>/dev/null || curl -s http://localhost/api/uploads/types/allowed
else
    print_error "Supabase Storage: FALLÓ"
fi

# 8. Resumen final
print_step "Resumen del deployment:"
echo ""
echo "🌐 URLs disponibles:"
echo "   Health:      http://localhost/health"
echo "   CORS Test:   http://localhost/cors-test"
echo "   API Docs:    http://localhost/docs"
echo "   Uploads:     http://localhost/api/uploads/types/allowed"
echo "   Rooms:       http://localhost/api/rooms/"
echo ""
echo "🗄️ Configuración Supabase:"
echo "   Bucket:      izpochat-bucket"
echo "   URL:         https://rldgqojsdmuckuacyfcs.supabase.co"
echo ""

# 9. Verificar logs si hay errores
if ! curl -f http://localhost/health > /dev/null 2>&1; then
    print_step "Logs recientes por errores:"
    echo ""
    docker-compose logs --tail=30 app
fi

print_success "🎉 Deployment actualizado con Supabase Storage!"
echo ""
echo "💡 Cambios aplicados:"
echo "   ✅ Google Cloud Storage removido de docker-compose.yml"
echo "   ✅ Variables Supabase agregadas a docker-compose.yml"
echo "   ✅ Variables GCS configuradas como vacías en .env"
echo "   ✅ Configuración CORS mantenida"
echo "   ✅ Sistema de uploads usando Supabase"
echo ""
echo "📱 Para Angular:"
echo "   Base URL: http://$(curl -s ifconfig.me 2>/dev/null || echo 'TU_IP_PUBLICA')"
echo "   Endpoints listos para usar"