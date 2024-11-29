```python
from flask import Flask
from routes import recommendation_blueprint
from db import init_db

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config()")

# Initialize the database
init_db(app)

# Register the recommendation routes
app.register_blueprint(recommendation_blueprint, url_prefix="/recommendations")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=app.config["DEBUG"])