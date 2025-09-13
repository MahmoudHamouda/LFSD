from flask import Flask
from api_gateway.routes.user_routes import user_blueprint
from api_gateway.routes.financial_routes import financial_blueprint
from api_gateway.routes.notification_routes import notification_blueprint
from api_gateway.routes.partner_routes import partner_blueprint
from api_gateway.routes.recommendation_routes import recommendation_blueprint
from api_gateway.routes.activity_feed_routes import activity_feed_blueprint
from api_gateway.routes.audit_routes import audit_blueprint
from api_gateway.routes.chat_routes import chat_blueprint
from shared.logging import setup_logging


def create_app():
    app = Flask(__name__)
    # Setup logging
    setup_logging(app, service_name="api_gateway")
    # Register Blueprints
    app.register_blueprint(user_blueprint, url_prefix="/users")
    app.register_blueprint(financial_blueprint, url_prefix="/financial")
    app.register_blueprint(notification_blueprint, url_prefix="/notifications")
    app.register_blueprint(partner_blueprint, url_prefix="/partners")
    app.register_blueprint(recommendation_blueprint, url_prefix="/recommendations")
    app.register_blueprint(activity_feed_blueprint, url_prefix="/activity")
    app.register_blueprint(audit_blueprint, url_prefix="/audit")
    app.register_blueprint(chat_blueprint, url_prefix="/chat")
    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok"}
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
