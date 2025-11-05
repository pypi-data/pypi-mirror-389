from django.utils.deprecation import MiddlewareMixin
from perfwatch.core.context import set_current_request_id, clear_current_request_id, get_current_request_id
from perfwatch.core.profiler import _get_current_stack, FunctionProfile
from perfwatch.core.critical import CriticalAnalyzer
import logging
import os
import re

logger = logging.getLogger(__name__)
from perfwatch.db import store as db_store
from perfwatch.adapters.django_orm_hook import clear_query_timings

class PerfWatchDjangoMiddleware(MiddlewareMixin):
    """
    Django middleware to profile each request and collect metrics.
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
        r'^/media/',          # Django media files
        r'^/admin/[^/]+/(css|img|js)/',  # Django admin static files
        r'^/_next/',          # Next.js static files
        r'^/__webpack_hmr',   # Webpack HMR
    }

    def __init__(self, get_response, func_threshold_ms=100, query_threshold_ms=50):
        super().__init__(get_response)
        self.func_threshold_ms = func_threshold_ms
        self.query_threshold_ms = query_threshold_ms
        # Compile ignore path patterns
        self.ignore_patterns = [re.compile(pattern) for pattern in self.IGNORE_PATHS]

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

    def process_request(self, request):
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
        if not self.should_track_request(request.path):
            return None

        # Assign unique request ID
        request_id = set_current_request_id()

        # Root FunctionProfile for this request
        root_profile = FunctionProfile(f"Request:{request.path}")
        _get_current_stack().append(root_profile)
        root_profile.start()

        # debug
        try:
            from perfwatch.core.profiler import _debug_stack_snapshot
            _debug_stack_snapshot("after request push")
        except Exception:
            pass

        # Store in request object for optional access
        request.perfwatch_root = root_profile

    def process_response(self, request, response):
        root_profile = getattr(request, "perfwatch_root", None)
        if root_profile:
            # Stop profiling for this request
            try:
                root_profile.stop()
            except Exception:
                pass

            # Ensure stack cleanup
            stack = _get_current_stack()
            if stack:
                try:
                    stack.pop()
                except Exception:
                    pass

            # Attach any adapter-collected queries (e.g., Django ORM) to root_profile
            try:
                from perfwatch.adapters.django_orm_hook import get_query_timings, clear_query_timings
                queries = get_query_timings()
                for q in queries:
                    root_profile.add_query(q)
                # clear adapter storage after attaching
                clear_query_timings()
            except Exception:
                logger.debug("No django orm queries to attach or failed to attach", exc_info=True)

            # Analyze critical functions/queries
            analyzer = CriticalAnalyzer(
                function_threshold_ms=self.func_threshold_ms,
                query_threshold_ms=self.query_threshold_ms,
            )
            critical_info = analyzer.analyze(root_profile)
            logger.info("[PerfWatch][Request %s] Critical Info: %s", request.path, critical_info)

            try:
                from perfwatch.core.profiler import _debug_stack_snapshot
                _debug_stack_snapshot("before persist")
            except Exception:
                pass

                # Persist metrics to DB (best-effort)
            try:
                request_id = getattr(request, 'perfwatch_request_id', None) or get_current_request_id()
                # Get request payload
                request_data = {
                    'method': request.method,
                    'path': request.path,
                    'query_params': request.GET.dict(),
                    'headers': dict(request.headers),
                    'body': request.body.decode() if request.body else None,
                    'client_ip': request.META.get('REMOTE_ADDR'),
                    'user_agent': request.META.get('HTTP_USER_AGENT'),
                    'host': request.get_host()
                }
                
                # Get response data (safely handle different response types)
                response_data = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers) if hasattr(response, 'headers') else {}
                }
                
                # Try to get response content safely
                try:
                    if hasattr(response, 'streaming') and response.streaming:
                        response_data['content'] = '<streaming response>'
                    elif hasattr(response, 'content'):
                        content_length = len(response.content)
                        if content_length > 1048576:  # 1MB limit
                            response_data['content'] = f'<large response: {content_length} bytes>'
                        else:
                            response_data['content'] = response.content.decode('utf-8', errors='ignore')
                    else:
                        response_data['content'] = None
                except Exception:
                    response_data['content'] = '<unable to capture>'
                
                db_store.store_metrics(
                    request_id=request_id,
                    data=root_profile.to_dict(),
                    request_payload=request_data,
                    response_data=response_data
                )
            except Exception:
                logger.exception("Failed to persist perfwatch metrics for request %s", request.path)            # Clear adapter-level query timings
            try:
                clear_query_timings()
            except Exception:
                logger.exception("Failed to clear query timings for request %s", request.path)

        # Clear request context
        clear_current_request_id()
        return response

    def process_exception(self, request, exception):
        # When exception occurs, try to stop and persist profiling similarly to process_response
        root_profile = getattr(request, "perfwatch_root", None)
        if root_profile:
            try:
                root_profile.stop()
            except Exception:
                pass
            try:
                stack = _get_current_stack()
                if stack:
                    stack.pop()
            except Exception:
                pass

            try:
                request_id = getattr(request, 'perfwatch_request_id', None) or get_current_request_id()
                db_store.store_metrics(request_id, root_profile.to_dict())
            except Exception:
                pass

        clear_current_request_id()
