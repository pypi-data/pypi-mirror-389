"""
PerfWatch Library
Python >=3.8
"""

__version__ = "1.0.0"

# CLI entry point
from .cli.main import cli as cli_main

# Core modules
from .core.profiler import FunctionProfile as Profiler, profile
from .core.critical import CriticalAnalyzer

# DB handler
from .db.store import store_metrics, get

# Config
from .config import _config_instance as config

# Adapters
from .adapters.fastapi_adapter import integrate_fastapi
from .adapters.flask_adapter import init_flask_app
from .adapters.django_adapter import PerfWatchDjangoMiddleware

# Dashboard (import lazily - optional)
try:
    from .dashboard.router import router as perf_router
except Exception:
    perf_router = None

__all__ = [
    "cli_main",
    "Profiler",
    "profile",
    "CriticalAnalyzer",
    "store_metrics",
    "get",
    "config",
    "integrate_fastapi",
    "init_flask_app",
    "PerfWatchDjangoMiddleware",
    "perf_router",
    "__version__",
]
