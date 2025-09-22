# Chat Backend API - Despliegue con Docker

## 🐳 Contenedores Incluidos

Este proyecto utiliza Docker Compose para orquestar múltiples servicios:

- **FastAPI App**: Backend principal con WebSockets
- **Nginx**: Reverse proxy y servidor de archivos estáticos
- **Redis**: Cache y gestión de sesiones WebSocket

## 🔧 Configuración Rápida

1. **Clonar/copiar el proyecto a tu VM de Google Cloud**
2. **Configurar variables de entorno**: `cp .env.production .env`
3. **Ejecutar despliegue**: `./deploy.sh`

## 📁 Estructura de Archivos Docker

```
├── Dockerfile              # Imagen de la aplicación FastAPI
├── docker-compose.yml      # Orquestación de servicios
├── nginx.conf             # Configuración del proxy
├── .dockerignore          # Archivos a excluir del build
├── deploy.sh              # Script de despliegue automático
├── .env.production        # Template de variables de entorno
└── DEPLOYMENT.md          # Guía completa de despliegue
```

## 🚀 Comandos Esenciales

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver estado de contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar un servicio específico
docker-compose restart app

# Detener todos los servicios
docker-compose down

# Reconstruir la aplicación
docker-compose build app
docker-compose up -d app
```

## 🌐 Endpoints Disponibles

Una vez desplegado, la aplicación estará disponible en:

- **API Docs**: `http://YOUR_IP/docs`
- **Health Check**: `http://YOUR_IP/health`
- **WebSocket**: `ws://YOUR_IP/api/ws/{room_id}`
- **Uploads**: `http://YOUR_IP/api/uploads/`

## 💾 Persistencia de Datos

- **Uploads**: `./uploads/` (montado como volumen)
- **Redis**: Datos en memoria (opcional persistence)
- **Base de datos**: Supabase (externa)

## 📈 Monitoreo

```bash
# Uso de recursos
docker stats

# Espacio en disco
docker system df

# Limpiar imágenes no utilizadas
docker system prune -f
```

**Para instrucciones detalladas, consulta [`DEPLOYMENT.md`](./DEPLOYMENT.md)**