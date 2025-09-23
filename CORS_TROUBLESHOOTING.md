# 🔧 CORS Troubleshooting Guide

## ❌ Problema Actual
Angular frontend no puede conectar al API debido a errores de CORS:
```
Failed to fetch
HttpErrorResponse status: 0
```

## ✅ Soluciones Implementadas

### 1. **Configuración CORS Permisiva**
```python
# En chat_app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ✅ Permite todos los orígenes
    allow_credentials=True,       # ✅ Permite cookies/auth
    allow_methods=["*"],         # ✅ Permite todos los métodos
    allow_headers=["*"],         # ✅ Permite todos los headers
)
```

### 2. **Endpoint de Debug CORS**
```python
@app.get("/cors-test")
async def cors_test():
    return {
        "message": "CORS working correctly",
        "timestamp": datetime.utcnow(),
        "cors_config": {
            "allow_origins": "*",
            "allow_credentials": True,
            "allow_methods": "*",
            "allow_headers": "*"
        }
    }
```

### 3. **Deshabilitado Redirect Slashes**
```python
app = FastAPI(
    title="IzpoChat API",
    redirect_slashes=False  # ✅ Evita 307 redirects
)
```

## 🚀 Pasos para Aplicar los Cambios

### En la VM (34.72.14.164):
```bash
# 1. Actualizar código
git pull origin main

# 2. Aplicar cambios con script automático
chmod +x fix_deployment.sh
./fix_deployment.sh

# 3. Verificar que todo esté funcionando
docker-compose ps
curl http://localhost/health
curl http://localhost/cors-test
```

### En tu Angular (localhost:4200):
```typescript
// Asegúrate de usar la URL correcta
const apiUrl = 'http://34.72.14.164';  // SIN puerto, SIN trailing slash

// Ejemplo de servicio
@Injectable()
export class ApiService {
  private apiUrl = 'http://34.72.14.164';
  
  constructor(private http: HttpClient) {}
  
  // Test básico
  testConnection() {
    return this.http.get(`${this.apiUrl}/health`);
  }
  
  // Test CORS específico
  testCors() {
    return this.http.get(`${this.apiUrl}/cors-test`);
  }
}
```

## 🧪 Cómo Probar

### 1. **Desde terminal:**
```bash
# Usar el script de pruebas
chmod +x test_cors.sh
./test_cors.sh 34.72.14.164
```

### 2. **Desde navegador:**
```javascript
// Console del navegador
fetch('http://34.72.14.164/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);

fetch('http://34.72.14.164/cors-test')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

### 3. **Desde Angular:**
```typescript
// En tu componente
ngOnInit() {
  // Test de conexión
  this.http.get('http://34.72.14.164/health').subscribe({
    next: (data) => console.log('✅ API conectado:', data),
    error: (error) => console.error('❌ Error CORS:', error)
  });
}
```

## 🔍 Debugging Común

### Error: "Failed to fetch"
- **Causa:** CORS bloqueado por navegador
- **Solución:** Verificar configuración CORS en main.py

### Error: Status 0
- **Causa:** Request bloqueado antes de llegar al servidor
- **Solución:** Verificar URL, CORS headers, y red

### Error: 307 Temporary Redirect
- **Causa:** FastAPI redirect automático
- **Solución:** `redirect_slashes=False` (ya implementado)

### Error: 401 Unauthorized
- **Causa:** Endpoint requiere autenticación
- **Solución:** Normal para endpoints protegidos, usar login primero

## 📋 Checklist de Verificación

- [ ] `git pull origin main` en VM
- [ ] `./fix_deployment.sh` ejecutado
- [ ] `docker-compose ps` muestra todos los servicios running
- [ ] `curl http://34.72.14.164/health` retorna 200
- [ ] `curl http://34.72.14.164/cors-test` retorna 200
- [ ] Navegador puede hacer fetch a los endpoints
- [ ] Angular puede conectar sin errores CORS

## 🎯 URLs para tu Presentación

### API Base:
```
http://34.72.14.164
```

### Endpoints de prueba:
```
GET  /health           - Health check
GET  /cors-test        - Test CORS
GET  /docs             - Swagger UI
POST /api/users/       - Crear usuario
POST /api/auth/login   - Login
GET  /api/rooms/       - Listar salas
```

### Postman Collection:
- Ya configurada para usar `34.72.14.164`
- 14 requests automatizados con validaciones
- Variables de entorno pre-configuradas

## ⚡ Comando Rápido de Emergencia

Si todo falla, reinicio completo:
```bash
# En la VM
docker-compose down
git pull origin main
docker-compose up -d --build
```

## 📞 Status Check

Para verificar que todo está funcionando:
```bash
echo "🔍 Checking API status..."
curl -s http://34.72.14.164/health | jq '.'
echo -e "\n🔍 Checking CORS..."
curl -s http://34.72.14.164/cors-test | jq '.'
echo -e "\n🔍 Checking Docker containers..."
docker-compose ps
```