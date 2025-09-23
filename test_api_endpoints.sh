#!/bin/bash
# test_api_endpoints.sh - Script para probar endpoints específicos

API_BASE="http://localhost"
if [ ! -z "$1" ]; then
    API_BASE="http://$1"
fi

echo "🔧 Probando endpoints de la API en: $API_BASE"
echo "================================================"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_test() {
    echo -e "\n${YELLOW}🧪 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Health check
print_test "Health Check"
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -c 4)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -c -4)

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Health check: $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
else
    print_error "Health check failed: $HTTP_CODE"
fi

# 2. Probar endpoints de rooms SIN autenticación (para ver si hay redirects)
print_test "Rooms endpoint (sin auth) - Verificar redirects"

# Probar /api/rooms/ (con slash final)
ROOMS_SLASH_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/api/rooms/")
HTTP_CODE_SLASH=$(echo "$ROOMS_SLASH_RESPONSE" | tail -c 4)

echo "GET /api/rooms/ -> HTTP $HTTP_CODE_SLASH"

# Probar /api/rooms (sin slash final)
ROOMS_NO_SLASH_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/api/rooms")
HTTP_CODE_NO_SLASH=$(echo "$ROOMS_NO_SLASH_RESPONSE" | tail -c 4)

echo "GET /api/rooms -> HTTP $HTTP_CODE_NO_SLASH"

if [ "$HTTP_CODE_SLASH" = "401" ] && [ "$HTTP_CODE_NO_SLASH" = "401" ]; then
    print_success "No hay redirects 307 - ambos devuelven 401 (sin auth)"
elif [ "$HTTP_CODE_SLASH" = "307" ] || [ "$HTTP_CODE_NO_SLASH" = "307" ]; then
    print_error "Aún hay redirects 307"
else
    print_success "Códigos: /api/rooms/ = $HTTP_CODE_SLASH, /api/rooms = $HTTP_CODE_NO_SLASH"
fi

# 3. Probar OPTIONS requests (CORS)
print_test "CORS OPTIONS request"
OPTIONS_RESPONSE=$(curl -s -w "%{http_code}" -X OPTIONS \
    -H "Origin: http://localhost:4200" \
    -H "Access-Control-Request-Method: GET" \
    "$API_BASE/api/rooms/")

HTTP_CODE_OPTIONS=$(echo "$OPTIONS_RESPONSE" | tail -c 4)
RESPONSE_OPTIONS=$(echo "$OPTIONS_RESPONSE" | head -c -4)

if [ "$HTTP_CODE_OPTIONS" = "200" ]; then
    print_success "OPTIONS request: $HTTP_CODE_OPTIONS"
else
    print_error "OPTIONS request failed: $HTTP_CODE_OPTIONS"
fi

# 4. Probar documentación
print_test "API Documentation"
DOCS_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/docs")
HTTP_CODE_DOCS=$(echo "$DOCS_RESPONSE" | tail -c 4)

if [ "$HTTP_CODE_DOCS" = "200" ]; then
    print_success "Docs disponibles: $API_BASE/docs"
else
    print_error "Docs no disponibles: $HTTP_CODE_DOCS"
fi

# 5. Probar registro de usuario (para obtener token)
print_test "User Registration"
USER_DATA='{
    "username": "testuser_'$(date +%s)'",
    "email": "test'$(date +%s)'@example.com",
    "password": "testpass123"
}'

REG_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_BASE/api/users/register" \
    -H "Content-Type: application/json" \
    -d "$USER_DATA")

HTTP_CODE_REG=$(echo "$REG_RESPONSE" | tail -c 4)
RESPONSE_REG=$(echo "$REG_RESPONSE" | head -c -4)

if [ "$HTTP_CODE_REG" = "201" ] || [ "$HTTP_CODE_REG" = "200" ]; then
    print_success "User registration: $HTTP_CODE_REG"
    
    # Extraer username para login
    USERNAME=$(echo "$USER_DATA" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    
    # 6. Login para obtener token
    print_test "User Login"
    LOGIN_DATA='{
        "username": "'$USERNAME'",
        "password": "testpass123"
    }'
    
    LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/users/login" \
        -H "Content-Type: application/json" \
        -d "$LOGIN_DATA")
    
    TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$TOKEN" ]; then
        print_success "Login successful, token obtained"
        
        # 7. Probar endpoints con autenticación
        print_test "Authenticated Rooms Request"
        
        AUTH_ROOMS_RESPONSE=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $TOKEN" \
            "$API_BASE/api/rooms/")
        
        HTTP_CODE_AUTH=$(echo "$AUTH_ROOMS_RESPONSE" | tail -c 4)
        
        if [ "$HTTP_CODE_AUTH" = "200" ]; then
            print_success "Authenticated rooms request: $HTTP_CODE_AUTH"
        else
            print_error "Authenticated rooms request failed: $HTTP_CODE_AUTH"
        fi
        
    else
        print_error "Login failed - no token received"
    fi
    
else
    print_error "User registration failed: $HTTP_CODE_REG"
    echo "Response: $RESPONSE_REG"
fi

echo
echo "================================================"
echo "🏁 Pruebas completadas"
echo
echo "📋 URLs importantes:"
echo "   - Health: $API_BASE/health"
echo "   - Docs: $API_BASE/docs"
echo "   - Rooms: $API_BASE/api/rooms/"
echo "   - Register: $API_BASE/api/users/register"
echo "   - Login: $API_BASE/api/users/login"