from flask import jsonify, g
import uuid

def get_request_id():
    if hasattr(g, 'request_id'):
        return g.request_id
    g.request_id = f"req-{uuid.uuid4().hex[:12]}"
    return g.request_id

def api_response(data=None, message=None, status_code=200, **extra):
    response = {
        "success": True,
        "request_id": get_request_id()
    }
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    for key, value in extra.items():
        response[key] = value
    return jsonify(response), status_code

def api_error(message, code="ERROR", status_code=400, details=None):
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        },
        "request_id": get_request_id()
    }
    if details:
        response["error"]["details"] = details
    return jsonify(response), status_code
