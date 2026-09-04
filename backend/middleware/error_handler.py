from backend.utils.response import api_error
import traceback
import logging

logger = logging.getLogger("faceattend")

def init_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(e):
        return api_error(str(e.description) if hasattr(e, 'description') else "Bad request", code="BAD_REQUEST", status_code=400)

    @app.errorhandler(404)
    def not_found_error(e):
        return api_error("Resource not found", code="NOT_FOUND", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed_error(e):
        return api_error("HTTP method not allowed", code="METHOD_NOT_ALLOWED", status_code=405)

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal Error: {e}\n{traceback.format_exc()}")
        return api_error("Internal server error", code="INTERNAL_SERVER_ERROR", status_code=500)

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        logger.error(f"Unhandled Exception: {e}\n{traceback.format_exc()}")
        return api_error("An internal server error occurred", code="SERVER_ERROR", status_code=500)
