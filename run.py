from app import app, db, socketio
import os

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada")
    
    # Detectar si estamos en Render (producción)
    if os.environ.get('RENDER') or os.environ.get('PORT'):
        # En producción usar gunicorn con eventlet
        import subprocess
        import sys
        
        cmd = [
            sys.executable, '-m', 'gunicorn',
            '--config', 'gunicorn_config.py',
            'app:app'
        ]
        print(f"Iniciando con gunicorn: {' '.join(cmd)}")
        subprocess.run(cmd)
    else:
        # Para desarrollo local
        port = int(os.environ.get('PORT', 5000))
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)