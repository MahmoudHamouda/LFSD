from flask import Flask
from .routes import activity_feed_blueprint  # Use relative import
from .db import init_db  # Use relative import

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config")

# Initialize the database
init_db(app)

# Register the activity feed routes
app.register_blueprint(activity_feed_blueprint, url_prefix="/activity-feed")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=app.config["DEBUG"])
