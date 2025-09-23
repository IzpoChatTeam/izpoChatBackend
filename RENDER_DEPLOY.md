# 🚀 Guía de Despliegue en Render

## 📋 Pasos para desplegar en Render

### 1. **Crear cuenta en Render**
- Ve a [render.com](https://render.com)
- Regístrate con tu cuenta de GitHub

### 2. **Conectar repositorio**
- Conecta tu repositorio de GitHub `izpoChatBackend`
- Render detectará automáticamente que es una app Python

### 3. **Configurar PostgreSQL Database**
- En Render, crear una nueva PostgreSQL Database
- Nombre: `izpochat-db`
- Copiar la `Internal Database URL` que se genera

### 4. **Configurar Web Service**
- **Build Command**: `./build.sh`
- **Start Command**: `python run.py`
- **Environment**: `Python 3.11`
- **Plan**: Free (para empezar)

### 5. **Variables de entorno**
```bash
# Básicas
SECRET_KEY=tu-clave-secreta-super-segura
JWT_SECRET_KEY=tu-jwt-clave-secreta
FLASK_ENV=production

# Base de datos (usar la Internal Database URL de Render)
DATABASE_URL=postgresql://user:pass@host:port/db

# Supabase Storage
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=tu-supabase-anon-key
SUPABASE_STORAGE_BUCKET=izpochat-bucket
```

### 6. **CORS para frontend**
- Una vez desplegado, obtendrás una URL como `https://tu-app.onrender.com`
- Actualiza tu Angular para usar esta URL como API_URL

### 7. **Ventajas de Render vs Docker/VM**
✅ **Más fácil**: No necesitas manejar Docker ni Nginx
✅ **Automático**: Deploy automático desde GitHub
✅ **HTTPS**: SSL automático incluido
✅ **Escalable**: Fácil cambiar planes
✅ **Base de datos**: PostgreSQL incluido
✅ **Logs**: Interface web para ver logs

## 🔧 Comandos para probar localmente

```bash
# Instalar dependencias Flask
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Correr localmente
python run.py
```

## 📱 Endpoints Flask

- **Health**: `GET /health`
- **Register**: `POST /api/users/register`
- **Login**: `POST /api/users/login`
- **Rooms**: `GET/POST /api/rooms`
- **Messages**: `GET /api/rooms/{id}/messages`
- **Upload**: `POST /api/upload`
- **WebSocket**: Connection at `/socket.io/`

## 🎯 Para tu presentación

1. **URL pública**: `https://tu-app.onrender.com`
2. **Documentación**: No hay Swagger, pero tienes endpoints REST claros
3. **WebSocket**: Funciona automáticamente con HTTPS
4. **Base de datos**: PostgreSQL en la nube
5. **Storage**: Supabase Storage integrado

¡Mucho más simple que Docker + Nginx + Google Cloud VM!