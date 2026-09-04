from flask import Flask, jsonify, render_template, request, redirect, url_for, session as flask_session
from flask_cors import CORS
import os
import sys

# Ensure root workspace is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.models.database import init_db, db_session
from backend.middleware.request_logging import init_request_logging
from backend.middleware.error_handler import init_error_handlers

from backend.api.auth_routes import auth_bp
from backend.api.student_routes import student_bp
from backend.api.faculty_routes import faculty_bp
from backend.api.timetable_routes import timetable_bp
from backend.api.session_routes import session_bp
from backend.api.attendance_routes import attendance_bp
from backend.api.report_routes import report_bp
from backend.api.admin_routes import admin_bp
from backend.api.log_routes import log_bp
from backend.api.device_routes import device_bp
from backend.api.health_routes import health_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    # Enable CORS for all API routes
    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)

    # Init Middleware & Database
    init_request_logging(app)
    init_error_handlers(app)
    init_db()

    # Register API v1 Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(health_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    @app.route("/")
    def index():
        return jsonify({
            "name": "FaceAttend API Backend",
            "version": "1.0.0",
            "documentation": "/api/v1/health",
            "status": "online"
        })

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
