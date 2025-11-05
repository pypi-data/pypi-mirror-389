import threading
import time
from pymongo import monitoring

_thread_local = threading.local()

def get_query_timings():
    """
    Return list of Mongo queries executed in current request/thread.
    Each item: {"command": str, "duration_ms": float}
    """
    return getattr(_thread_local, "queries", [])

def clear_query_timings():
    _thread_local.queries = []

class PerfWatchMongoListener(monitoring.CommandListener):
    """
    PyMongo command listener to track query timings.
    """

    def started(self, event):
        event._start_time = time.time()

    def succeeded(self, event):
        duration_ms = (time.time() - getattr(event, "_start_time", time.time())) * 1000
        
        query_info = {
            "command": str(event.command),
            "duration_ms": duration_ms,
            "db_type": "mongodb",
            "database_type": "mongodb",
            "function_name": "Unknown"
        }
        
        # Try to attach query to current executing function
        try:
            from perfwatch.core.profiler import _get_current_stack
            stack = _get_current_stack()
            
            if stack:
                # Attach to the current function in the stack
                current_func = stack[-1]
                current_func.add_query({
                    "sql": str(event.command),  # Using 'sql' key for consistency
                    "time_ms": duration_ms,
                    "database_type": "mongodb",
                    "db_type": "mongodb",
                    "params": [],
                    "function_name": current_func.func_name
                })
                query_info["function_name"] = current_func.func_name
            else:
                # Fallback: store in thread-local
                if not hasattr(_thread_local, "queries"):
                    _thread_local.queries = []
                _thread_local.queries.append(query_info)
        except Exception:
            # Fallback: store in thread-local
            if not hasattr(_thread_local, "queries"):
                _thread_local.queries = []
            _thread_local.queries.append(query_info)

    def failed(self, event):
        duration_ms = (time.time() - getattr(event, "_start_time", time.time())) * 1000
        
        query_info = {
            "command": str(event.command),
            "duration_ms": duration_ms,
            "db_type": "mongodb",
            "database_type": "mongodb",
            "failed": True,
            "function_name": "Unknown"
        }
        
        # Try to attach query to current executing function
        try:
            from perfwatch.core.profiler import _get_current_stack
            stack = _get_current_stack()
            
            if stack:
                # Attach to the current function in the stack
                current_func = stack[-1]
                current_func.add_query({
                    "sql": str(event.command),
                    "time_ms": duration_ms,
                    "database_type": "mongodb",
                    "db_type": "mongodb",
                    "params": [],
                    "failed": True,
                    "function_name": current_func.func_name
                })
                query_info["function_name"] = current_func.func_name
            else:
                # Fallback: store in thread-local
                if not hasattr(_thread_local, "queries"):
                    _thread_local.queries = []
                _thread_local.queries.append(query_info)
        except Exception:
            # Fallback: store in thread-local
            if not hasattr(_thread_local, "queries"):
                _thread_local.queries = []
            _thread_local.queries.append(query_info)

def attach_mongo_monitoring(client):
    """
    Attach PerfWatch Mongo listener to PyMongo client.
    """
    monitoring.register(PerfWatchMongoListener())

def detach_mongo_monitoring(client):
    """
    Unregister PerfWatch Mongo listener.
    """
    monitoring.unregister(PerfWatchMongoListener)
