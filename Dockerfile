# Dockerfile para IzpoChat Backend
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Crear usuario no root para seguridad
RUN useradd --create-home --shell /bin/bash app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libmagic1 \
    libmagic-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para archivos estáticos
RUN mkdir -p /app/static/uploads && \
    chown -R app:app /app

# Cambiar a usuario no root
USER app

# Exponer puerto
EXPOSE 8000

# Comando de inicio para producción
CMD ["uvicorn", "chat_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]