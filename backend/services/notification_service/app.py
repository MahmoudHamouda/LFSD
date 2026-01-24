from flask import Flask, jsonify
import os
import logging

# Basic logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_object=None):
    """
    Application Factory for Notification Service.
    """
    app = Flask(__name__)

    # 1. Load Configuration
    if config_object is None:
        # Assuming a config.py exists or is shared; for now using the pattern from PartnerService
        try:
            from .config import get_config
            app.config.from_object(get_config())
        except ImportError:
            # Fallback if config.py hasn't been created yet for this specific service
            app.config.update(
                DB_USER=os.environ.get("DB_USER", "postgres"),
                DB_PASSWORD=os.environ.get("DB_PASSWORD", "postgres"),
                DB_HOST=os.environ.get("DB_HOST", "localhost"),
                DB_PORT=os.environ.get("DB_PORT", "5432"),
                DB_NAME=os.environ.get("DB_NAME", "viv_notifications"),
                DEBUG=os.environ.get("DEBUG", "False").lower() == "true",
                ENV=os.environ.get("ENV", "development")
            )

    # 2. Initialize Database
    try:
        from .db import init_db
        init_db(app)
    except Exception as e:
        logger.error(f"Failed to initialize notification database: {e}")

    # 3. Register Routes
    from .routes import notification_blueprint
    app.register_blueprint(notification_blueprint, url_prefix="/notifications")

    # 4. Health Check
    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy", 
            "service": "notification-service",
            "environment": app.config.get("ENV")
        }), 200

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("NOTIFICATION_SERVICE_PORT", 5005))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=app.config.get("DEBUG", False),
        use_reloader=app.config.get("DEBUG", False)
    )
