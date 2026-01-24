from flask import Flask, jsonify
import logging
import os

# Configure basic logging at the top-level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_object=None):
    """
    Application Factory for Partner Service.
    Hardened for multi-environment use and robust startup.
    """
    app = Flask(__name__)

    # 1. Load Configuration
    if config_object is None:
        from .config import get_config
        config_object = get_config()
    
    app.config.from_object(config_object)
    
    # 2. Initialize Database with error handling
    try:
        from .db import init_db
        init_db(app)
        logger.info("Partner database initialized successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Database initialization failed: {e}")
        # In a real microservice, we might want to exit here if DB is strictly required
        # but for dev workflows we might just log it.

    # 3. Register Routes (Deferred import to avoid circular dependencies)
    from .routes import partner_blueprint
    app.register_blueprint(partner_blueprint, url_prefix="/partners")

    # 4. Health Check Endpoint
    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "partner-service",
            "environment": app.config.get("ENV", "unknown")
        }), 200

    # 5. Global Error Handling
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    
    # Get port from environment or default to 5004
    port = int(os.environ.get("PARTNER_SERVICE_PORT", 5004))
    
    app.run(
        host="0.0.0.0",
        port=port,
        debug=app.config.get("DEBUG", False),
        use_reloader=app.config.get("DEBUG", False)
    )
