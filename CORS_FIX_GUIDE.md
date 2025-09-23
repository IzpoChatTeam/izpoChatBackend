# 🚀 Guía de Aplicación CORS Fix

## ✅ Cambios Realizados

### 1. **Archivos Eliminados:**
- ❌ `test_cors.sh`
- ❌ `test_api_endpoints.sh` 
- ❌ `test_chat_functionality.sh`

### 2. **Configuración CORS Mejorada:**
```python
# Orígenes específicos para Angular
allow_origins=[
    "http://localhost:4200",
    "http://127.0.0.1:4200", 
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Fallback
]

# Headers específicos para WebSocket
allow_headers=[
    "Accept", "Content-Type", "Authorization",
    "X-Requested-With", "Origin", "Cache-Control",
    "Sec-WebSocket-Extensions", "Sec-WebSocket-Key",
    "Sec-WebSocket-Protocol", "Sec-WebSocket-Version",
    "Upgrade", "Connection"
]
```

### 3. **Middleware Personalizado:**
- Headers adicionales para WebSocket
- Manejo específico de conexiones `upgrade`

### 4. **Endpoint OPTIONS:**
- Maneja preflight requests automáticamente
- Respuesta optimizada para Angular

### 5. **Endpoint `/cors-test` Mejorado:**
- Información detallada de debugging
- Validación específica para Angular

## 🔧 Aplicar en VM (34.72.14.164)

### Paso 1: Actualizar código
```bash
cd /path/to/izpoChatBackend
git pull origin main
```

### Paso 2: Rebuilding containers
```bash
# Parar containers
docker-compose down

# Rebuild con cambios
docker-compose up -d --build

# Verificar estado
docker-compose ps
```

### Paso 3: Verificar funcionamiento
```bash
# Test básico
curl http://localhost/health

# Test CORS mejorado
curl -H "Origin: http://localhost:4200" http://localhost/cors-test

# Test preflight OPTIONS
curl -X OPTIONS \
  -H "Origin: http://localhost:4200" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type" \
  http://localhost/api/rooms/
```

## 🧪 Probar desde Angular

### En tu aplicación Angular:

#### 1. **Service Configuration:**
```typescript
// En tu service Angular
@Injectable()
export class ChatService {
  private apiUrl = 'http://34.72.14.164';  // IP de tu VM
  private wsUrl = 'ws://34.72.14.164';     // WebSocket URL
  
  constructor(private http: HttpClient) {}
  
  // Test conexión básica
  testConnection() {
    return this.http.get(`${this.apiUrl}/cors-test`);
  }
  
  // Test rooms endpoint
  getRooms() {
    return this.http.get(`${this.apiUrl}/api/rooms/`);
  }
  
  // WebSocket connection
  connectToRoom(roomId: number, token: string) {
    return new WebSocket(`${this.wsUrl}/api/ws/${roomId}?token=${token}`);
  }
}
```

#### 2. **Component Test:**
```typescript
// En tu componente
ngOnInit() {
  // Test 1: CORS básico
  this.chatService.testConnection().subscribe({
    next: (data) => {
      console.log('✅ CORS Test exitoso:', data);
      // Test 2: Endpoints de rooms
      this.testRoomsEndpoint();
    },
    error: (error) => {
      console.error('❌ Error CORS:', error);
    }
  });
}

testRoomsEndpoint() {
  this.chatService.getRooms().subscribe({
    next: (rooms) => {
      console.log('✅ Rooms endpoint funciona:', rooms);
    },
    error: (error) => {
      console.log('⚠️ Rooms error (normal sin auth):', error.status);
      if (error.status === 401) {
        console.log('✅ Endpoint funciona, solo necesita autenticación');
      }
    }
  });
}

// Test WebSocket (después de login)
testWebSocket(roomId: number, token: string) {
  const ws = this.chatService.connectToRoom(roomId, token);
  
  ws.onopen = () => {
    console.log('✅ WebSocket conectado a sala', roomId);
  };
  
  ws.onerror = (error) => {
    console.error('❌ Error WebSocket:', error);
  };
  
  ws.onmessage = (event) => {
    console.log('📨 Mensaje recibido:', JSON.parse(event.data));
  };
}
```

#### 3. **Console Quick Test:**
```javascript
// En la consola del navegador Angular (F12)
// Test 1: CORS básico
fetch('http://34.72.14.164/cors-test')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

// Test 2: Preflight OPTIONS
fetch('http://34.72.14.164/api/rooms/', {
  method: 'OPTIONS',
  headers: {
    'Origin': 'http://localhost:4200',
    'Access-Control-Request-Method': 'GET'
  }
}).then(console.log).catch(console.error);
```

## 🎯 Endpoints para tu Presentación

### URLs principales:
```
Base API:     http://34.72.14.164
Health:       http://34.72.14.164/health
CORS Test:    http://34.72.14.164/cors-test
Docs:         http://34.72.14.164/docs
Rooms:        http://34.72.14.164/api/rooms/
WebSocket:    ws://34.72.14.164/api/ws/{room_id}?token={jwt_token}
```

### Flujo completo para demo:
1. **Registrar usuario:** `POST /api/users/`
2. **Login:** `POST /api/auth/login`
3. **Crear sala:** `POST /api/rooms/`
4. **Conectar WebSocket:** `ws://34.72.14.164/api/ws/{room_id}?token={token}`
5. **Enviar mensaje:** Enviar JSON por WebSocket
6. **Recibir mensajes:** Escuchar eventos WebSocket

## 🔍 Troubleshooting

### Si sigue dando error CORS:
```bash
# En la VM, verificar logs
docker-compose logs app

# Restart completo
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Si Angular no conecta:
1. Verificar URL exacta: `http://34.72.14.164` (sin puerto)
2. Verificar que VM esté corriendo: `docker-compose ps`
3. Verificar CORS test: `curl http://34.72.14.164/cors-test`
4. Verificar consola del navegador para errores específicos

## ✅ Checklist Final

- [ ] `git pull origin main` en VM ejecutado
- [ ] `docker-compose up -d --build` completado
- [ ] `curl http://34.72.14.164/health` retorna 200
- [ ] `curl http://34.72.14.164/cors-test` retorna datos detallados
- [ ] Fetch desde Angular console funciona sin errores
- [ ] WebSocket puede conectar desde Angular
- [ ] Mensajes se envían y reciben correctamente

🎉 **¡Listo para la presentación!**