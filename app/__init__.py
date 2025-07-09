import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config.from_mapping(
        SECRET_KEY='dev', # Should be replaced with a real secret key
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'database.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    from .models import db
    db.init_app(app)

    # Register blueprints
    from .routes import main_routes
    app.register_blueprint(main_routes)

    return app
