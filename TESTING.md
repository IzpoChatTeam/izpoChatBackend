# IzpoChat API - Configuración de Pruebas

## 🌐 CORS Configurado para Desarrollo

Tu API ahora está configurada con **CORS completamente abierto** para facilitar las pruebas desde cualquier origen:

### ✅ Configuración Aplicada:

- **Orígenes permitidos**: `*` (cualquier dominio)
- **Métodos permitidos**: `GET, POST, PUT, DELETE, PATCH, OPTIONS`
- **Headers permitidos**: `*` (todos)
- **Credenciales**: Habilitadas
- **Rate limiting**: Más permisivo (30 req/s en API, 15 req/s en WebSocket)

## 🧪 Cómo Probar la API

### 1. **Desde cualquier navegador (JavaScript):**

```javascript
// Probar endpoint de salud
fetch('http://YOUR_VM_IP/health')
  .then(response => response.json())
  .then(data => console.log(data));

// Registrar usuario
fetch('http://YOUR_VM_IP/api/users/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'testuser',
    email: 'test@example.com',
    password: 'testpassword123'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// WebSocket (después de autenticarte)
const ws = new WebSocket('ws://YOUR_VM_IP/api/ws/room1');
ws.onmessage = function(event) {
    console.log('Mensaje recibido:', event.data);
};
```

### 2. **Desde Postman/Insomnia:**

- **Base URL**: `http://YOUR_VM_IP`
- **No necesitas configurar headers CORS especiales**
- **Todos los endpoints están disponibles**

### 3. **Desde curl (terminal):**

```bash
# Health check
curl http://YOUR_VM_IP/health

# Registrar usuario
curl -X POST http://YOUR_VM_IP/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'

# Login
curl -X POST http://YOUR_VM_IP/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'
```

### 4. **Desde aplicaciones frontend locales:**

- **React** (localhost:3000): ✅ Funcionará
- **Vue** (localhost:8080): ✅ Funcionará  
- **Angular** (localhost:4200): ✅ Funcionará
- **HTML simple** (file://): ✅ Funcionará

## 📱 Frontend de Prueba Rápido

Si quieres una interfaz web simple para probar, puedes crear este archivo HTML:

```html
<!DOCTYPE html>
<html>
<head>
    <title>IzpoChat Test</title>
</head>
<body>
    <h1>IzpoChat API Test</h1>
    <button onclick="testAPI()">Test Health</button>
    <button onclick="testRegister()">Test Register</button>
    <div id="results"></div>

    <script>
        const API_BASE = 'http://YOUR_VM_IP';
        
        async function testAPI() {
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();
                document.getElementById('results').innerHTML = 
                    `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function testRegister() {
            try {
                const response = await fetch(`${API_BASE}/api/users/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        username: 'testuser' + Date.now(),
                        email: 'test' + Date.now() + '@example.com',
                        password: 'test123'
                    })
                });
                const data = await response.json();
                document.getElementById('results').innerHTML = 
                    `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                console.error('Error:', error);
            }
        }
    </script>
</body>
</html>
```

## 🔒 Nota de Seguridad

**Esta configuración es para desarrollo/ejercicio únicamente.** 

Para producción real deberías:
- Especificar dominios exactos en `ALLOWED_ORIGINS`
- Configurar rate limiting más estricto
- Implementar autenticación adicional
- Usar HTTPS

## 🚀 Despliegue

Una vez que hagas los cambios, simplemente redespliega:

```bash
# En tu VM
docker-compose down
docker-compose build
docker-compose up -d
```

¡Ahora tu API aceptará conexiones desde cualquier origen! 🌍