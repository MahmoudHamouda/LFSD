from flask import Flask
from routes import chat_blueprint
from services.chat_service.controllers.feedback_controller import (
    feedback_controller,
)
from db import init_db

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config()")

# Initialize the database
init_db(app)

# Register the chat routes
app.register_blueprint(chat_blueprint, url_prefix="/chat")
app.register_blueprint(
    feedback_controller, url_prefix="/feedback"
)  # Register feedback routes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=app.config["DEBUG"])
