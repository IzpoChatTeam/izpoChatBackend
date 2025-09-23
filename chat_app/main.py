# chat_app/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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

# Middleware personalizado para manejar headers adicionales para WebSocket
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Headers adicionales para WebSocket y CORS
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    # Headers específicos para WebSocket
    if "upgrade" in request.headers.get("connection", "").lower():
        response.headers["Access-Control-Allow-Headers"] += ", Upgrade, Connection, Sec-WebSocket-Key, Sec-WebSocket-Version, Sec-WebSocket-Protocol, Sec-WebSocket-Extensions"
    
    return response

# Configurar CORS - Específico para Angular y compatible con WebSockets
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200", 
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Fallback para cualquier otro origen
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
        "Sec-WebSocket-Extensions",
        "Sec-WebSocket-Key",
        "Sec-WebSocket-Protocol", 
        "Sec-WebSocket-Version",
        "Upgrade",
        "Connection"
    ],
    expose_headers=["*"]
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

@app.options("/{path:path}")
async def options_handler(path: str):
    """Manejar todas las requests OPTIONS para CORS preflight"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "IzpoChat API"}

@app.get("/cors-test")
async def cors_test(request: Request):
    """Endpoint específico para probar CORS con información detallada"""
    origin = request.headers.get("origin", "No origin header")
    user_agent = request.headers.get("user-agent", "No user agent")
    
    return {
        "message": "CORS funcionando correctamente",
        "timestamp": "2025-09-23",
        "origin_received": origin,
        "user_agent": user_agent,
        "cors_status": "enabled",
        "websocket_support": True,
        "angular_compatible": True,
        "headers_allowed": [
            "Content-Type", "Authorization", "Accept", "Origin",
            "X-Requested-With", "Cache-Control", "Pragma",
            "Sec-WebSocket-Extensions", "Sec-WebSocket-Key",
            "Sec-WebSocket-Protocol", "Sec-WebSocket-Version",
            "Upgrade", "Connection"
        ],
        "methods_allowed": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "credentials": True
    }

# Manejador de errores global
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint no encontrado", "status_code": 404}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Error interno del servidor", "status_code": 500}