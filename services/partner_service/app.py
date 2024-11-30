from flask import Flask
from routes import partner_blueprint
from db import init_db

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config()")

# Initialize the database
init_db(app)

# Register the partner routes
app.register_blueprint(partner_blueprint, url_prefix="/partners")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=app.config["DEBUG"])
