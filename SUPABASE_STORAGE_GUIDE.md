# 🗄️ Guía de Configuración Supabase Storage

## ✅ Configuración Completada

### 🔧 **Cambios Implementados:**

1. **Archivo `.env` actualizado:**
```env
# Supabase Storage - Bucket para archivos
SUPABASE_STORAGE_BUCKET=izpochat-bucket
SUPABASE_URL=https://rldgqojsdmuckuacyfcs.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

2. **Configuración en `config.py`:**
```python
SUPABASE_STORAGE_BUCKET: str = "izpochat-bucket"
SUPABASE_URL: str
SUPABASE_ANON_KEY: str
```

3. **Implementación completa en `uploads.py`:**
- ✅ Upload de archivos a Supabase Storage
- ✅ Eliminación de archivos
- ✅ Listado de archivos por usuario/sala
- ✅ Validación de tipos y tamaños
- ✅ URLs públicas automáticas

### 📁 **Tipos de Archivos Soportados:**
- **Imágenes:** JPEG, PNG, GIF, WebP
- **Documentos:** PDF, Word, Excel
- **Texto:** Plain text, CSV
- **Tamaño máximo:** 50MB

### 🗂️ **Estructura de Archivos en Supabase:**
```
bucket: izpochat-bucket/
├── uploads/
│   ├── {user_id}/
│   │   ├── 2025/09/23/
│   │   │   ├── uuid-filename.jpg
│   │   │   └── uuid-document.pdf
│   │   └── 2025/09/24/
│   └── {another_user_id}/
```

## 🚀 **Endpoints Disponibles:**

### 1. **Subir Archivo:**
```http
POST /api/uploads/
Content-Type: multipart/form-data
Authorization: Bearer {jwt_token}

file: [archivo]
room_id: 123 (opcional)
description: "Mi documento" (opcional)
```

### 2. **Listar Archivos:**
```http
GET /api/uploads/
Authorization: Bearer {jwt_token}

Query params:
- skip: 0
- limit: 50
- room_id: 123 (opcional)
```

### 3. **Obtener Archivo:**
```http
GET /api/uploads/{file_id}
Authorization: Bearer {jwt_token}
```

### 4. **Eliminar Archivo:**
```http
DELETE /api/uploads/{file_id}
Authorization: Bearer {jwt_token}
```

### 5. **Tipos Permitidos:**
```http
GET /api/uploads/types/allowed
```

## 🔧 **Configuración en Supabase Console:**

### 1. **Verificar Bucket:**
- Ir a Storage > Buckets
- Verificar que existe el bucket `v1`
- Configurar políticas de acceso

### 2. **Políticas RLS (Row Level Security):**
```sql
-- Política para INSERT (subir archivos)
CREATE POLICY "Users can upload files" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'izpochat-bucket' AND 
  auth.uid()::text = (storage.foldername(name))[2]
);

-- Política para SELECT (ver archivos)
CREATE POLICY "Users can view own files" ON storage.objects
FOR SELECT USING (
  bucket_id = 'izpochat-bucket' AND 
  auth.uid()::text = (storage.foldername(name))[2]
);

-- Política para DELETE (eliminar archivos)
CREATE POLICY "Users can delete own files" ON storage.objects
FOR DELETE USING (
  bucket_id = 'izpochat-bucket' AND 
  auth.uid()::text = (storage.foldername(name))[2]
);
```

### 3. **Configuración Bucket:**
```sql
-- Hacer bucket público para lectura
UPDATE storage.buckets 
SET public = true 
WHERE id = 'izpochat-bucket';
```

## 🧪 **Probar la Implementación:**

### 1. **Desde Postman:**
```json
POST {{api_url}}/api/uploads/
Headers:
  Authorization: Bearer {{jwt_token}}
  Content-Type: multipart/form-data

Body:
  file: [seleccionar archivo]
  room_id: 1
  description: "Documento de prueba"
```

### 2. **Desde Angular:**
```typescript
uploadFile(file: File, roomId?: number, description?: string) {
  const formData = new FormData();
  formData.append('file', file);
  if (roomId) formData.append('room_id', roomId.toString());
  if (description) formData.append('description', description);

  return this.http.post(`${this.apiUrl}/api/uploads/`, formData, {
    headers: {
      'Authorization': `Bearer ${this.token}`
    }
  });
}
```

### 3. **Verificar en Supabase:**
- Storage > v1 bucket
- Verificar que aparecen los archivos subidos
- Probar URL pública del archivo

## 🔄 **Migración de Base de Datos:**

### En la VM, ejecutar:
```bash
# Aplicar migración
cd /path/to/izpoChatBackend
python migrate_to_supabase_storage.py
```

O usar Alembic si está configurado:
```bash
alembic upgrade head
```

## 📊 **Monitoreo:**

### Verificar uploads funcionando:
```bash
# Test endpoint
curl -X GET "http://34.72.14.164/api/uploads/types/allowed"

# Verificar bucket
curl "https://rldgqojsdmuckuacyfcs.supabase.co/storage/v1/bucket/izpochat-bucket"

# Ver logs
docker-compose logs app | grep upload
```

## 🎯 **Para tu Presentación:**

### Demo completo de archivos:
1. **Login:** `POST /api/auth/login`
2. **Crear sala:** `POST /api/rooms/`
3. **Subir archivo:** `POST /api/uploads/` (con room_id)
4. **Listar archivos:** `GET /api/uploads/?room_id=X`
5. **Enviar mensaje con archivo:** WebSocket con referencia al file_id
6. **Ver archivo público:** Usar file_url directamente

### URLs de ejemplo:
```
Subir: http://34.72.14.164/api/uploads/
Listar: http://34.72.14.164/api/uploads/
Tipos: http://34.72.14.164/api/uploads/types/allowed
```

## ⚡ **Ventajas de Supabase Storage:**

- ✅ **Gratis:** 1GB incluido en plan gratuito
- ✅ **URLs públicas:** Acceso directo a archivos
- ✅ **Integrado:** Misma base de datos que usas
- ✅ **CDN:** Distribución global automática
- ✅ **Seguridad:** Políticas RLS configurables
- ✅ **Sin servidores:** Serverless automático

## 🔍 **Troubleshooting:**

### Error de permisos:
```bash
# Verificar configuración
curl "https://rldgqojsdmuckuacyfcs.supabase.co/storage/v1/bucket/izpochat-bucket"
```

### Error de CORS:
- Verificar que bucket sea público
- Revisar políticas RLS en Supabase Console

### Error de autenticación:
- Verificar SUPABASE_ANON_KEY en .env
- Confirmar URL de Supabase

¡Listo para usar Supabase Storage! 🎉