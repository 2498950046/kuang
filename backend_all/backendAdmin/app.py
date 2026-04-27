from flask import Flask
from sqlalchemy import inspect, text

from backendAdmin.config import Config
from backendAdmin.extensions import bcrypt, cors, db, jwt


def create_app(config_class=Config):
    """Create the admin Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, supports_credentials=True)

    from backendAdmin.routes.auth import auth_bp
    from backendAdmin.routes.mineral import mineral_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(mineral_bp, url_prefix="/manage")

    database_initialized = False

    @app.before_request
    def initialize_database_once():
        nonlocal database_initialized
        if database_initialized:
            return

        with app.app_context():
            try:
                db.session.execute(text("SELECT 1"))

                inspector = inspect(db.engine)
                tables = inspector.get_table_names()

                if "users" not in tables:
                    create_table_sql = """
                    CREATE TABLE users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                    """

                    db.session.execute(text(create_table_sql))
                    db.session.commit()

                    from backendAdmin.models.user import User

                    admin = User(
                        username="admin",
                        email="admin@example.com",
                        password="Admin@123456",
                    )
                    db.session.add(admin)
                    db.session.commit()

                database_initialized = True
            except Exception as exc:
                print(f"database init failed: {exc}")
                import traceback

                traceback.print_exc()

    return app
