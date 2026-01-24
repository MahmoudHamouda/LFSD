from flask import Flask
from .config import get_config
from .db import init_db

def create_app(config_object=None):
    """
    Application factory for the User Management Service.
    """
    app = Flask(__name__)

    # 1. Load Configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)

    # 2. Initialize Database & Teardown
    # This also handles Base.metadata.create_all() for dev ENV and Session.remove()
    init_db(app)

    # 3. Register Blueprints
    # Defer import to prevent circular dependencies
    from .routes import user_blueprint
    app.register_blueprint(user_blueprint, url_prefix="/users")

    @app.route("/health")
    def health_check():
        return {"status": "healthy", "service": "user-management"}, 200

    return app

if __name__ == "__main__":
    app = create_app()
    # Note: debug=True in dev can cause the app to init twice due to reloader.
    # We rely on the app factory and guarded init_db to handle this safely.
    app.run(
        host="0.0.0.0", 
        port=5001, 
        debug=app.config.get("DEBUG", False),
        use_reloader=app.config.get("DEBUG", False)
    )
