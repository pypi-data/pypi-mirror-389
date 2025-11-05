import threading
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

_thread_local = threading.local()

def get_query_timings():
    """
    Return list of queries executed in current request/thread.
    Each item: {"sql": str, "time_ms": float}
    """
    return getattr(_thread_local, "queries", [])

def clear_query_timings():
    _thread_local.queries = []

def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if not hasattr(_thread_local, "queries"):
        _thread_local.queries = []
    context._query_start_time = time.time()

def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    elapsed = (time.time() - getattr(context, "_query_start_time", time.time())) * 1000
    
    # Detect database type from connection
    database_type = 'unknown'
    try:
        dialect_name = conn.engine.dialect.name
        database_type = dialect_name  # postgres, mysql, sqlite, etc.
    except:
        pass
    
    query_info = {
        "sql": statement,
        "time_ms": elapsed,
        "params": parameters if parameters else [],
        "function_name": "Unknown",
        "database_type": database_type
    }
    
    # Try to attach query to current executing function
    try:
        from perfwatch.core.profiler import _get_current_stack
        stack = _get_current_stack()
        
        if stack:
            # Attach to the current function in the stack
            current_func = stack[-1]
            current_func.add_query(query_info)
            query_info["function_name"] = current_func.func_name
        else:
            # Fallback: store in thread-local
            _thread_local.queries.append(query_info)
    except Exception:
        # Fallback: store in thread-local
        _thread_local.queries.append(query_info)

def attach_sqlalchemy_listeners(engine: Engine):
    """
    Attach SQLAlchemy event listeners to track all queries and timings.
    """
    event.listen(engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(engine, "after_cursor_execute", _after_cursor_execute)

def detach_sqlalchemy_listeners(engine: Engine):
    """
    Detach listeners if needed.
    """
    event.remove(engine, "before_cursor_execute", _before_cursor_execute)
    event.remove(engine, "after_cursor_execute", _after_cursor_execute)
