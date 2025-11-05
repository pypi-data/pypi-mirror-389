from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePerfwatchView(ABC):
    """Base class for framework-specific perfwatch views"""
    
    @abstractmethod
    def render_dashboard(self, request=None, **kwargs):
        """Render the dashboard template"""
        pass

    @abstractmethod
    def get_api_stats(self, timeframe="24h", severity="all") -> Dict[str, Any]:
        """Get API statistics
        
        Args:
            timeframe: Time range to look back (1h, 6h, 24h, 7d)
            severity: Filter by severity (all, critical, warning, normal)
        """
        pass

    @abstractmethod
    def get_api_details(self, request, id: int) -> Dict[str, Any]:
        """Get detailed profiling data for a specific API call - requires authentication"""
        from perfwatch.core.store import PerfwatchStore
        from perfwatch.dashboard.auth import verify_session
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JSONResponse({'error': 'Unauthorized'}, status_code=401)

class DjangoPerfwatchView(BasePerfwatchView):
    """Django-specific implementation of perfwatch views"""
    
    def __init__(self):
        import os
        import sys
        from django.template.loader import render_to_string
        from django.http import JsonResponse, HttpResponse, FileResponse
        from django.conf import settings
        from django.contrib.staticfiles import finders

        # Get the current directory where views.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add our templates directory to Django's template dirs
        template_dir = os.path.join(current_dir, 'templates')
        
        # Debug: Print template directory path (will help diagnose issues)
        print(f"[PerfWatch] Template directory: {template_dir}")
        print(f"[PerfWatch] Template exists: {os.path.exists(template_dir)}")
        if os.path.exists(template_dir):
            print(f"[PerfWatch] Template contents: {os.listdir(template_dir)}")
        
        # Configure templates
        if not hasattr(settings, 'TEMPLATES'):
            settings.TEMPLATES = []

        # Check for existing Django template backend
        django_backend = None
        for template_config in settings.TEMPLATES:
            if template_config.get('BACKEND') == 'django.template.backends.django.DjangoTemplates':
                django_backend = template_config
                break

        if django_backend:
            # Add our template dir to existing Django backend if not already there
            if 'DIRS' not in django_backend:
                django_backend['DIRS'] = []
            if template_dir not in django_backend['DIRS']:
                django_backend['DIRS'].insert(0, template_dir)  # Insert at beginning for priority
                print(f"[PerfWatch] Added template dir to existing backend")
                
            # Ensure required context processors are present
            if 'OPTIONS' not in django_backend:
                django_backend['OPTIONS'] = {}
            if 'context_processors' not in django_backend['OPTIONS']:
                django_backend['OPTIONS']['context_processors'] = []
            
            required_processors = [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
            ]
            for processor in required_processors:
                if processor not in django_backend['OPTIONS']['context_processors']:
                    django_backend['OPTIONS']['context_processors'].append(processor)
        else:
            # No Django backend exists, create new one with unique name
            print(f"[PerfWatch] Creating new Django template backend")
            settings.TEMPLATES.append({
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'NAME': 'perfwatch_django',  # Add unique name
                'DIRS': [template_dir],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.template.context_processors.static',
                    ],
                },
            })

        # Configure static files
        self.static_dir = os.path.join(current_dir, 'static')
        self.static_url = '/perfwatch/static/'

        if not hasattr(settings, 'STATIC_URL'):
            settings.STATIC_URL = '/static/'

        # Configure STATICFILES_DIRS if needed
        if not hasattr(settings, 'STATICFILES_DIRS'):
            settings.STATICFILES_DIRS = []
        
        if self.static_dir not in settings.STATICFILES_DIRS:
            settings.STATICFILES_DIRS.append(self.static_dir)

        # Store template loader functions
        self.render_to_string = render_to_string
        self.JsonResponse = JsonResponse
        self.HttpResponse = HttpResponse
        self.FileResponse = FileResponse
        
    def _render_login_page(self):
        """Render simple login page"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PerfWatch Login</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl w-96">
                <div class="text-center mb-6">
                    <i class="fas fa-gauge-high text-4xl text-blue-500 mb-2"></i>
                    <h1 class="text-2xl font-bold">PerfWatch</h1>
                    <p class="text-gray-400 text-sm">Dashboard Login</p>
                </div>
                <form id="loginForm">
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2">Username</label>
                        <input type="text" id="username" class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none" required>
                    </div>
                    <div class="mb-6">
                        <label class="block text-sm font-medium mb-2">Password</label>
                        <input type="password" id="password" class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none" required>
                    </div>
                    <div id="error" class="mb-4 text-red-400 text-sm hidden"></div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded">
                        Login
                    </button>
                </form>
            </div>
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
            <script>
                $('#loginForm').submit(async function(e) {
                    e.preventDefault();
                    const username = $('#username').val();
                    const password = $('#password').val();
                    
                    try {
                        const response = await fetch('/perfwatch/api/login', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username, password})
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            window.location.href = '/perfwatch/dashboard/';
                        } else {
                            $('#error').text(data.error || 'Login failed').removeClass('hidden');
                        }
                    } catch (err) {
                        $('#error').text('Network error').removeClass('hidden');
                    }
                });
            </script>
        </body>
        </html>
        '''

    def serve_static_file(self, request, path):
        """Serve static files directly"""
        import os
        import mimetypes
        from django.http import FileResponse, HttpResponseNotFound
        
        # Construct the full path to the requested file
        full_path = os.path.join(self.static_dir, path)
        
        # Security check - ensure the path is within our static directory
        try:
            full_path = os.path.abspath(full_path)
            if not full_path.startswith(os.path.abspath(self.static_dir)):
                return HttpResponseNotFound()
        except:
            return HttpResponseNotFound()
        
        # Check if file exists
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return HttpResponseNotFound()
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(full_path)
        
        # Open and serve the file
        return FileResponse(open(full_path, 'rb'), content_type=content_type)

    def render_dashboard(self, request=None, **kwargs):
        """Render dashboard for Django - requires authentication"""
        from perfwatch.dashboard.auth import verify_session
        import os
        
        # Check authentication
        session_id = request.COOKIES.get('perfwatch_session') if request else None
        if not session_id or not verify_session(session_id):
            # Return login page or redirect
            return self.HttpResponse(self._render_login_page(), content_type='text/html')
        
        # User is authenticated, show dashboard
        context = {
            'perfwatch_static_url': self.static_url,
            **kwargs
        }
        
        # Try to render using Django's template system first
        try:
            return self.HttpResponse(
                self.render_to_string('perfwatch/dashboard.html', context, request=request),
                content_type='text/html'
            )
        except Exception as e:
            # If Django template loader fails, load template directly from file
            print(f"[PerfWatch] Django template loader failed: {e}")
            print(f"[PerfWatch] Attempting direct file load...")
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(current_dir, 'templates', 'perfwatch', 'dashboard.html')
            
            print(f"[PerfWatch] Template path: {template_path}")
            print(f"[PerfWatch] Template exists: {os.path.exists(template_path)}")
            
            if os.path.exists(template_path):
                # Load template directly and do simple string replacement
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Simple context replacement (for basic variables)
                for key, value in context.items():
                    template_content = template_content.replace(f'{{{{ {key} }}}}', str(value))
                
                return self.HttpResponse(template_content, content_type='text/html')
            else:
                return self.HttpResponse(
                    f"<h1>Template Error</h1><p>Template not found at: {template_path}</p>",
                    content_type='text/html',
                    status=500
                )

    def get_api_stats(self, request) -> Dict[str, Any]:
        """Get API statistics for Django"""
        from perfwatch.core.store import get_api_stats
        from perfwatch.dashboard.auth import verify_session
        from datetime import datetime
        
        # Check authentication
        session_id = request.COOKIES.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Parse parameters
        timeframe = request.GET.get('timeframe', '24h')
        severity = request.GET.get('severity', 'all')
        search = request.GET.get('search', '').strip()
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Pagination
        try:
            page = max(1, int(request.GET.get('page', 1)))
            page_size = min(100, max(10, int(request.GET.get('page_size', 10))))
        except (ValueError, TypeError):
            page = 1
            page_size = 10
        
        # Validation
        if timeframe not in ['1h', '6h', '24h', '7d', '30d', 'custom']:
            timeframe = '24h'
        if severity not in ['all', 'critical', 'warning', 'normal']:
            severity = 'all'
        if len(search) > 200:
            search = search[:200]
        
        # Handle custom date range
        start_timestamp = None
        end_timestamp = None
        
        if timeframe == 'custom' and start_date and end_date:
            try:
                # Parse datetime-local format (YYYY-MM-DDTHH:MM)
                # Add seconds if not present
                if len(start_date) == 16:
                    start_date += ':00'
                if len(end_date) == 16:
                    end_date += ':00'
                
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                
                start_timestamp = int(start_dt.timestamp())
                end_timestamp = int(end_dt.timestamp())
                
                print(f"🔵 Django Custom Date Range:")
                print(f"   Input: {request.GET.get('start_date')} to {request.GET.get('end_date')}")
                print(f"   Parsed: {start_dt} to {end_dt}")
                print(f"   Timestamps: {start_timestamp} to {end_timestamp}")
            except (ValueError, AttributeError) as e:
                print(f"❌ Django Date parsing error: {e}")
                # Invalid date format, fall back to 24h
                timeframe = '24h'
        
        # Get stats (Django)
        print(f"🔵 Django Calling get_api_stats:")
        print(f"   timeframe: {timeframe}")
        print(f"   start_timestamp: {start_timestamp}")
        print(f"   end_timestamp: {end_timestamp}")
        
        if start_timestamp and end_timestamp:
            stats = get_api_stats(start_time=start_timestamp, end_time=end_timestamp, search=search)
        else:
            hours = {'1h': 1, '6h': 6, '24h': 24, '7d': 168, '30d': 720}.get(timeframe, 24)
            stats = get_api_stats(hours=hours, search=search)
        
        # Filter by severity
        if severity != 'all' and stats['heaviest_apis']:
            stats['heaviest_apis'] = [
                api for api in stats['heaviest_apis'] 
                if api['severity'] == severity
            ]
        
        # Pagination
        all_apis = stats['heaviest_apis']
        total_count = len(all_apis)
        total_pages = (total_count + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_apis = all_apis[start_idx:end_idx]
        
        stats['heaviest_apis'] = paginated_apis
        stats['pagination'] = {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
            
        return self.JsonResponse(stats)

    def get_api_details(self, request, api_id: str) -> Dict[str, Any]:
        """Get API details for Django - requires authentication"""
        from perfwatch.core.store import get_api_details
        from perfwatch.dashboard.auth import verify_session
        
        # Check authentication - redirect to login if unauthorized
        session_id = request.COOKIES.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JsonResponse({'error': 'Unauthorized', 'redirect': '/perfwatch/dashboard/'}, status=401)
        
        return self.JsonResponse(get_api_details(api_id))
    
    def login(self, request) -> Dict[str, Any]:
        """Handle login for Django"""
        from perfwatch.dashboard.auth import PerfWatchAuth, create_session
        import json
        
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                
                if not username or not password:
                    return self.JsonResponse({'error': 'Username and password required'}, status=400)
                
                if PerfWatchAuth.verify_password(username, password):
                    session_id = create_session(username)
                    response = self.JsonResponse({'success': True, 'username': username})
                    # 15 minutes = 900 seconds
                    response.set_cookie('perfwatch_session', session_id, httponly=True, max_age=900, samesite='Lax')
                    return response
                else:
                    return self.JsonResponse({'error': 'Invalid credentials'}, status=401)
            except Exception as e:
                return self.JsonResponse({'error': str(e)}, status=400)
        
        return self.JsonResponse({'error': 'Method not allowed'}, status=405)
    
    def logout(self, request) -> Dict[str, Any]:
        """Handle logout for Django"""
        from perfwatch.dashboard.auth import destroy_session
        
        session_id = request.COOKIES.get('perfwatch_session')
        if session_id:
            destroy_session(session_id)
        
        response = self.JsonResponse({'success': True})
        response.delete_cookie('perfwatch_session')
        return response
    
    def check_auth(self, request) -> Dict[str, Any]:
        """Check if user is authenticated"""
        from perfwatch.dashboard.auth import verify_session
        
        session_id = request.COOKIES.get('perfwatch_session')
        if session_id:
            username = verify_session(session_id)
            if username:
                return self.JsonResponse({'authenticated': True, 'username': username})
        
        return self.JsonResponse({'authenticated': False}, status=401)
    
    def toggle_profiling(self, request) -> Dict[str, Any]:
        """Toggle profiling on/off - requires authentication (Django)"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        
        session_id = request.COOKIES.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JsonResponse({'error': 'Unauthorized'}, status=401)
        
        current_status = _config_instance.get('profiling.enabled', False)
        new_status = not current_status
        _config_instance.set('profiling.enabled', new_status)
        
        return self.JsonResponse({
            'success': True,
            'profiling_enabled': new_status,
            'message': f"Profiling {'enabled' if new_status else 'disabled'}"
        })
    
    def get_profiling_status(self, request) -> Dict[str, Any]:
        """Get current profiling status - requires authentication (Django)"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        
        session_id = request.COOKIES.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JsonResponse({'error': 'Unauthorized'}, status=401)
        
        status = _config_instance.get('profiling.enabled', False)
        return self.JsonResponse({'profiling_enabled': status})

class FlaskPerfwatchView(BasePerfwatchView):
    """Flask-specific implementation of perfwatch views"""
    
    def __init__(self):
        from flask import render_template, jsonify, request, make_response
        self.render_template = render_template
        self.jsonify = jsonify
        self.request = request
        self.make_response = make_response

    def render_dashboard(self, request=None, **kwargs):
        """Render dashboard for Flask - requires authentication"""
        from perfwatch.dashboard.auth import verify_session
        from flask import request as flask_request
        
        # Check authentication
        session_id = flask_request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            # Return login page
            return self._render_login_page()
        
        return self.render_template('perfwatch/dashboard.html', 
                                  request=request,
                                  perfwatch_static_url='/perfwatch/static/',
                                  flask_static=True,
                                  **kwargs)

    def get_api_stats(self) -> Dict[str, Any]:
        """Get API statistics for Flask"""
        from flask import request
        from perfwatch.core.store import get_api_stats
        from perfwatch.dashboard.auth import verify_session
        from datetime import datetime
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.jsonify({'error': 'Unauthorized'}), 401
        
        # Parse parameters
        timeframe = request.args.get('timeframe', '24h')
        severity = request.args.get('severity', 'all')
        search = request.args.get('search', '').strip()
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Pagination
        try:
            page = max(1, int(request.args.get('page', 1)))
            page_size = min(100, max(10, int(request.args.get('page_size', 10))))
        except (ValueError, TypeError):
            page = 1
            page_size = 10
        
        # Validation
        if timeframe not in ['1h', '6h', '24h', '7d', '30d', 'custom']:
            timeframe = '24h'
        if severity not in ['all', 'critical', 'warning', 'normal']:
            severity = 'all'
        if len(search) > 200:
            search = search[:200]
        
        # Handle custom date range
        start_timestamp = None
        end_timestamp = None
        
        if timeframe == 'custom' and start_date and end_date:
            try:
                # Parse datetime-local format (YYYY-MM-DDTHH:MM)
                # Add seconds if not present
                if len(start_date) == 16:
                    start_date += ':00'
                if len(end_date) == 16:
                    end_date += ':00'
                
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                
                start_timestamp = int(start_dt.timestamp())
                end_timestamp = int(end_dt.timestamp())
                
                print(f"🟢 Flask Custom Date Range:")
                print(f"   Input: {request.args.get('start_date')} to {request.args.get('end_date')}")
                print(f"   Parsed: {start_dt} to {end_dt}")
                print(f"   Timestamps: {start_timestamp} to {end_timestamp}")
            except (ValueError, AttributeError) as e:
                print(f"❌ Flask Date parsing error: {e}")
                # Invalid date format, fall back to 24h
                timeframe = '24h'
        
        # Get stats (Flask)
        print(f"🟢 Flask Calling get_api_stats:")
        print(f"   timeframe: {timeframe}")
        print(f"   start_timestamp: {start_timestamp}")
        print(f"   end_timestamp: {end_timestamp}")
        
        if start_timestamp and end_timestamp:
            stats = get_api_stats(start_time=start_timestamp, end_time=end_timestamp, search=search)
        else:
            hours = {'1h': 1, '6h': 6, '24h': 24, '7d': 168, '30d': 720}.get(timeframe, 24)
            stats = get_api_stats(hours=hours, search=search)
        
        # Filter by severity
        if severity != 'all' and stats['heaviest_apis']:
            stats['heaviest_apis'] = [
                api for api in stats['heaviest_apis'] 
                if api['severity'] == severity
            ]
        
        # Pagination
        all_apis = stats['heaviest_apis']
        total_count = len(all_apis)
        total_pages = (total_count + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_apis = all_apis[start_idx:end_idx]
        
        stats['heaviest_apis'] = paginated_apis
        stats['pagination'] = {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
            
        return self.jsonify(stats)

    def get_api_details(self, api_id: str) -> Dict[str, Any]:
        """Get API details for Flask - requires authentication"""
        from perfwatch.core.store import get_api_details
        from perfwatch.dashboard.auth import verify_session
        from flask import request
        
        # Check authentication - redirect to login if unauthorized
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.jsonify({'error': 'Unauthorized', 'redirect': '/perfwatch/dashboard'}), 401
        
        return self.jsonify(get_api_details(api_id))
    
    def login(self):
        """Handle login for Flask"""
        from perfwatch.dashboard.auth import PerfWatchAuth, create_session
        from flask import request
        
        if request.method == 'POST':
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return self.jsonify({'error': 'Username and password required'}), 400
            
            if PerfWatchAuth.verify_password(username, password):
                session_id = create_session(username)
                response = self.make_response(self.jsonify({'success': True, 'username': username}))
                # 15 minutes = 900 seconds
                response.set_cookie('perfwatch_session', session_id, httponly=True, max_age=900, samesite='Lax')
                return response
            else:
                return self.jsonify({'error': 'Invalid credentials'}), 401
        
        return self.jsonify({'error': 'Method not allowed'}), 405
    
    def logout(self):
        """Handle logout for Flask"""
        from perfwatch.dashboard.auth import destroy_session
        from flask import request
        
        session_id = request.cookies.get('perfwatch_session')
        if session_id:
            destroy_session(session_id)
        
        response = self.make_response(self.jsonify({'success': True}))
        response.delete_cookie('perfwatch_session')
        return response
    
    def check_auth(self):
        """Check if user is authenticated"""
        from perfwatch.dashboard.auth import verify_session
        from flask import request
        
        session_id = request.cookies.get('perfwatch_session')
        if session_id:
            username = verify_session(session_id)
            if username:
                return self.jsonify({'authenticated': True, 'username': username})
        
        return self.jsonify({'authenticated': False}), 401
    
    def toggle_profiling(self):
        """Toggle profiling on/off - requires authentication (Flask)"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        from flask import request
        
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.jsonify({'error': 'Unauthorized'}), 401
        
        current_status = _config_instance.get('profiling.enabled', False)
        new_status = not current_status
        _config_instance.set('profiling.enabled', new_status)
        
        return self.jsonify({
            'success': True,
            'profiling_enabled': new_status,
            'message': f"Profiling {'enabled' if new_status else 'disabled'}"
        })
    
    def get_profiling_status(self):
        """Get current profiling status - requires authentication (Flask)"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        from flask import request
        
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.jsonify({'error': 'Unauthorized'}), 401
        
        status = _config_instance.get('profiling.enabled', False)
        return self.jsonify({'profiling_enabled': status})
    
    def _render_login_page(self):
        """Render simple login page for Flask"""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PerfWatch Login</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl w-96">
                <div class="text-center mb-6">
                    <i class="fas fa-gauge-high text-4xl text-blue-500 mb-2"></i>
                    <h1 class="text-2xl font-bold">PerfWatch</h1>
                    <p class="text-gray-400 text-sm">Dashboard Login</p>
                </div>
                <form id="loginForm">
                    <div class="mb-4">
                        <label class="block text-sm font-medium mb-2">Username</label>
                        <input type="text" id="username" class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none" required>
                    </div>
                    <div class="mb-6">
                        <label class="block text-sm font-medium mb-2">Password</label>
                        <input type="password" id="password" class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none" required>
                    </div>
                    <div id="error" class="mb-4 text-red-400 text-sm hidden"></div>
                    <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded">
                        Login
                    </button>
                </form>
            </div>
            <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
            <script>
                $('#loginForm').submit(async function(e) {
                    e.preventDefault();
                    const username = $('#username').val();
                    const password = $('#password').val();
                    
                    try {
                        const response = await fetch('/perfwatch/api/login', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username, password})
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            window.location.href = '/perfwatch/dashboard/';
                        } else {
                            $('#error').text(data.error || 'Login failed').removeClass('hidden');
                        }
                    } catch (err) {
                        $('#error').text('Network error').removeClass('hidden');
                    }
                });
            </script>
        </body>
        </html>
        '''

class FastAPIPerfwatchView(BasePerfwatchView):
    """FastAPI-specific implementation of perfwatch views"""
    
    def __init__(self):
        import os
        from fastapi.templating import Jinja2Templates
        from fastapi.responses import JSONResponse, HTMLResponse
        from fastapi.staticfiles import StaticFiles
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(current_dir, 'templates')
        static_dir = os.path.join(current_dir, 'static')
        self.templates = Jinja2Templates(directory=template_dir)
        self.static_url = "/perfwatch/static"
        self.static_files = StaticFiles(directory=static_dir)
        self.JSONResponse = JSONResponse
        self.HTMLResponse = HTMLResponse

    def render_dashboard(self, request, **kwargs):
        """Render dashboard for FastAPI - requires authentication"""
        from perfwatch.dashboard.auth import verify_session
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            # Return login page
            return self.HTMLResponse(content=self._render_login_page())
        
        return self.templates.TemplateResponse(
            "perfwatch/dashboard.html",
            {
                "request": request,
                "perfwatch_static_url": self.static_url + "/",
                **kwargs
            }
        )

    def get_api_stats(self, request, timeframe: str = "24h", severity: str = "all", search: str = "", page: int = 1, page_size: int = 20, start_date: str = "", end_date: str = "") -> Dict[str, Any]:
        """Get API statistics for FastAPI"""
        from perfwatch.core.store import get_api_stats
        from perfwatch.dashboard.auth import verify_session
        from datetime import datetime
        from fastapi import Query
        
        # Extract query parameters manually since FastAPI might not bind them automatically
        query_params = dict(request.query_params)
        start_date = query_params.get('start_date', '')
        end_date = query_params.get('end_date', '')
        
        print(f"🟣 FastAPI RAW INPUT:")
        print(f"   query_params: {query_params}")
        print(f"   timeframe: {timeframe}")
        print(f"   start_date: '{start_date}'")
        print(f"   end_date: '{end_date}'")
        print(f"   Type start_date: {type(start_date)}")
        print(f"   Len start_date: {len(start_date)}")
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JSONResponse({'error': 'Unauthorized'}, status_code=401)
        
        # Validation
        if timeframe not in ['1h', '6h', '24h', '7d', '30d', 'custom']:
            timeframe = '24h'
        if severity not in ['all', 'critical', 'warning', 'normal']:
            severity = 'all'
        
        search = search.strip()
        if len(search) > 200:
            search = search[:200]
        
        page = max(1, page)
        page_size = min(100, max(10, page_size))
        
        print(f"🟣 FastAPI RAW INPUT:")
        print(f"   timeframe: {timeframe}")
        print(f"   start_date: '{start_date}'")
        print(f"   end_date: '{end_date}'")
        print(f"   Type start_date: {type(start_date)}")
        print(f"   Len start_date: {len(start_date)}")
        
        # Handle custom date range
        start_timestamp = None
        end_timestamp = None
        
        if timeframe == 'custom' and start_date and end_date:
            try:
                # Parse datetime-local format (YYYY-MM-DDTHH:MM)
                # Add seconds if not present
                if len(start_date) == 16:
                    start_date += ':00'
                if len(end_date) == 16:
                    end_date += ':00'
                
                start_dt = datetime.fromisoformat(start_date)
                end_dt = datetime.fromisoformat(end_date)
                
                start_timestamp = int(start_dt.timestamp())
                end_timestamp = int(end_dt.timestamp())
                
                print(f"🟣 FastAPI Custom Date Range:")
                print(f"   Input: {start_date} to {end_date}")
                print(f"   Parsed: {start_dt} to {end_dt}")
                print(f"   Timestamps: {start_timestamp} to {end_timestamp}")
            except (ValueError, AttributeError) as e:
                print(f"❌ FastAPI Date parsing error: {e}")
                # Invalid date format, fall back to 24h
                timeframe = '24h'
        
        # Get stats (FastAPI)
        print(f"🟣 FastAPI Calling get_api_stats:")
        print(f"   timeframe: {timeframe}")
        print(f"   start_timestamp: {start_timestamp}")
        print(f"   end_timestamp: {end_timestamp}")
        
        if start_timestamp and end_timestamp:
            stats = get_api_stats(start_time=start_timestamp, end_time=end_timestamp, search=search)
        else:
            hours = {'1h': 1, '6h': 6, '24h': 24, '7d': 168, '30d': 720}.get(timeframe, 24)
            stats = get_api_stats(hours=hours, search=search)        # Filter by severity
        if severity != 'all' and stats['heaviest_apis']:
            stats['heaviest_apis'] = [
                api for api in stats['heaviest_apis'] 
                if api['severity'] == severity
            ]
        
        # Pagination
        all_apis = stats['heaviest_apis']
        total_count = len(all_apis)
        total_pages = (total_count + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_apis = all_apis[start_idx:end_idx]
        
        stats['heaviest_apis'] = paginated_apis
        stats['pagination'] = {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
            
        return self.JSONResponse(stats)

    def get_api_details(self, request, id: int) -> Dict[str, Any]:
        """Get detailed profiling data for a specific API call - requires authentication"""
        from perfwatch.core.store import PerfwatchStore
        from perfwatch.dashboard.auth import verify_session
        
        # Check authentication - redirect to login if unauthorized
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JSONResponse({'error': 'Unauthorized', 'redirect': '/perfwatch/dashboard'}, status_code=401)
        
        store = PerfwatchStore()
        details = store.get_api_details(id)
        return self.JSONResponse(details)
    
    def login(self, request, username: str, password: str) -> Dict[str, Any]:
        """Handle login for FastAPI"""
        from perfwatch.dashboard.auth import PerfWatchAuth, create_session
        
        auth = PerfWatchAuth()
        if not auth.verify_password(username, password):
            return self.JSONResponse({'error': 'Invalid credentials'}, status_code=401)
        
        # Create session
        session_id = create_session(username)
        
        # Create response with cookie
        response = self.JSONResponse({'success': True, 'username': username})
        response.set_cookie(
            key='perfwatch_session',
            value=session_id,
            max_age=900,  # 15 minutes in seconds
            httponly=True,
            samesite='lax'
        )
        return response
    
    def logout(self, request) -> Dict[str, Any]:
        """Handle logout for FastAPI"""
        from perfwatch.dashboard.auth import destroy_session
        
        session_id = request.cookies.get('perfwatch_session')
        if session_id:
            destroy_session(session_id)
        
        # Create response and delete cookie
        response = self.JSONResponse({'success': True})
        response.delete_cookie('perfwatch_session')
        return response
    
    def check_auth(self, request) -> Dict[str, Any]:
        """Check authentication status for FastAPI"""
        from perfwatch.dashboard.auth import verify_session
        
        session_id = request.cookies.get('perfwatch_session')
        username = verify_session(session_id) if session_id else None
        
        return self.JSONResponse({
            'authenticated': username is not None,
            'username': username
        })
    
    def toggle_profiling(self, request) -> Dict[str, Any]:
        """Toggle profiling on/off - requires authentication"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JSONResponse({'error': 'Unauthorized'}, status_code=401)
        
        # Get current status
        current_status = _config_instance.get('profiling.enabled', False)
        
        # Toggle it
        new_status = not current_status
        _config_instance.set('profiling.enabled', new_status)
        
        return self.JSONResponse({
            'success': True,
            'profiling_enabled': new_status,
            'message': f"Profiling {'enabled' if new_status else 'disabled'}"
        })
    
    def get_profiling_status(self, request) -> Dict[str, Any]:
        """Get current profiling status - requires authentication"""
        from perfwatch.dashboard.auth import verify_session
        from perfwatch.config import _config_instance
        
        # Check authentication
        session_id = request.cookies.get('perfwatch_session')
        if not session_id or not verify_session(session_id):
            return self.JSONResponse({'error': 'Unauthorized'}, status_code=401)
        
        status = _config_instance.get('profiling.enabled', False)
        
        return self.JSONResponse({
            'profiling_enabled': status
        })
    
    def _render_login_page(self) -> str:
        """Render login page HTML with embedded Tailwind CSS"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PerfWatch Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
    <div class="bg-gray-800 p-8 rounded-lg shadow-xl w-96">
        <div class="text-center mb-6">
            <i class="fas fa-gauge-high text-4xl text-blue-500 mb-2"></i>
            <h1 class="text-2xl font-bold">PerfWatch</h1>
            <p class="text-gray-400 text-sm">Dashboard Login</p>
        </div>
        <form id="loginForm" class="space-y-4">
            <div>
                <label class="block text-sm font-medium mb-2">Username</label>
                <input type="text" name="username" required 
                       class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-sm font-medium mb-2">Password</label>
                <input type="password" name="password" required 
                       class="w-full px-3 py-2 bg-gray-700 rounded border border-gray-600 focus:border-blue-500 focus:outline-none">
            </div>
            <div id="errorMsg" class="text-red-400 text-sm hidden"></div>
            <button type="submit" 
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded">
                Login
            </button>
        </form>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const errorMsg = document.getElementById('errorMsg');
            
            try {
                const response = await fetch('/perfwatch/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: formData.get('username'),
                        password: formData.get('password')
                    })
                });
                
                if (response.ok) {
                    window.location.reload();
                } else {
                    errorMsg.textContent = 'Invalid username or password';
                    errorMsg.classList.remove('hidden');
                }
            } catch (error) {
                errorMsg.textContent = 'Login failed. Please try again.';
                errorMsg.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
"""