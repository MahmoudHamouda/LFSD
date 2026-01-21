from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    
    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "ok", "service": "api-gateway"}
    
    @app.route("/")
    def root():
        return {"message": "API Gateway is running", "port": os.environ.get("PORT", "not set")}
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting API Gateway on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
