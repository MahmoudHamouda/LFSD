import os
import sys
import logging
from flask import Flask, jsonify

# Add the current directory to path if running directly to fix relative import issues
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from db import init_db

def create_app(config_object=None):
    """
    Application factory for the Recommendation Service.
    """
    app = Flask(__name__)

    # 1. Load Configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)

    # 2. Configure Logging
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 3. Initialize Database
    # Internal idempotency check is handled within init_db itself
    init_db(app)

    # 4. Error Handlers (Ensure JSON responses for all errors)
    @app.errorhandler(404)
    def non_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

    # 5. Register Blueprints
    from routes import recommendation_blueprint
    app.register_blueprint(recommendation_blueprint, url_prefix="/recommendations")

    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "service": "recommendation-service"}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    # Use environment variable for port, default to 5006
    port = int(os.environ.get("SERVICE_PORT", 5006))
    
    # In production, use a production-grade WSGI server like Gunicorn.
    # For development, we disable the reloader if we want to avoid double-init side effects,
    # though our init_db is now hardened.
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=app.config.get("DEBUG", False),
        use_reloader=False 
    )
