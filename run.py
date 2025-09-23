from app import app, db, socketio

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada")
    
    # Para Render, usar el puerto que asignen
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)