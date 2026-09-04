import time
from flask import request, g
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("faceattend")

def init_request_logging(app):
    @app.before_request
    def before_request_func():
        g.start_time = time.time()
        import uuid
        g.request_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:12]}")
        logger.info(f"[{g.request_id}] START {request.method} {request.path} IP={request.remote_addr}")

    @app.after_request
    def after_request_func(response):
        duration = round((time.time() - getattr(g, 'start_time', time.time())) * 1000, 2)
        req_id = getattr(g, 'request_id', 'req-unknown')
        response.headers['X-Request-ID'] = req_id
        logger.info(f"[{req_id}] END {request.method} {request.path} Status={response.status_code} Duration={duration}ms")

        # Auto-register mobile devices sending X-Device-ID header
        device_id = request.headers.get("X-Device-ID")
        if device_id and not request.path.startswith("/static"):
            try:
                from backend.services.device_service import device_service
                user_id = getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') and g.current_user else None
                device_name = request.headers.get("X-Device-Model", "Android Mobile")
                platform = request.headers.get("X-OS-Version", "Android")
                app_version = request.headers.get("X-App-Version", "v1.0.0")
                device_service.register_or_update_device(
                    device_id=device_id,
                    user_id=user_id,
                    device_name=device_name,
                    platform=platform,
                    app_version=app_version
                )
            except Exception as err:
                logger.warning(f"Device auto-registration warning: {err}")

        return response

