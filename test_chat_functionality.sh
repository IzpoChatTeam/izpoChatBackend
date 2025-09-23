#!/bin/bash
# test_chat_functionality.sh - Script para probar funcionalidad completa del chat

set -e

API_BASE="http://localhost"
if [ ! -z "$1" ]; then
    API_BASE="http://$1"
fi

echo "🧪 Probando funcionalidad completa del chat API en: $API_BASE"
echo "=================================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Variables para almacenar tokens y datos
USER1_TOKEN=""
USER2_TOKEN=""
ROOM_ID=""

# 1. Probar health check
echo
print_info "1. Probando health check..."
HEALTH_RESPONSE=$(curl -s "$API_BASE/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "Health check OK"
else
    print_error "Health check falló"
    exit 1
fi

# 2. Registrar usuarios de prueba
echo
print_info "2. Registrando usuarios de prueba..."

# Usuario 1
USER1_DATA='{
    "username": "testuser1",
    "email": "test1@example.com",
    "password": "testpass123"
}'

USER1_RESPONSE=$(curl -s -X POST "$API_BASE/api/users/register" \
    -H "Content-Type: application/json" \
    -d "$USER1_DATA")

if echo "$USER1_RESPONSE" | grep -q "testuser1"; then
    print_success "Usuario 1 registrado"
else
    print_info "Usuario 1 ya existe o error en registro"
fi

# Usuario 2
USER2_DATA='{
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "testpass123"
}'

USER2_RESPONSE=$(curl -s -X POST "$API_BASE/api/users/register" \
    -H "Content-Type: application/json" \
    -d "$USER2_DATA")

if echo "$USER2_RESPONSE" | grep -q "testuser2"; then
    print_success "Usuario 2 registrado"
else
    print_info "Usuario 2 ya existe o error en registro"
fi

# 3. Login usuarios
echo
print_info "3. Iniciando sesión con usuarios..."

# Login Usuario 1
LOGIN1_DATA='{
    "username": "testuser1",
    "password": "testpass123"
}'

LOGIN1_RESPONSE=$(curl -s -X POST "$API_BASE/api/users/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN1_DATA")

USER1_TOKEN=$(echo "$LOGIN1_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$USER1_TOKEN" ]; then
    print_success "Usuario 1 loggeado"
else
    print_error "Error en login Usuario 1"
    echo "Response: $LOGIN1_RESPONSE"
    exit 1
fi

# Login Usuario 2
LOGIN2_DATA='{
    "username": "testuser2",
    "password": "testpass123"
}'

LOGIN2_RESPONSE=$(curl -s -X POST "$API_BASE/api/users/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN2_DATA")

USER2_TOKEN=$(echo "$LOGIN2_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ ! -z "$USER2_TOKEN" ]; then
    print_success "Usuario 2 loggeado"
else
    print_error "Error en login Usuario 2"
    echo "Response: $LOGIN2_RESPONSE"
    exit 1
fi

# 4. Crear sala
echo
print_info "4. Creando sala de prueba..."

ROOM_DATA='{
    "name": "Sala de Prueba",
    "description": "Sala para probar funcionalidad",
    "is_public": true
}'

ROOM_RESPONSE=$(curl -s -X POST "$API_BASE/api/rooms/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -d "$ROOM_DATA")

ROOM_ID=$(echo "$ROOM_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ ! -z "$ROOM_ID" ]; then
    print_success "Sala creada con ID: $ROOM_ID"
else
    print_error "Error creando sala"
    echo "Response: $ROOM_RESPONSE"
    exit 1
fi

# 5. Unir usuarios a la sala
echo
print_info "5. Uniendo usuarios a la sala..."

# Usuario 2 se une a la sala
JOIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/rooms/$ROOM_ID/join" \
    -H "Authorization: Bearer $USER2_TOKEN")

if echo "$JOIN_RESPONSE" | grep -q "exitosamente"; then
    print_success "Usuario 2 se unió a la sala"
else
    print_error "Error uniendo Usuario 2 a la sala"
    echo "Response: $JOIN_RESPONSE"
fi

# 6. Obtener salas
echo
print_info "6. Obteniendo lista de salas..."

ROOMS_RESPONSE=$(curl -s -X GET "$API_BASE/api/rooms/" \
    -H "Authorization: Bearer $USER1_TOKEN")

if echo "$ROOMS_RESPONSE" | grep -q "Sala de Prueba"; then
    print_success "Lista de salas obtenida correctamente"
else
    print_error "Error obteniendo salas"
    echo "Response: $ROOMS_RESPONSE"
fi

# 7. Enviar mensaje
echo
print_info "7. Enviando mensaje de prueba..."

MESSAGE_DATA='{
    "content": "¡Hola! Este es un mensaje de prueba",
    "room_id": '$ROOM_ID'
}'

MESSAGE_RESPONSE=$(curl -s -X POST "$API_BASE/api/rooms/$ROOM_ID/messages" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $USER1_TOKEN" \
    -d "$MESSAGE_DATA")

if echo "$MESSAGE_RESPONSE" | grep -q "mensaje de prueba"; then
    print_success "Mensaje enviado correctamente"
else
    print_error "Error enviando mensaje"
    echo "Response: $MESSAGE_RESPONSE"
fi

# 8. Obtener mensajes
echo
print_info "8. Obteniendo mensajes de la sala..."

MESSAGES_RESPONSE=$(curl -s -X GET "$API_BASE/api/rooms/$ROOM_ID/messages" \
    -H "Authorization: Bearer $USER2_TOKEN")

if echo "$MESSAGES_RESPONSE" | grep -q "mensaje de prueba"; then
    print_success "Mensajes obtenidos correctamente"
else
    print_error "Error obteniendo mensajes"
    echo "Response: $MESSAGES_RESPONSE"
fi

# 9. Probar endpoint específico de room
echo
print_info "9. Probando endpoint específico de sala..."

ROOM_INFO_RESPONSE=$(curl -s -X GET "$API_BASE/api/rooms/$ROOM_ID" \
    -H "Authorization: Bearer $USER1_TOKEN")

if echo "$ROOM_INFO_RESPONSE" | grep -q "Sala de Prueba"; then
    print_success "Información de sala obtenida"
else
    print_error "Error obteniendo información de sala"
    echo "Response: $ROOM_INFO_RESPONSE"
fi

echo
echo "=================================================="
print_success "🎉 Todas las pruebas completadas exitosamente!"
echo
print_info "Puedes probar WebSockets conectándote a:"
echo "   ws://$API_BASE/api/ws/$ROOM_ID?token=$USER1_TOKEN"
echo
print_info "Endpoints disponibles:"
echo "   - API Docs: $API_BASE/docs"
echo "   - Health: $API_BASE/health"
echo "   - Salas: $API_BASE/api/rooms/"
echo "   - Mensajes: $API_BASE/api/rooms/$ROOM_ID/messages"