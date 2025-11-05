import time

def format_ms(ms):
    """Convert milliseconds to human-readable string"""
    if ms < 1000:
        return f"{ms:.2f} ms"
    else:
        return f"{ms/1000:.2f} s"

def current_time_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
