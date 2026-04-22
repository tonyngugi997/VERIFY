from flask import Flask
from models import init_database
from routes import register_routes
from flask_login import LoginManager
from auth import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['role'])
    return None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'incorrect.997@BreastFriend'
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    init_database()
    
    register_routes(app)
    
    return app

def run():
    try:
        app = create_app()
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"Error starting the application: {e}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"Unhandled exception: {e}")