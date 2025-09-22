# 🚀 IzpoChat Backend

API backend para IzpoChat - Sistema de chat en tiempo real con soporte para archivos y documentos.

## ✨ Características

- 💬 **Chat en tiempo real** con WebSockets
- 📁 **Subida de archivos** con soporte para documentos, imágenes, audio y video
- 🔐 **Autenticación JWT** segura
- 🏠 **Salas públicas y privadas**
- 👥 **Gestión de usuarios** y miembros
- 🔍 **Historial de mensajes**
- ☁️ **Almacenamiento en Google Cloud Storage**
- 🗄️ **Base de datos PostgreSQL** (Supabase)

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **WebSockets** - Comunicación en tiempo real
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos (Supabase)
- **Google Cloud Storage** - Almacenamiento de archivos
- **JWT** - Autenticación y autorización
- **Pydantic** - Validación de datos

## 📋 Requisitos

- Python 3.11+
- Cuenta de Supabase (PostgreSQL)
- Cuenta de Google Cloud (para almacenamiento)
- Git

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd izpoChatBackend
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# Base de datos - Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.xxx.supabase.co:5432/postgres

# Seguridad JWT
SECRET_KEY=tu_secret_key_muy_seguro_cambia_esto_por_algo_unico
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Cloud Storage
GCS_BUCKET_NAME=tu-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]

# App
APP_NAME=IzpoChat API
DEBUG=true
```

### 5. Configurar Supabase

1. Ve a [Supabase](https://supabase.com) y crea un nuevo proyecto
2. Ve a Settings > Database y copia la cadena de conexión
3. Reemplaza `TU_PASSWORD` en `DATABASE_URL` con tu contraseña real

### 6. Configurar Google Cloud Storage

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Cloud Storage
4. Crea un bucket para almacenar archivos
5. Crea una cuenta de servicio y descarga el JSON de credenciales
6. Actualiza `GCS_BUCKET_NAME` y `GOOGLE_APPLICATION_CREDENTIALS` en `.env`

### 7. Inicializar la base de datos

```bash
python init_db.py
```

## 🏃‍♂️ Ejecutar el servidor

### Modo desarrollo

```bash
python run_dev.py
```

### Modo producción

```bash
uvicorn chat_app.main:app --host 0.0.0.0 --port 8000
```

## 📖 Documentación de la API

Una vez que el servidor esté ejecutándose, puedes acceder a:

- **Documentación interactiva**: http://localhost:8000/docs
- **Documentación alternativa**: http://localhost:8000/redoc

## 🔌 Endpoints principales

### Autenticación
- `POST /api/users/register` - Registrar nuevo usuario
- `POST /api/users/login` - Iniciar sesión
- `GET /api/users/me` - Información del usuario actual

### Salas de chat
- `GET /api/rooms/` - Listar salas públicas
- `POST /api/rooms/` - Crear nueva sala
- `GET /api/rooms/{room_id}` - Obtener información de sala
- `POST /api/rooms/{room_id}/join` - Unirse a sala
- `POST /api/rooms/{room_id}/leave` - Salir de sala

### Mensajes
- `GET /api/rooms/{room_id}/messages` - Obtener mensajes de sala
- `POST /api/rooms/{room_id}/messages` - Enviar mensaje

### Archivos
- `POST /api/uploads/` - Subir archivo
- `GET /api/uploads/{file_id}` - Información de archivo
- `DELETE /api/uploads/{file_id}` - Eliminar archivo
- `GET /api/uploads/types/allowed` - Tipos de archivo permitidos

### WebSocket
- `ws://localhost:8000/api/ws/{room_id}?token=JWT_TOKEN` - Conexión en tiempo real

## 🌐 Uso de WebSocket

### Conectar al chat en tiempo real

```javascript
const token = "tu_jwt_token";
const roomId = 1;
const ws = new WebSocket(`ws://localhost:8000/api/ws/${roomId}?token=${token}`);

ws.onopen = function() {
    console.log("Conectado al chat");
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("Mensaje recibido:", data);
};

// Enviar mensaje
ws.send(JSON.stringify({
    type: "message",
    content: "¡Hola mundo!",
    file_id: null // opcional
}));

// Indicar que estás escribiendo
ws.send(JSON.stringify({
    type: "typing",
    typing: true
}));
```

### Tipos de mensajes WebSocket

#### Recibidos del servidor:
- `welcome` - Mensaje de bienvenida
- `message` - Nuevo mensaje de chat
- `user_joined` - Usuario se unió a la sala
- `user_left` - Usuario salió de la sala
- `typing` - Indicador de escritura
- `users_online` - Lista de usuarios conectados
- `error` - Error del servidor

#### Enviados al servidor:
- `message` - Enviar mensaje de chat
- `typing` - Indicar estado de escritura
- `ping` - Mantener conexión activa

## 📁 Subida de archivos

### Tipos de archivo soportados

- **Documentos**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT, CSV
- **Imágenes**: JPG, PNG, GIF, WebP, SVG
- **Audio**: MP3, WAV, OGG
- **Video**: MP4, AVI, MOV
- **Comprimidos**: ZIP, RAR, 7Z

### Límites
- Tamaño máximo: 50MB por archivo
- Máximo 10 archivos por subida múltiple

### Ejemplo de subida

```python
import requests

# Subir archivo
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    headers = {'Authorization': 'Bearer JWT_TOKEN'}
    response = requests.post(
        'http://localhost:8000/api/uploads/',
        files=files,
        headers=headers
    )

file_info = response.json()
print(f"Archivo subido: {file_info['public_url']}")

# Enviar mensaje con archivo
message_data = {
    "content": "Te envío este documento",
    "room_id": 1,
    "file_id": file_info['id']
}

response = requests.post(
    'http://localhost:8000/api/rooms/1/messages',
    json=message_data,
    headers=headers
)
```

## 🗂️ Estructura del proyecto

```
izpoChatBackend/
├── chat_app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI
│   ├── database.py          # Configuración de base de datos
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Esquemas Pydantic
│   ├── crud.py              # Operaciones de base de datos
│   ├── dependencies.py      # Dependencias y autenticación
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuración de la aplicación
│   └── routers/
│       ├── __init__.py
│       ├── users.py         # Endpoints de usuarios
│       ├── rooms.py         # Endpoints de salas
│       ├── uploads.py       # Endpoints de archivos
│       └── websockets.py    # WebSocket para chat en tiempo real
├── static/                  # Archivos estáticos
├── .env                     # Variables de entorno
├── requirements.txt         # Dependencias
├── init_db.py              # Script de inicialización
├── run_dev.py              # Script para desarrollo
└── README.md               # Este archivo
```

## 🔧 Solución de problemas

### Error de conexión a Supabase

```
could not translate host name "db.xxx.supabase.co" to address
```

**Soluciones:**
1. Verificar conexión a internet
2. Verificar URL de Supabase en `.env`
3. Verificar que el proyecto Supabase esté activo
4. Verificar firewall/proxy

### Error de Google Cloud Storage

```
The bucket specified does not exist
```

**Soluciones:**
1. Verificar que el bucket existe en Google Cloud
2. Verificar credenciales en `GOOGLE_APPLICATION_CREDENTIALS`
3. Verificar permisos de la cuenta de servicio

### Dependencias faltantes

```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt

# En Windows, si hay problemas con psycopg2
pip install psycopg2-binary --force-reinstall
```

## 🚀 Despliegue

### Variables de entorno para producción

```env
DEBUG=false
DATABASE_URL=postgresql://...
SECRET_KEY=clave_super_segura_para_produccion
ALLOWED_ORIGINS=["https://tu-frontend.com"]
```

### Docker (opcional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "chat_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -m 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Si tienes problemas o preguntas:
1. Revisa la documentación de la API en `/docs`
2. Verifica los logs del servidor
3. Abre un issue en GitHub

---

¡Gracias por usar IzpoChat! 🎉