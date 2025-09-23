# 🎓 Guía para Presentación en Clase - IzpoChat

## 📋 Resumen del Proyecto

**IzpoChat** es una aplicación de chat en tiempo real con las siguientes características:

✅ **Chat persona a persona** con WebSockets
✅ **Envío de documentos** (PDF, imágenes, Word, etc.)
✅ **Base de datos PostgreSQL** (Supabase)
✅ **Almacenamiento de archivos** (Supabase Storage)
✅ **Autenticación JWT** 
✅ **API REST** completa

## 🚀 Demostración en Vivo

### 1. **Iniciar servidor local**
```bash
python run.py
```
Servidor corre en: `http://127.0.0.1:5000`

### 2. **Endpoints principales**
```http
POST /api/users/register  # Registrar usuario
POST /api/users/login     # Login  
GET  /api/rooms          # Ver salas
POST /api/rooms          # Crear sala
POST /api/upload         # Subir archivo
WebSocket: /socket.io/   # Chat en tiempo real
```

### 3. **Flujo de demostración**

#### Paso 1: Registrar usuarios
```bash
# Usuario 1
curl -X POST http://127.0.0.1:5000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "profesor",
    "email": "profesor@clase.com",
    "password": "123456",
    "full_name": "Profesor Demo"
  }'
```

#### Paso 2: Login y obtener token
```bash
curl -X POST http://127.0.0.1:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "profesor@clase.com",
    "password": "123456"
  }'
```

#### Paso 3: Crear sala de chat
```bash
curl -X POST http://127.0.0.1:5000/api/rooms \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Clase de Programación",
    "description": "Sala para la clase"
  }'
```

#### Paso 4: Subir archivo
```bash
curl -X POST http://127.0.0.1:5000/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@documento.pdf" \
  -F "room_id=1"
```

## 🔧 Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Base de datos**: PostgreSQL (Supabase) 
- **Storage**: Supabase Storage
- **WebSockets**: Flask-SocketIO
- **Autenticación**: JWT tokens
- **ORM**: SQLAlchemy

## 📊 Arquitectura

```
Frontend (Angular) ←→ Flask API ←→ PostgreSQL (Supabase)
                   ↕
               WebSocket Chat
                   ↕
            Supabase Storage (Archivos)
```

## 🎯 Características Técnicas

### Chat en Tiempo Real
- WebSocket connection para mensajería instantánea
- Salas públicas y privadas
- Tracking de usuarios conectados
- Historial persistente de mensajes

### Upload de Archivos
- Integración con Supabase Storage
- Soporte para documentos, imágenes
- URLs públicas para archivos
- Validación de tipos y tamaños

### Seguridad
- Autenticación JWT
- Hashing de passwords con bcrypt
- Validación de tokens en todos los endpoints
- CORS configurado para desarrollo y producción

## 🚀 Despliegue

**Para producción**: Listo para desplegar en Render.com
- Build: `./build.sh`
- Start: `python run.py`
- Variables de entorno configuradas
- Base de datos PostgreSQL incluida

## 📱 Funcionalidades Demonstradas

1. **Registro de usuarios**
2. **Login con JWT**
3. **Creación de salas**
4. **Chat en tiempo real**
5. **Envío de archivos**
6. **Persistencia de mensajes**
7. **Descarga de archivos compartidos**

---

### 🏆 **Proyecto completo y funcional**
- ✅ **Código limpio y organizado**
- ✅ **Base de datos en la nube**
- ✅ **Storage de archivos**
- ✅ **WebSockets funcionando**
- ✅ **API REST completa**
- ✅ **Listo para producción**