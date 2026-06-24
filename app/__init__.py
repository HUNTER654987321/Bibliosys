from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesion para acceder."
    login_manager.login_message_category = "warning"

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.libros.routes import libros_bp
    from app.catalogos.routes import catalogos_bp
    from app.usuarios.routes import usuarios_bp
    from app.prestamos.routes import prestamos_bp
    from app.busqueda.routes import busqueda_bp
    from app.reportes.routes import reportes_bp
    from app.configuracion.routes import configuracion_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(libros_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(prestamos_bp)
    app.register_blueprint(busqueda_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(configuracion_bp)

    with app.app_context():
        from app import models
        db.create_all()
        models.obtener_configuracion_sistema()

    @app.context_processor
    def inject_configuracion_sistema():
        from app.models import obtener_configuracion_sistema
        return {"config_sistema": obtener_configuracion_sistema()}

    return app
