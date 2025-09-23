# chat_app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .core.config import settings
from .routers import users, rooms, uploads, websockets

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API backend para IzpoChat - Chat en tiempo real con soporte para archivos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False  # CRÍTICO: Evitar redirects 307
)

# Configurar CORS - Permisivo para desarrollo/ejercicio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

# Crear directorio static si no existe
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Incluir routers
app.include_router(users.router, prefix="/api")
app.include_router(rooms.router, prefix="/api/rooms")  # Prefix específico para evitar redirects
app.include_router(uploads.router, prefix="/api")
app.include_router(websockets.router, prefix="/api")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "¡Bienvenido a IzpoChat API!",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IzpoChat API"}

@app.get("/cors-test")
async def cors_test():
    """Endpoint específico para probar CORS"""
    return {
        "message": "CORS funcionando correctamente",
        "timestamp": "2025-09-23",
        "origin_allowed": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "headers": "All headers allowed"
    }

# Manejador de errores global
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint no encontrado", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Error interno del servidor", "status_code": 500}