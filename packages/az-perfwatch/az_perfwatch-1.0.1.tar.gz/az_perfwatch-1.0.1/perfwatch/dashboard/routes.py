"""Routes for different web frameworks"""
from typing import Any

def register_fastapi_routes(app: Any, prefix: str = '/perfwatch') -> None:
    """Register FastAPI routes using APIRouter"""
    from fastapi import APIRouter, Request, Query, Body
    from pydantic import BaseModel
    from .views import FastAPIPerfwatchView

    # Pydantic model for login request
    class LoginRequest(BaseModel):
        username: str
        password: str

    view = FastAPIPerfwatchView()
    router = APIRouter(prefix=prefix)
    
    # Wrapper functions to properly inject Request
    async def dashboard_wrapper(request: Request):
        return view.render_dashboard(request)
    
    async def login_wrapper(request: Request, credentials: LoginRequest):
        return view.login(request, credentials.username, credentials.password)
    
    async def logout_wrapper(request: Request):
        return view.logout(request)
    
    async def check_auth_wrapper(request: Request):
        return view.check_auth(request)
    
    async def toggle_profiling_wrapper(request: Request):
        return view.toggle_profiling(request)
    
    async def get_profiling_status_wrapper(request: Request):
        return view.get_profiling_status(request)
    
    async def stats_wrapper(
        request: Request, 
        timeframe: str = Query("24h"),
        severity: str = Query("all"),
        search: str = Query(""),
        page: int = Query(1),
        page_size: int = Query(20),
        start_date: str = Query(""),
        end_date: str = Query("")
    ):
        return view.get_api_stats(request, timeframe, severity, search, page, page_size, start_date, end_date)
    
    async def details_wrapper(request: Request, id: str):
        return view.get_api_details(request, id)
    
    # Register routes on router
    router.add_api_route("/dashboard/", dashboard_wrapper, methods=["GET"], name="dashboard")
    router.add_api_route("/dashboard", dashboard_wrapper, methods=["GET"], name="dashboard_no_slash")
    # Auth routes
    router.add_api_route("/api/login", login_wrapper, methods=["POST"], name="login")
    router.add_api_route("/api/logout", logout_wrapper, methods=["POST"], name="logout")
    router.add_api_route("/api/check-auth", check_auth_wrapper, methods=["GET"], name="check_auth")
    # Profiling toggle routes
    router.add_api_route("/api/toggle-profiling", toggle_profiling_wrapper, methods=["POST"], name="toggle_profiling")
    router.add_api_route("/api/profiling-status", get_profiling_status_wrapper, methods=["GET"], name="profiling_status")
    # API routes (protected) - with and without trailing slash
    router.add_api_route("/api/stats", stats_wrapper, methods=["GET"], name="api_stats")
    router.add_api_route("/api/stats/", stats_wrapper, methods=["GET"], name="api_stats_slash")
    router.add_api_route("/api/details/{id}", details_wrapper, methods=["GET"], name="api_details")
    router.add_api_route("/api/details/{id}/", details_wrapper, methods=["GET"], name="api_details_slash")
    
    # Include router in app
    app.include_router(router)
    
    # Mount static files separately (must be done on app, not router)
    app.mount(f"{prefix}/static", view.static_files, name="perfwatch_static")

def register_flask_routes(app: Any, url_prefix: str = '/perfwatch') -> None:
    """Register Flask routes"""
    from flask import Blueprint
    from .views import FlaskPerfwatchView

    view = FlaskPerfwatchView()
    blueprint = Blueprint('perfwatch', __name__, url_prefix=url_prefix)
    print("Registering Flask PerfWatch routes...")
    # Main dashboard - with and without trailing slash
    blueprint.route('/dashboard', strict_slashes=False)(view.render_dashboard)
    # Auth routes
    blueprint.route('/api/login', methods=['POST'], strict_slashes=False)(view.login)
    blueprint.route('/api/logout', methods=['POST'], strict_slashes=False)(view.logout)
    blueprint.route('/api/check-auth', strict_slashes=False)(view.check_auth)
    # Profiling toggle routes
    blueprint.route('/api/toggle-profiling', methods=['POST'], strict_slashes=False)(view.toggle_profiling)
    blueprint.route('/api/profiling-status', strict_slashes=False)(view.get_profiling_status)
    # API routes (protected)
    blueprint.route('/api/stats', strict_slashes=False)(view.get_api_stats)
    blueprint.route('/api/details/<api_id>', strict_slashes=False)(view.get_api_details)

    app.register_blueprint(blueprint)
    