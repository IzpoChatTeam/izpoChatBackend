#!/bin/bash
# test_cors.sh - Script específico para probar CORS

API_BASE="http://localhost"
if [ ! -z "$1" ]; then
    API_BASE="http://$1"
fi

echo "🔍 Probando CORS en: $API_BASE"
echo "=================================================="

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

# 1. Probar health check básico
print_test "Health Check básico"
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -c 4)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -c -4)

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Health check: $HTTP_CODE"
else
    print_error "Health check failed: $HTTP_CODE"
fi

# 2. Probar CORS test endpoint
print_test "CORS Test Endpoint"
CORS_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/cors-test")
HTTP_CODE_CORS=$(echo "$CORS_RESPONSE" | tail -c 4)

if [ "$HTTP_CODE_CORS" = "200" ]; then
    print_success "CORS test: $HTTP_CODE_CORS"
else
    print_error "CORS test failed: $HTTP_CODE_CORS"
fi

# 3. Probar OPTIONS request (preflight)
print_test "OPTIONS Preflight Request"
OPTIONS_RESPONSE=$(curl -s -w "%{http_code}" -X OPTIONS \
    -H "Origin: http://localhost:4200" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type,Authorization" \
    "$API_BASE/api/rooms/" -v 2>&1)

echo "Options response:"
echo "$OPTIONS_RESPONSE"

# 4. Probar GET con Origin header
print_test "GET Request con Origin Header"
GET_RESPONSE=$(curl -s -w "%{http_code}" \
    -H "Origin: http://localhost:4200" \
    "$API_BASE/api/rooms/" -v 2>&1)

echo "GET response:"
echo "$GET_RESPONSE"

# 5. Probar usando JavaScript fetch simulation
print_test "Simulación de fetch desde navegador"
cat > /tmp/test_cors.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>CORS Test</title>
</head>
<body>
    <h1>CORS Test</h1>
    <button onclick="testCORS()">Test CORS</button>
    <div id="result"></div>

    <script>
        async function testCORS() {
            const apiBase = 'API_BASE_PLACEHOLDER';
            const resultDiv = document.getElementById('result');
            
            try {
                // Test 1: Health check
                const healthResponse = await fetch(apiBase + '/health');
                const healthData = await healthResponse.json();
                console.log('Health check:', healthData);
                
                // Test 2: CORS test
                const corsResponse = await fetch(apiBase + '/cors-test');
                const corsData = await corsResponse.json();
                console.log('CORS test:', corsData);
                
                // Test 3: Rooms (sin auth, debería dar 401)
                const roomsResponse = await fetch(apiBase + '/api/rooms/');
                console.log('Rooms response status:', roomsResponse.status);
                
                resultDiv.innerHTML = '<p style="color: green;">✅ CORS funcionando correctamente!</p>';
                
            } catch (error) {
                console.error('Error:', error);
                resultDiv.innerHTML = '<p style="color: red;">❌ Error de CORS: ' + error.message + '</p>';
            }
        }
    </script>
</body>
</html>
EOF

# Reemplazar placeholder
sed -i "s|API_BASE_PLACEHOLDER|$API_BASE|g" /tmp/test_cors.html

print_success "Archivo de prueba HTML creado en: /tmp/test_cors.html"
echo "Abre este archivo en tu navegador para probar CORS desde JavaScript"

# 6. Mostrar información de debugging
print_test "Información de debugging"
echo "API Base URL: $API_BASE"
echo "Endpoints a probar:"
echo "  - Health: $API_BASE/health"
echo "  - CORS Test: $API_BASE/cors-test"
echo "  - Rooms: $API_BASE/api/rooms/"
echo ""
echo "Headers CORS esperados:"
echo "  - Access-Control-Allow-Origin: *"
echo "  - Access-Control-Allow-Methods: *"
echo "  - Access-Control-Allow-Headers: *"
echo "  - Access-Control-Allow-Credentials: true"

echo ""
echo "=================================================="
print_success "🏁 Pruebas de CORS completadas"
echo ""
echo "💡 Para tu Angular, asegúrate de usar:"
echo "   const apiUrl = '$API_BASE';"
echo "   // Sin trailing slash en la base URL"