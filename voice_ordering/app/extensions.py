"""Flask extension singletons, imported by the app factory and blueprints."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

login_manager.login_view = "admin.login"
login_manager.login_message = "Administrator sign-in required."
login_manager.session_protection = "strong"
