import time
import functools
import threading
from typing import List, Dict, Optional
import logging
import tracemalloc
import gc
import sys
import os
import psutil  # For system-level metrics
from contextvars import ContextVar

# Do not import a specific adapter at module import time; choose at runtime.


# Thread-local for sync contexts (Django, Flask sync)
_thread_local = threading.local()

# Context var for async contexts (FastAPI, async views)
_async_stack: ContextVar[Optional[List]] = ContextVar('perfwatch_stack', default=None)

logger = logging.getLogger(__name__)


class FunctionProfile:
    def __init__(self, func_name: str, parent: Optional["FunctionProfile"] = None):
        self.func_name = func_name
        self.parent = parent
        self.start_time = None
        self.end_time = None
        self.duration_ms = 0.0
        self.children: List["FunctionProfile"] = []
        self.queries: List[Dict] = []
        
        # Memory metrics
        self.memory_bytes = 0
        self.memory_peak_bytes = 0
        self.memory_before_mb = 0
        self.memory_after_mb = 0
        self.memory_delta_mb = 0
        
        # GC metrics
        self.gc_stats_before = {}
        self.gc_stats_after = {}
        self.gc_collected = {}
        self.gc_enabled = True
        
        # Object tracking
        self.objects_created = 0
        self.objects_destroyed = 0
        self.object_count_delta = 0
        
        # CPU and system metrics
        self.cpu_percent = 0.0
        self.cpu_time_user = 0.0
        self.cpu_time_system = 0.0
        self.thread_count = 0
        self.io_read_bytes = 0
        self.io_write_bytes = 0
        
        self.call_count = 0
        self.file_path = None
        self.line_number = None
        self.error = None
        self.stack_trace = None
        
        # Internal snapshots
        self._mem_before = 0
        self._mem_peak_before = 0
        self._process = None
        self._cpu_times_before = None
        self._io_counters_before = None
        self._obj_count_before = 0
        
        # Get caller info
        try:
            import inspect
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back  # Skip our own frames
            self.file_path = caller_frame.f_code.co_filename
            self.line_number = caller_frame.f_lineno
        except:
            pass
        finally:
            del frame

    def start(self):
        self.start_time = time.perf_counter()
        self.call_count += 1
        
        # Start tracemalloc if not already running
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            self._mem_before, self._mem_peak_before = tracemalloc.get_traced_memory()
        except Exception:
            self._mem_before = 0
            self._mem_peak_before = 0
        
        # Capture process-level metrics
        try:
            self._process = psutil.Process(os.getpid())
            mem_info = self._process.memory_info()
            self.memory_before_mb = mem_info.rss / (1024 * 1024)
            self._cpu_times_before = self._process.cpu_times()
            self._io_counters_before = self._process.io_counters()
            self.thread_count = self._process.num_threads()
        except Exception as e:
            logger.debug(f"Failed to capture process metrics: {e}")
        
        # Capture GC stats before
        try:
            self.gc_enabled = gc.isenabled()
            self.gc_stats_before = {
                'collections': [gc.get_count()[i] for i in range(3)],
                'thresholds': gc.get_threshold(),
                'objects': len(gc.get_objects())
            }
            self._obj_count_before = self.gc_stats_before['objects']
        except Exception as e:
            logger.debug(f"Failed to capture GC stats: {e}")

    def stop(self):
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        
        # Record memory delta using tracemalloc
        try:
            mem_after, mem_peak_after = tracemalloc.get_traced_memory()
            self.memory_bytes = mem_after - getattr(self, '_mem_before', 0)
            self.memory_peak_bytes = mem_peak_after - getattr(self, '_mem_peak_before', 0)
        except Exception:
            self.memory_bytes = 0
            self.memory_peak_bytes = 0
        
        # Capture process-level metrics after
        try:
            if self._process:
                mem_info = self._process.memory_info()
                self.memory_after_mb = mem_info.rss / (1024 * 1024)
                self.memory_delta_mb = self.memory_after_mb - self.memory_before_mb
                
                # CPU time
                cpu_times_after = self._process.cpu_times()
                self.cpu_time_user = cpu_times_after.user - self._cpu_times_before.user
                self.cpu_time_system = cpu_times_after.system - self._cpu_times_before.system
                
                # Calculate CPU percent based on actual CPU time used during this request
                # Formula: (cpu_time_used / wall_time) * 100
                total_cpu_time = self.cpu_time_user + self.cpu_time_system
                wall_time = self.end_time - self.start_time
                if wall_time > 0:
                    self.cpu_percent = (total_cpu_time / wall_time) * 100
                else:
                    self.cpu_percent = 0.0
                
                # I/O counters
                io_counters_after = self._process.io_counters()
                self.io_read_bytes = io_counters_after.read_bytes - self._io_counters_before.read_bytes
                self.io_write_bytes = io_counters_after.write_bytes - self._io_counters_before.write_bytes
        except Exception as e:
            logger.debug(f"Failed to capture process metrics after: {e}")
        
        # Capture GC stats after
        try:
            self.gc_stats_after = {
                'collections': [gc.get_count()[i] for i in range(3)],
                'thresholds': gc.get_threshold(),
                'objects': len(gc.get_objects())
            }
            
            # Calculate GC collections that happened during this function
            self.gc_collected = {
                f'gen{i}': max(0, self.gc_stats_after['collections'][i] - self.gc_stats_before['collections'][i])
                for i in range(3)
            }
            
            # Object count analysis
            # Note: gc.get_objects() gives us the CURRENT count of tracked objects
            # The delta shows net change, but doesn't tell us how many were created/destroyed
            # We can only reliably report the net change
            self.object_count_delta = self.gc_stats_after['objects'] - self._obj_count_before
            
            # Be honest about what we can measure:
            # - If delta is positive: we know AT LEAST this many were created (some might have been destroyed too)
            # - If delta is negative: we know AT LEAST this many were destroyed (some might have been created too)
            # - The actual numbers could be higher for both
            if self.object_count_delta > 0:
                # Net increase: at least this many created, unknown destroyed
                self.objects_created = self.object_count_delta
                self.objects_destroyed = 0  # Unknown, could be anything
            elif self.object_count_delta < 0:
                # Net decrease: at least this many destroyed, unknown created
                self.objects_created = 0  # Unknown, could be anything
                self.objects_destroyed = abs(self.object_count_delta)
            else:
                # No net change: could mean nothing happened, or equal creates/destroys
                self.objects_created = 0
                self.objects_destroyed = 0
        except Exception as e:
            logger.debug(f"Failed to capture GC stats after: {e}")

    def add_child(self, child: "FunctionProfile"):
        self.children.append(child)

    def add_query(self, query_info: Dict):
        self.queries.append(query_info)

    def to_dict(self) -> Dict:
        """Convert profile to dict for dashboard/CLI."""
        children = [c.to_dict() for c in self.children]
        # compute total query time for this node + children
        def _total_query_time(node_dict):
            s = 0.0
            for q in node_dict.get('queries', []):
                try:
                    s += float(q.get('time_ms') or 0.0)
                except Exception:
                    pass
            for ch in node_dict.get('children', []):
                s += _total_query_time(ch)
            return s

        d = {
            "func_name": self.func_name,
            "duration_ms": round(self.duration_ms, 2),
            "call_count": self.call_count,
            "queries": self.queries,
            "children": children,
            
            # Memory metrics
            "memory_bytes": int(self.memory_bytes),
            "memory_peak_bytes": int(self.memory_peak_bytes),
            "memory_before_mb": round(self.memory_before_mb, 2),
            "memory_after_mb": round(self.memory_after_mb, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 4),
            
            # GC metrics
            "gc_enabled": self.gc_enabled,
            "gc_collected": self.gc_collected,
            "gc_stats_before": self.gc_stats_before,
            "gc_stats_after": self.gc_stats_after,
            
            # Object tracking
            "objects_created": self.objects_created,
            "objects_destroyed": self.objects_destroyed,
            "object_count_delta": self.object_count_delta,
            
            # CPU and system metrics
            "cpu_percent": round(self.cpu_percent, 2),
            "cpu_time_user": round(self.cpu_time_user, 4),
            "cpu_time_system": round(self.cpu_time_system, 4),
            "thread_count": self.thread_count,
            "io_read_bytes": self.io_read_bytes,
            "io_write_bytes": self.io_write_bytes,
            
            # Source location and error
            "file_path": self.file_path,
            "line_number": self.line_number,
            "error": self.error,
            "stack_trace": self.stack_trace,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
        d['total_query_time_ms'] = round(_total_query_time(d), 4)
        return d


def _get_current_stack():
    """
    Get current profiling stack - works for both sync and async contexts
    """
    # Try async context first (FastAPI, async views)
    async_stack = _async_stack.get()
    if async_stack is not None:
        return async_stack
    
    # Fall back to thread-local (Django, Flask sync)
    if not hasattr(_thread_local, "stack"):
        _thread_local.stack = []
    return _thread_local.stack


def _debug_stack_snapshot(msg: str = ""):
    try:
        stack = _get_current_stack()
        logger.debug("Stack snapshot %s: depth=%d, top=%s", msg, len(stack), stack[-1].func_name if stack else None)
    except Exception:
        logger.debug("Stack snapshot %s: (error fetching stack)", msg, exc_info=True)


def profile(func=None, *, critical_threshold_ms=None):
    """
    Decorator to profile any function (nested safe).
    Tracks function-level timings, nested structure, and ORM query timings.
    Supports both sync and async functions.
    """
    if func is None:
        return lambda f: profile(f, critical_threshold_ms=critical_threshold_ms)

    # Check if function is async
    import asyncio
    import inspect
    is_async = asyncio.iscoroutinefunction(func)

    if is_async:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            stack = _get_current_stack()
            parent = stack[-1] if stack else None

            prof = FunctionProfile(func.__qualname__, parent)
            if parent:
                parent.add_child(prof)

            stack.append(prof)
            prof.start()

            try:
                result = await func(*args, **kwargs)
            finally:
                prof.stop()
                stack.pop()

                # Optional: print critical function log
                threshold = critical_threshold_ms or 100
                if prof.duration_ms >= threshold:
                    logger.warning(
                        "[CRITICAL] %s took %.2fms (calls: %d)",
                        prof.func_name,
                        prof.duration_ms,
                        prof.call_count,
                    )

            return result

        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            stack = _get_current_stack()
            parent = stack[-1] if stack else None

            prof = FunctionProfile(func.__qualname__, parent)
            if parent:
                parent.add_child(prof)

            stack.append(prof)
            prof.start()

            try:
                result = func(*args, **kwargs)
            finally:
                prof.stop()
                stack.pop()

                # Optional: print critical function log
                threshold = critical_threshold_ms or 100
                if prof.duration_ms >= threshold:
                    logger.warning(
                        "[CRITICAL] %s took %.2fms (calls: %d)",
                        prof.func_name,
                        prof.duration_ms,
                        prof.call_count,
                    )

            return result

        return sync_wrapper


def start_watch():
    """Initialize profiling manually for script-based apps."""
    _get_current_stack().clear()
    root = FunctionProfile("ManualSessionRoot")
    _get_current_stack().append(root)
    root.start()
    return root


def stop_watch():
    """Stop manual profiling session."""
    stack = _get_current_stack()
    if not stack:
        return None
    root = stack[0]
    root.stop()
    _get_current_stack().clear()
    return root


def get_request_profile() -> Optional[FunctionProfile]:
    """Return the root FunctionProfile for current thread/request."""
    stack = _get_current_stack()
    return stack[0] if stack else None


# Simple module-level watcher API so CLI and other modules can control profiling.
_global_root: Optional[FunctionProfile] = None
_watching = False


def start() -> FunctionProfile:
    """Start a global manual profiling session."""
    global _global_root, _watching
    _global_root = start_watch()
    _watching = True
    return _global_root


def stop() -> Optional[FunctionProfile]:
    """Stop the global manual profiling session and return the root."""
    global _global_root, _watching
    if not _global_root:
        return None
    root = stop_watch()
    _watching = False
    _global_root = None
    return root


def get_root() -> Optional[FunctionProfile]:
    """Return the current root FunctionProfile (request-local or global)."""
    # Prefer per-request root
    req = get_request_profile()
    if req:
        return req
    return _global_root


def is_watching() -> bool:
    return _watching


def print_profile_tree(profile: FunctionProfile, indent=0):
    """Pretty print function tree with timings (for CLI debug)."""
    spacer = " " * indent
    print(f"{spacer}└── {profile.func_name} [{profile.duration_ms:.2f}ms, calls={profile.call_count}]")
    for q in profile.queries:
        print(f"{spacer}    💾 Query: {q.get('sql', 'N/A')} ({q.get('time_ms', 0):.2f}ms)")
    for child in profile.children:
        print_profile_tree(child, indent + 4)


