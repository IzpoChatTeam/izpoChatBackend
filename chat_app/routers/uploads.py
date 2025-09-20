# chat_app/routers/uploads.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from google.cloud import storage
from google.api_core import exceptions
import uuid

# Importa tu configuración para obtener el nombre del bucket
from ..core.config import settings # Suponiendo que tienes un objeto settings

router = APIRouter()

# Configura el cliente de Google Cloud Storage
# La autenticación se maneja automáticamente a través de la variable de entorno
storage_client = storage.Client()
bucket_name = settings.GCS_BUCKET_NAME

@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    """
    Sube un archivo a Google Cloud Storage y devuelve su URL pública.
    """
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except exceptions.NotFound:
        raise HTTPException(status_code=404, detail="El bucket especificado no existe.")

    # Genera un nombre de archivo único para evitar sobrescribir archivos
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    
    # Crea un "blob" (el objeto que representa el archivo en GCS)
    blob = bucket.blob(unique_filename)

    try:
        # Sube el contenido del archivo al blob
        # Usamos file.file que es un objeto tipo archivo (spooled temporary file)
        blob.upload_from_file(file.file, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo subir el archivo: {e}")

    # Opcional: Haz el archivo públicamente accesible
    blob.make_public()

    # Devuelve la URL pública del archivo subido
    return {"filename": unique_filename, "public_url": blob.public_url}