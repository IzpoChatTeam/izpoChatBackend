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
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Crear directorio static si no existe
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Incluir routers
app.include_router(users.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
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

# Manejador de errores global
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint no encontrado", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Error interno del servidor", "status_code": 500}