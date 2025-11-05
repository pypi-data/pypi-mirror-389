from .views import DjangoPerfwatchView, FlaskPerfwatchView, FastAPIPerfwatchView
from .routes import register_fastapi_routes, register_flask_routes

__all__ = [
    'DjangoPerfwatchView',
    'FlaskPerfwatchView',
    'FastAPIPerfwatchView',
    'register_fastapi_routes',
    'register_flask_routes'
]