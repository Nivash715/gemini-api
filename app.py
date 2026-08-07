import os
from flask import Flask, render_template, send_from_directory
from config import UPLOAD_FOLDER, SECRET_KEY
from utils.database import init_db
from routes.chat_routes import chat_bp
from routes.history_routes import history_bp
from routes.export_routes import export_bp, settings_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs("database", exist_ok=True)
    os.makedirs("static/images", exist_ok=True)

    init_db()

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")
    app.register_blueprint(export_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        safe_name = os.path.basename(filename)
        return send_from_directory(str(UPLOAD_FOLDER), safe_name)

    @app.errorhandler(413)
    def too_large(e):
        return {"error": "File too large. Maximum upload size is 15 MB."}, 413

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Resource not found."}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error."}, 500

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=5000)
