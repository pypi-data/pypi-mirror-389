import time
import threading
from django.db import connection
from perfwatch.core.profiler import _get_current_stack
import logging

logger = logging.getLogger(__name__)

_thread_local = threading.local()


def get_query_timings():
    return getattr(_thread_local, "queries", [])


def clear_query_timings():
    _thread_local.queries = []


def _record_query(sql, params, duration_ms):
    """Record query and attach it to the currently executing function"""
    stack = _get_current_stack()
    
    # If there's a function currently executing, attach query directly to it
    if stack:
        current_func = stack[-1]  # Get the topmost function in the stack
        current_func.add_query({
            "sql": sql,
            "params": params,
            "time_ms": duration_ms,
            "function_name": current_func.func_name,  # Add function name for easy hierarchy building
        })
    else:
        # Fallback: store in thread-local if no function is executing
        if not hasattr(_thread_local, "queries"):
            _thread_local.queries = []
        _thread_local.queries.append({
            "sql": sql,
            "params": params,
            "time_ms": duration_ms,
            "function_name": "Unknown",  # No function context
        })


class DjangoORMProfilerMiddleware:
    """Middleware that records DB query timings more robustly.

    Uses Django's connection.execute_wrapper when available (Django 3.2+).
    Falls back to patching the cursor class methods and restoring them afterwards.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        clear_query_timings()

        # Prefer Django's execute_wrapper if available
        wrapper_ctx = None
        patched = False
        original_execute = None
        original_executemany = None
        cursor_cls = None

        try:
            if hasattr(connection, "execute_wrapper"):
                # use execute_wrapper to intercept all executes
                def _wrapper_execute_execute(execute, sql, params, many, context):
                    start = time.time()
                    try:
                        return execute(sql, params, many, context)
                    finally:
                        duration_ms = (time.time() - start) * 1000
                        _record_query(sql, params, duration_ms)

                # Use as context manager so wrapper is active during get_response
                with connection.execute_wrapper(_wrapper_execute_execute):
                    response = self.get_response(request)
                    # response will be returned below after cleanup
                    pass
            else:
                # Fallback: patch cursor class methods so all cursors are affected
                cur = connection.cursor()
                cursor_cls = cur.__class__
                # save originals from class
                original_execute = getattr(cursor_cls, "execute", None)
                original_executemany = getattr(cursor_cls, "executemany", None)

                def timed_execute(self, sql, params=None):
                    start = time.time()
                    try:
                        return original_execute(self, sql, params)
                    finally:
                        duration_ms = (time.time() - start) * 1000
                        _record_query(sql, params, duration_ms)

                def timed_executemany(self, sql, param_list):
                    start = time.time()
                    try:
                        return original_executemany(self, sql, param_list)
                    finally:
                        duration_ms = (time.time() - start) * 1000
                        _record_query(sql, param_list, duration_ms)

                # patch class
                if original_execute:
                    cursor_cls.execute = timed_execute
                if original_executemany:
                    cursor_cls.executemany = timed_executemany
                patched = True

            # Call the next middleware / view (for fallback path)
            if not hasattr(connection, "execute_wrapper"):
                response = self.get_response(request)

        finally:
            # Restore any patched/unwrapped state
            try:
                if wrapper_ctx is not None:
                    # execute_wrapper returns a context manager-like object
                    try:
                        wrapper_ctx.close()
                    except Exception:
                        # older Django may use context manager protocol
                        logger.debug("Failed to close execute_wrapper context cleanly", exc_info=True)

                if patched and cursor_cls is not None:
                    if original_execute:
                        cursor_cls.execute = original_execute
                    if original_executemany:
                        cursor_cls.executemany = original_executemany
            except Exception:
                # ensure cleanup never raises
                pass

        return response
