from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from perfwatch.core.context import set_current_request_id, clear_current_request_id
from perfwatch.core.profiler import _get_current_stack, FunctionProfile
from perfwatch.core.critical import CriticalAnalyzer
import os
import logging
import re

from perfwatch.dashboard.routes import register_fastapi_routes

logger = logging.getLogger(__name__)

class PerfWatchFastAPIMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to profile each request and collect metrics.
    """

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

    def __init__(self, app, func_threshold_ms=100, query_threshold_ms=50):
        super().__init__(app)
        self.func_threshold_ms = func_threshold_ms
        self.query_threshold_ms = query_threshold_ms
        # Compile ignore path patterns
        self.ignore_patterns = [re.compile(pattern) for pattern in self.IGNORE_PATHS]
        # Initialize sampling
        self._request_count = 0
        self.sample_rate = 1.0  # Profile 100% of requests by default

    def should_track_request(self, path: str) -> bool:
        """
        Determine if a request should be tracked based on its path
        """
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.match(path):
                return False
                
        # Check file extensions
        ext = os.path.splitext(path)[1].lower()
        if ext in self.STATIC_EXTENSIONS:
            return False
            
        return True

    async def dispatch(self, request: Request, call_next):
        # Skip OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return await call_next(request)
        
        # Check if profiling is enabled in config
        from perfwatch.config import _config_instance
        config_enabled = _config_instance.get('profiling.enabled', False)
        
        # Skip if profiling is disabled in config
        if not config_enabled:
            return await call_next(request)
        
        # Skip if request should not be tracked
        if not self.should_track_request(request.url.path):
            return await call_next(request)
        
        # Sampling: only profile a percentage of requests
        import random
        self._request_count += 1
        if random.random() > self.sample_rate:
            return await call_next(request)

        # Assign unique request ID
        request_id = set_current_request_id()
        
        # Clear any previous SQLAlchemy query timings
        try:
            from perfwatch.adapters.sqlalchemy_hook import clear_query_timings
            clear_query_timings()
        except ImportError:
            pass
        
        # Initialize async context stack for this request
        from perfwatch.core.profiler import _async_stack
        request_stack = []
        _async_stack.set(request_stack)
        
        # Create root profile for this request
        root_profile = FunctionProfile(f"Request:{request.url.path}")
        request_stack.append(root_profile)
        root_profile.start()

        # Process request
        response = await call_next(request)

        # Stop root profiling
        root_profile.stop()
        
        # Clean up async context
        _async_stack.set(None)
        
        # Capture SQLAlchemy queries if available (fallback for queries without function context)
        try:
            from perfwatch.adapters.sqlalchemy_hook import get_query_timings, clear_query_timings
            sqlalchemy_queries = get_query_timings()
            if sqlalchemy_queries:
                # Add queries to root profile
                if not hasattr(root_profile, 'queries'):
                    root_profile.queries = []
                root_profile.queries.extend([
                    {
                        'sql': q.get('sql', ''),
                        'time_ms': q.get('time_ms', 0),
                        'params': q.get('params', []),
                        'rows_affected': 0,
                        'db_type': 'sqlalchemy',
                        'function_name': q.get('function_name', 'Request')
                    }
                    for q in sqlalchemy_queries
                ])
                clear_query_timings()
        except ImportError:
            pass
        
        # Capture MongoDB queries if available (fallback for queries without function context)
        try:
            from perfwatch.adapters.mongo_hook import get_query_timings, clear_query_timings
            mongo_queries = get_query_timings()
            if mongo_queries:
                # Add queries to root profile
                if not hasattr(root_profile, 'queries'):
                    root_profile.queries = []
                root_profile.queries.extend([
                    {
                        'sql': q.get('command', ''),
                        'time_ms': q.get('duration_ms', 0),
                        'params': [],
                        'db_type': 'mongodb',
                        'failed': q.get('failed', False),
                        'function_name': q.get('function_name', 'Request')
                    }
                    for q in mongo_queries
                ])
                clear_query_timings()
        except ImportError:
            pass
        
        # No need to pop - we already cleaned up async context above

        # Analyze critical functions/queries
        analyzer = CriticalAnalyzer(
            function_threshold_ms=self.func_threshold_ms,
            query_threshold_ms=self.query_threshold_ms
        )
        critical_info = analyzer.analyze(root_profile)
        
        # Store metrics in DB
        try:
            from perfwatch.db import store as db_store
            metrics_data = root_profile.to_dict()
            request_data = {
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers),
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent', ''),
                'host': request.headers.get('host', '')
            }
            
            # Get response data (safely handle different response types)
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers) if hasattr(response, 'headers') else {}
            }
            
            # Try to get response body safely
            try:
                if hasattr(response, 'body'):
                    body_bytes = response.body
                    if isinstance(body_bytes, bytes):
                        if len(body_bytes) > 1048576:  # 1MB limit
                            response_data['body'] = f'<large response: {len(body_bytes)} bytes>'
                        else:
                            response_data['body'] = body_bytes.decode('utf-8', errors='ignore')
                    else:
                        response_data['body'] = str(body_bytes)
                else:
                    response_data['body'] = '<streaming or file response>'
            except Exception:
                response_data['body'] = '<unable to capture>'
            
            # Environment info
            environment = (
                os.environ.get('ENV') or 
                os.environ.get('ENVIRONMENT') or 
                os.environ.get('FASTAPI_ENV') or 
                'development'
            )
            
            metrics_data.update({
                'method': request.method,
                'endpoint': request.url.path,
                'status_code': response.status_code,
                'host': request.headers.get('host', ''),
                'client_ip': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent', ''),
                'environment': environment
            })
            db_store.store_metrics(
                request_id=request_id,
                data=metrics_data,
                request_payload=request_data,
                response_data=response_data
            )
        except Exception as e:
            logger.exception("Failed to persist perfwatch metrics for FastAPI request %s", request.url.path)

        # Clear request context
        clear_current_request_id()
        return response


# Helper function to easily add middleware
def integrate_fastapi(app: FastAPI, func_threshold_ms=100, query_threshold_ms=50, auto_profile=True):
    """
    Add PerfWatch FastAPI middleware to the app.
    
    Args:
        app: FastAPI application instance
        func_threshold_ms: Function execution threshold in milliseconds
        query_threshold_ms: Query execution threshold in milliseconds
        auto_profile: If True, automatically wrap all route handlers with @profile decorator
    
    Note:
        To track database queries (SQLAlchemy/MongoDB):
           
        For SQLAlchemy:
            from perfwatch.adapters.sqlalchemy_hook import attach_sqlalchemy_listeners
            attach_sqlalchemy_listeners(engine)
        
        For MongoDB:
            from perfwatch.adapters.mongo_hook import attach_mongo_listeners
            attach_mongo_listeners(client)
        
        Example:
            from fastapi import FastAPI
            from perfwatch.adapters.fastapi_adapter import integrate_fastapi
            
            app = FastAPI()
            
            # Define your routes first
            @app.get("/users")
            async def get_users():
                users = await db.query(User).all()
                return users
            
            # Then integrate perfwatch (with auto_profile=True, routes are auto-wrapped)
            integrate_fastapi(app, auto_profile=True)
    """
    from perfwatch.core.profiler import profile
    import inspect
    
    # Auto-wrap route handlers with @profile decorator
    if auto_profile:
        try:
            from fastapi.routing import APIRoute
        except ImportError:
            from starlette.routing import Route as APIRoute
        
        wrapped_count = 0
        for route in app.routes:
            # Check if it's an API route with an endpoint
            if not isinstance(route, APIRoute):
                continue
                
            if not hasattr(route, 'endpoint') or not callable(route.endpoint):
                continue
            
            endpoint = route.endpoint
            
            # Skip if already wrapped or is a perfwatch/docs route
            if (hasattr(endpoint, '__wrapped__') or 
                getattr(endpoint, '__perfwatch_profiled__', False) or
                route.path.startswith('/perfwatch') or
                route.path.startswith('/docs') or
                route.path.startswith('/openapi.json') or
                route.path.startswith('/redoc')):
                continue
            
            # Wrap the endpoint with @profile
            try:
                if inspect.iscoroutinefunction(endpoint):
                    # Async endpoint
                    wrapped = profile(endpoint)
                    wrapped.__perfwatch_profiled__ = True
                    route.endpoint = wrapped
                    wrapped_count += 1
                elif callable(endpoint):
                    # Sync endpoint
                    wrapped = profile(endpoint)
                    wrapped.__perfwatch_profiled__ = True
                    route.endpoint = wrapped
                    wrapped_count += 1
            except Exception as e:
                logger.warning(f"Failed to wrap endpoint {route.path}: {e}")
        
        logger.info(f"PerfWatch: Auto-profiled {wrapped_count} FastAPI routes")
    
    app.add_middleware(
        PerfWatchFastAPIMiddleware,
        func_threshold_ms=func_threshold_ms,
        query_threshold_ms=query_threshold_ms
    )
    register_fastapi_routes(app)
    return app
