import sys
import os
# Ensure workspace root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import Config
from backend.routes.auth_routes import auth_bp
from backend.routes.profile_routes import profile_bp
from backend.routes.assessment_routes import assessment_bp
from backend.routes.project_routes import project_bp
from backend.routes.analytics_routes import analytics_bp
from backend.routes.chatbot_routes import chatbot_bp

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for frontend communication
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(profile_bp, url_prefix="/api/profile")
app.register_blueprint(assessment_bp, url_prefix="/api/assessment")
app.register_blueprint(project_bp, url_prefix="/api/project")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

@app.route("/", methods=["GET"])
@app.route("/api", methods=["GET"])
def index():
    return jsonify({
        "status": "Online",
        "message": "WorkForceX API Server is running",
        "version": "1.0.0"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Ensure upload directory exists
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
        
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting WorkForceX backend on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
