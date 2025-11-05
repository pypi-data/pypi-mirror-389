import threading
import uuid

_thread_local = threading.local()

def generate_request_id():
    """
    Generate a unique request ID.
    Can be used to track metrics per request.
    """
    return str(uuid.uuid4())

def set_current_request_id(request_id=None):
    """
    Set the current request ID in thread-local storage.
    If request_id is None, generate a new one.
    """
    if request_id is None:
        request_id = generate_request_id()
    _thread_local.request_id = request_id
    return request_id

def get_current_request_id():
    """
    Get the current request ID from thread-local storage.
    Returns None if not set.
    """
    return getattr(_thread_local, "request_id", None)

def clear_current_request_id():
    """
    Clear the request ID from thread-local storage.
    Useful after request is complete.
    """
    if hasattr(_thread_local, "request_id"):
        del _thread_local.request_id
