# app/__init__.py (Final Corrected Version)

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

# 1. Initialize extensions at the global level
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """The application factory. All configuration and setup happens here."""
    
    # 2. Create the Flask app instance
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 3. Initialize the extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db)

    # 4. Import and register blueprints inside the factory
    # This is crucial to prevent circular imports with routes.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # 5. Setup the background scheduler
    from .scheduler import check_expiring_products
    scheduler = BackgroundScheduler()
    scheduler.add_job(id='expiry_check_job', func=check_expiring_products, args=[app], trigger="interval", hours=24)
    if not scheduler.running:
        scheduler.start()

    return app

# 6. Import models at the bottom. This allows models.py to safely import 'db' from this file.
from . import models