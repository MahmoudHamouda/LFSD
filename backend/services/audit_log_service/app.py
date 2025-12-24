from flask import Flask
from routes import audit_log_blueprint
from db import init_db

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config()")

# Initialize the database
init_db(app)

# Register the audit log routes
app.register_blueprint(audit_log_blueprint, url_prefix="/audit-logs")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=app.config["DEBUG"])
