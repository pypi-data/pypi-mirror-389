"""Django URLs for PerfWatch Dashboard"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import DjangoPerfwatchView

view = DjangoPerfwatchView()

urlpatterns = [
    # Main dashboard
    path('dashboard/', view.render_dashboard, name='perfwatch-dashboard'),
    # Auth routes (CSRF exempt for API)
    path('api/login', csrf_exempt(view.login), name='perfwatch-login'),
    path('api/logout', csrf_exempt(view.logout), name='perfwatch-logout'),
    path('api/check-auth', view.check_auth, name='perfwatch-check-auth'),
    # Profiling toggle routes
    path('api/toggle-profiling', csrf_exempt(view.toggle_profiling), name='perfwatch-toggle-profiling'),
    path('api/profiling-status', view.get_profiling_status, name='perfwatch-profiling-status'),
    # API routes (protected)
    path('api/stats/', view.get_api_stats, name='perfwatch-api-stats'),
    path('api/details/<str:api_id>/', view.get_api_details, name='perfwatch-api-details'),
    # Static files
    path('static/<path:path>', view.serve_static_file, name='perfwatch-static'),
]
