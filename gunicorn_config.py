# gunicorn_config.py - Configuración para Gunicorn en producción

import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1
worker_class = 'eventlet'
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to help with memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# Process naming
proc_name = 'izpochat_gunicorn'

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = '/tmp'

# SSL (Render maneja esto automáticamente)
keyfile = None
certfile = None