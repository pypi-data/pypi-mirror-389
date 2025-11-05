from flask import request, g
from perfwatch.core.context import set_current_request_id, clear_current_request_id, get_current_request_id
from perfwatch.core.profiler import _get_current_stack, FunctionProfile
from perfwatch.core.critical import CriticalAnalyzer
from perfwatch.dashboard.routes import register_flask_routes
from perfwatch.db import store as db_store
from perfwatch.adapters.django_orm_hook import clear_query_timings
import os
import logging
import re

logger = logging.getLogger(__name__)

# Static file extensions to ignore
STATIC_EXTENSIONS = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot'}

# Special paths to ignore
IGNORE_PATHS = {
    r'^/\.well-known/',  # Chrome DevTools and other .well-known paths
    r'^/favicon\.ico$',   # Favicon requests
    r'^/static/',         # Static file directories
    r'^/assets/',         # Common assets directory
    r'^/perfwatch/',      # PerfWatch's own endpoints
    r'^/_next/',          # Next.js static files
    r'^/__webpack_hmr',   # Webpack HMR
}

# Compile ignore path patterns once
IGNORE_PATTERNS = [re.compile(pattern) for pattern in IGNORE_PATHS]

def should_track_request(path: str) -> bool:
    """
    Determine if a request should be tracked based on its path
    """
    # Check against ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern.match(path):
            return False
            
    # Check file extensions
    ext = os.path.splitext(path)[1].lower()
    if ext in STATIC_EXTENSIONS:
        return False
        
    return True

def init_flask_app(app, func_threshold_ms=100, query_threshold_ms=50, auto_profile=True):
    """
    Integrate PerfWatch profiling with Flask app.
    
    Args:
        app: Flask application instance
        func_threshold_ms: Function execution threshold in milliseconds
        query_threshold_ms: Query execution threshold in milliseconds
        auto_profile: If True, automatically wrap all view functions with @profile decorator
    """
    
    # Configure template folder for PerfWatch
    import os
    from jinja2 import ChoiceLoader, FileSystemLoader
    
    perfwatch_template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'dashboard', 
        'templates'
    )
    
    # Add PerfWatch templates to Flask's Jinja loader
    my_loader = FileSystemLoader(perfwatch_template_dir)
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        my_loader,
    ])
    
    # Auto-wrap all view functions with @profile decorator
    if auto_profile:
        from perfwatch.core.profiler import profile
        
        wrapped_count = 0
        for endpoint, view_func in list(app.view_functions.items()):
            # Skip if already wrapped or is a perfwatch/static endpoint
            if (hasattr(view_func, '__wrapped__') or 
                getattr(view_func, '__perfwatch_profiled__', False) or
                endpoint.startswith('perfwatch.') or
                endpoint.startswith('static')):
                continue
            
            # Wrap with @profile
            try:
                wrapped = profile(view_func)
                wrapped.__perfwatch_profiled__ = True
                app.view_functions[endpoint] = wrapped
                wrapped_count += 1
            except Exception as e:
                logger.warning(f"Failed to wrap view function {endpoint}: {e}")
        
        logger.info(f"PerfWatch: Auto-profiled {wrapped_count} Flask view functions")

    @app.before_request
    def before_request():
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Check if profiling is enabled in config
        from perfwatch.config import _config_instance
        config_enabled = _config_instance.get('profiling.enabled', False)
        
        # Skip if profiling is disabled in config
        if not config_enabled:
            return None
        
        # Skip profiling if request should not be tracked
        if not should_track_request(request.path):
            return None

        # Assign unique request ID
        request_id = set_current_request_id()

        # Root FunctionProfile for request
        root_profile = FunctionProfile(f"Request:{request.path}")
        _get_current_stack().append(root_profile)
        root_profile.start()

        # Store in flask.g for optional access
        g.perfwatch_root = root_profile

    @app.after_request
    def after_request(response):
        # Stop root profiling
        root_profile = getattr(g, "perfwatch_root", None)
        if root_profile:
            try:
                root_profile.stop()
            except Exception:
                pass

            try:
                _get_current_stack().pop()
            except Exception:
                pass

            # Analyze critical functions/queries
            # Attach any remaining queries from thread-local (fallback for queries without function context)
            try:
                from perfwatch.adapters.sqlalchemy_hook import get_query_timings, clear_query_timings
                queries = get_query_timings()
                for q in queries:
                    root_profile.add_query(q)
                clear_query_timings()
            except Exception:
                logger.debug("No SQLAlchemy queries to attach or failed to attach", exc_info=True)

            analyzer = CriticalAnalyzer(
                function_threshold_ms=func_threshold_ms,
                query_threshold_ms=query_threshold_ms,
            )
            critical_info = analyzer.analyze(root_profile)

            # Persist metrics (best-effort)
            try:
                request_id = getattr(g, 'perfwatch_request_id', None) or get_current_request_id()
                # Collect request metadata
                # Get request payload
                request_data = {
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.args),
                    'headers': dict(request.headers),
                    'body': request.get_data(as_text=True),
                    'client_ip': request.remote_addr,
                    'user_agent': request.user_agent.string,
                    'host': request.host
                }
                
                # Get response data (safely handle different response types)
                response_data = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                
                # Try to get response content, but handle file/stream responses
                try:
                    # Check if response is in direct passthrough mode (file download)
                    if hasattr(response, 'direct_passthrough') and response.direct_passthrough:
                        response_data['content'] = '<binary file or stream>'
                    elif hasattr(response, 'get_data'):
                        # Only get data if it's safe (small responses)
                        content_length = response.headers.get('Content-Length', type=int)
                        if content_length and content_length > 1048576:  # 1MB limit
                            response_data['content'] = f'<large response: {content_length} bytes>'
                        else:
                            response_data['content'] = response.get_data(as_text=True)
                    else:
                        response_data['content'] = None
                except Exception:
                    response_data['content'] = '<unable to capture>'
                
                # Get environment info
                environment = (
                    os.environ.get('ENV') or 
                    os.environ.get('ENVIRONMENT') or 
                    os.environ.get('FLASK_ENV') or 
                    'development'
                )
                metrics_data = root_profile.to_dict()
                metrics_data.update({
                    'method': request.method,
                    'endpoint': request.path,
                    'status_code': response.status_code,
                    'environment': environment
                })
                
                db_store.store_metrics(
                    request_id=request_id,
                    data=metrics_data,
                    request_payload=request_data,
                    response_data=response_data
                )
            except Exception:
                logger.exception("Failed to persist perfwatch metrics for Flask request %s", request.path)

            # Clear adapter-level query timings
            try:
                clear_query_timings()
            except Exception:
                logger.exception("Failed to clear query timings for Flask request %s", request.path)

        # Clear request context
        clear_current_request_id()
        return response

    register_flask_routes(app)
    
    # Mount static files for PerfWatch
    from flask import send_from_directory
    
    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'dashboard', 
        'static'
    )
    
    @app.route('/perfwatch/static/<path:filename>')
    def perfwatch_static(filename):
        """Serve static files for PerfWatch dashboard"""
        response = send_from_directory(static_dir, filename)
        # Disable cache in development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return app
