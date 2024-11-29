```python
from flask import Flask
from routes import user_blueprint
from db import init_db

# Initialize the Flask app
app = Flask(__name__)

# Load configuration
app.config.from_object("config.get_config()")

# Initialize the database
init_db(app)

# Register the user management routes
app.register_blueprint(user_blueprint, url_prefix="/users")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=app.config["DEBUG"])