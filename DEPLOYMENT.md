# Guía de Despliegue en Google Cloud VM

## 📋 Requisitos Previos

1. **Cuenta de Google Cloud Platform** con proyecto creado
2. **VM creada** con las siguientes especificaciones mínimas:
   - OS: Ubuntu 20.04 LTS o superior
   - RAM: 2GB mínimo (4GB recomendado)
   - Disco: 20GB mínimo
   - Firewall: Puertos 80, 443, 22 abiertos

## 🚀 Despliegue Paso a Paso

### 1. Conectar a la VM

```bash
# Desde Google Cloud Console o usando gcloud CLI
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE
```

### 2. Clonar/Subir el Proyecto

Opción A - Usando Git:
```bash
git clone YOUR_REPOSITORY_URL
cd izpoChatBackend
```

Opción B - Subir archivos usando SCP:
```bash
# Desde tu máquina local
gcloud compute scp --recurse ./izpoChatBackend YOUR_VM_NAME:~/ --zone=YOUR_ZONE
```

### 3. Configurar Variables de Entorno

```bash
# Copiar y editar el archivo de configuración
cp .env.production .env

# Editar las variables con tus valores reales
nano .env
```

**Variables importantes a configurar:**
```env
# Base de datos Supabase
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Secret (generar uno seguro)
SECRET_KEY=your-super-secret-jwt-key-here

# Configuración de uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=pdf,doc,docx,txt,jpg,png

# Redis (usando el contenedor local)
REDIS_URL=redis://redis:6379

# Configuración del servidor
HOST=0.0.0.0
PORT=8000
```

### 4. Ejecutar el Script de Despliegue

```bash
# Hacer ejecutable el script
chmod +x deploy.sh

# Ejecutar despliegue automático
./deploy.sh
```

El script automáticamente:
- ✅ Instala Docker y Docker Compose
- ✅ Configura el firewall
- ✅ Construye las imágenes
- ✅ Inicia los servicios
- ✅ Verifica la salud de la aplicación

### 5. Verificar Despliegue

```bash
# Verificar que los contenedores están corriendo
docker ps

# Ver logs de la aplicación
docker-compose logs -f app

# Probar el endpoint de salud
curl http://localhost/health
```

## 🌐 Configuración de Dominio (Opcional)

### 1. Configurar IP Estática

```bash
# Reservar IP estática en Google Cloud
gcloud compute addresses create chat-app-ip --region=YOUR_REGION

# Asignar a la VM
gcloud compute instances delete-access-config YOUR_VM_NAME --zone=YOUR_ZONE
gcloud compute instances add-access-config YOUR_VM_NAME --zone=YOUR_ZONE --address=STATIC_IP
```

### 2. Configurar DNS

En tu proveedor de DNS, crear registros:
```
A    your-domain.com    -> STATIC_IP
A    www.your-domain.com -> STATIC_IP
```

### 3. Configurar SSL (HTTPS)

```bash
# Instalar Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# El certificado se renovará automáticamente
```

## 📊 Monitoreo y Mantenimiento

### Ver Logs

```bash
# Logs de la aplicación
docker-compose logs -f app

# Logs de Nginx
docker-compose logs -f nginx

# Logs de Redis
docker-compose logs -f redis
```

### Comandos Útiles

```bash
# Reiniciar servicios
docker-compose restart

# Actualizar aplicación
git pull
docker-compose build app
docker-compose up -d

# Backup de base de datos (si usas PostgreSQL local)
docker-compose exec postgres pg_dump -U username database > backup.sql

# Limpiar contenedores antiguos
docker system prune -f
```

### Escalado

Para manejar más tráfico:

```bash
# Escalar instancias de la aplicación
docker-compose up -d --scale app=3
```

Actualizar `nginx.conf` para load balancing:
```nginx
upstream app {
    server app:8000;
    server app_2:8000;
    server app_3:8000;
}
```

## 🔒 Seguridad

### Firewall de Google Cloud

```bash
# Crear reglas de firewall específicas
gcloud compute firewall-rules create allow-http --allow tcp:80
gcloud compute firewall-rules create allow-https --allow tcp:443
gcloud compute firewall-rules create allow-ssh --allow tcp:22 --source-ranges=YOUR_IP
```

### Hardening de la VM

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Configurar fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Configurar swap si es necesario
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 🛠️ Troubleshooting

### Problemas Comunes

1. **Error de conexión a base de datos**
   ```bash
   # Verificar variables de entorno
   docker-compose exec app env | grep DATABASE
   
   # Probar conexión manualmente
   docker-compose exec app python test_connection.py
   ```

2. **Error 502 Bad Gateway**
   ```bash
   # Verificar que la app está corriendo
   docker-compose ps
   
   # Verificar logs de nginx
   docker-compose logs nginx
   ```

3. **WebSockets no funcionan**
   - Verificar que el puerto 80/443 está abierto
   - Comprobar configuración de proxy en nginx.conf

4. **Falta de espacio en disco**
   ```bash
   # Limpiar imágenes Docker no utilizadas
   docker system prune -a
   
   # Verificar espacio
   df -h
   ```

## 📞 Soporte

Para problemas específicos:
1. Revisar logs: `docker-compose logs -f`
2. Verificar salud: `curl http://localhost/health`
3. Comprobar configuración: `docker-compose config`

---

**¡Tu aplicación de chat está lista para producción!** 🎉

Accede a: `http://YOUR_VM_IP` o `https://your-domain.com`