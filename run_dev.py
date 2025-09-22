# run_dev.py
"""
Script para ejecutar el servidor en modo desarrollo
"""

import uvicorn
from chat_app.main import app

if __name__ == "__main__":
    print("🚀 Iniciando IzpoChat API en modo desarrollo...")
    print("📝 Documentación disponible en: http://localhost:8000/docs")
    print("🔌 WebSocket endpoint: ws://localhost:8000/api/ws/{room_id}?token=your_jwt_token")
    
    uvicorn.run(
        "chat_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )