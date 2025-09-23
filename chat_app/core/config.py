# chat_app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # --- Base ---
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- Google Cloud Storage ---
    GCS_BUCKET_NAME: str
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # --- App ---
    APP_NAME: str = "IzpoChat API"
    DEBUG: bool = False

    # --- CORS ---
    ALLOWED_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # --- Database Pool ---
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- Logs ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # --- File Uploads ---
    MAX_FILE_SIZE: int = 52428800
    UPLOAD_PATH: str = "/app/static/uploads"

    # --- SMTP ---
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True

    # --- Rate Limiting ---
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 30

    # --- WebSocket ---
    WS_MAX_CONNECTIONS_PER_ROOM: int = 100
    WS_PING_INTERVAL: int = 30
    WS_PING_TIMEOUT: int = 10

    # --- Monitoring ---
    HEALTH_CHECK_INTERVAL: int = 30
    METRICS_ENABLED: bool = True

    # --- SSL ---
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()