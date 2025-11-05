import typer
import re
from getpass import getpass
from passlib.context import CryptContext

from perfwatch.core import profiler
from perfwatch.core.critical import CriticalAnalyzer
from perfwatch.db.store import (
    init_db as migrate_db,
    create_user as create_new_user,
    get_user_by_username,
    list_users,
)
from perfwatch.config import _config_instance as config
import importlib.util
from pathlib import Path

def version_callback(value: bool):
    """Callback for --version flag"""
    if value:
        from perfwatch import __version__
        typer.echo(f"PerfWatch version {__version__}")
        raise typer.Exit()

cli = typer.Typer(help="PerfWatch CLI")

@cli.callback()
def main(
    version: bool = typer.Option(
        None, 
        "--version", 
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """
    PerfWatch - Production-ready performance monitoring for Python web applications
    """
    pass

@cli.command()
def version():
    """Show PerfWatch version"""
    from perfwatch import __version__
    typer.echo(f"PerfWatch version {__version__}")

@cli.command()
def migrate():
    """Run database migrations (creates/recreates tables)"""
    from perfwatch.config import _config_instance as config
    
    typer.echo("🔧 Running database migration...")
    
    # Show current database config
    try:
        db_config = config.validate_db_config()
        engine = db_config["engine"]
        
        if engine == "sqlite":
            typer.echo(f"📦 Database: SQLite")
            typer.echo(f"📁 Path: {db_config['path']}")
        else:
            typer.echo(f"📦 Database: {engine.upper()}")
            typer.echo(f"🌐 Host: {db_config['host']}:{db_config['port']}")
            typer.echo(f"💾 Database: {db_config['name']}")
            typer.echo(f"👤 User: {db_config['user']}")
    except ValueError as e:
        typer.secho(str(e), fg="red")
        raise typer.Exit(code=1)
    
    typer.echo("\n⚠️  This will DROP existing tables and recreate them!")
    
    confirm = typer.confirm("Continue?", default=False)
    if not confirm:
        typer.echo("❌ Migration cancelled")
        raise typer.Exit(code=1)
    
    try:
        migrate_db()
        typer.secho("✅ Migration complete - Database tables created", fg="green")
    except ImportError as e:
        typer.secho(f"\n{str(e)}", fg="red")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"❌ Migration failed: {str(e)}", fg="red")
        raise typer.Exit(code=1)

@cli.command()
def create_user(username: str = typer.Option(None, help="Username for the new user")):
    """Create new dashboard user - stores in DATABASE (not config file)"""
    from passlib.context import CryptContext
    from perfwatch.db.store import create_user as db_create_user, get_user_by_username
    
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    # Prompt for username if not provided
    if not username:
        username = typer.prompt("Username")

    username = username.strip()
    if not username:
        typer.secho("Username cannot be empty", fg="red")
        raise typer.Exit(code=2)

    # Validate username
    if not re.match(r"^[A-Za-z0-9._-]{3,150}$", username):
        typer.secho("Username must be 3-150 characters and contain only letters, numbers, ., _, -", fg="red")
        raise typer.Exit(code=2)

    # Check if user already exists in database
    existing = get_user_by_username(username)
    if existing:
        typer.secho(f"User '{username}' already exists in database", fg="red")
        raise typer.Exit(code=3)

    # Optional fields
    email = typer.prompt("Email (optional, press Enter to skip)", default="", show_default=False)
    email = email if email else None
    
    full_name = typer.prompt("Full Name (optional, press Enter to skip)", default="", show_default=False)
    full_name = full_name if full_name else None

    # Prompt for password twice
    for attempt in range(3):
        pwd = getpass("Password: ")
        pwd2 = getpass("Confirm Password: ")
        if pwd != pwd2:
            typer.secho("Passwords do not match. Try again.", fg="red")
            continue
        if len(pwd) < 8:
            typer.secho("Password must be at least 8 characters", fg="red")
            continue
        if pwd.isdigit():
            typer.secho("Password cannot be entirely numeric", fg="red")
            continue
        break
    else:
        typer.secho("Failed to set a valid password after 3 attempts", fg="red")
        raise typer.Exit(code=4)

    # Hash password and create user in database
    password_hash = pwd_context.hash(pwd)
    success = db_create_user(username, password_hash, email, full_name)
    
    if not success:
        typer.secho(f"Failed to create user '{username}'", fg="red")
        raise typer.Exit(code=5)

    typer.secho(f"✅ User '{username}' created successfully in DATABASE", fg="green")
    if email:
        typer.secho(f"   Email: {email}", fg="cyan")
    if full_name:
        typer.secho(f"   Name: {full_name}", fg="cyan")

@cli.command()
def users_list():
    """List all dashboard users from DATABASE"""
    from perfwatch.db.store import list_all_users
    
    users = list_all_users()
    if not users:
        typer.echo("No users found in database")
    else:
        typer.echo(f"\n📊 Users in database ({len(users)}):\n")
        for u in users:
            status = "✓ Active" if u.get('is_active') else "✗ Inactive"
            typer.secho(f"  Username: {u['username']}", fg="cyan", bold=True)
            typer.echo(f"  Status:   {status}")
            if u.get('email'):
                typer.echo(f"  Email:    {u['email']}")
            if u.get('full_name'):
                typer.echo(f"  Name:     {u['full_name']}")
            typer.echo(f"  Created:  {u.get('created_at', 'N/A')}")
            typer.echo("")

# ------------------------
# Config Commands
# ------------------------
@cli.command()
def show_config():
    """Show current applied config"""
    typer.echo(config._config)

@cli.command()
def create_default_config():
    """Generate default config file"""
    config.save()
    typer.echo("Default config created")

@cli.command()
def apply_config():
    """Apply updated config"""
    config.save()
    typer.echo("Config applied")

# ------------------------
# Profiling Commands
# ------------------------
# @cli.command()
# def watch():
#     """Start runtime profiling on demand"""
#     profiler.start()
#     typer.echo("Watching performance...")

# @cli.command()
# def stop_watch():
#     """Stop runtime profiling"""
#     profiler.stop()
#     typer.echo("Stopped watching")

# @cli.command()
# def insights(top_n: int = 5):
#     """Show critical functions/queries report"""
#     # Use default thresholds; CLI could be extended to accept thresholds
#     report = CriticalAnalyzer.get_report()
#     typer.echo(report)

# ------------------------
# Dashboard Commands
# ------------------------
# @cli.command()
# def dashboard():
#     """Run web dashboard (FastAPI/Flask/Django)"""
#     typer.echo("Starting dashboard...")
#     # TODO: Call FastAPI/Flask/Django router integration

# # cli/main.py

@cli.command()
def embed_status():
    """
    Check if PerfWatch profiling is embedded in project.
    Performs:
    1. Profiler import check
    2. Config existence check
    3. DB path check
    """

    messages = []

    # Profiler module check
    profiler_spec = importlib.util.find_spec("perfwatch.core.profiler")
    if profiler_spec is not None:
        messages.append("Profiler module available")
    else:
        messages.append("Profiler module NOT found")

    # Config check
    if Path(config.config_file).exists():
        messages.append(f"Config file found at {config.config_file}")
    else:
        messages.append(f"Config file NOT found, default config will be used")

    # DB path check
    db_path = config.get("db.path")
    if db_path and Path(db_path).exists():
        messages.append(f"DB file exists at {db_path}")
    else:
        messages.append(f"DB file not found at {db_path} (it will be created on migrate)")

    # Check module-level profiler status
    if config.get("profiling.enabled"):
        messages.append("Profiling is currently ACTIVE")
    else:
        messages.append("Profiling is currently INACTIVE")

    # Display all status messages
    for msg in messages:
        typer.echo(msg)


# ------------------------
# User Config Update Command
# ------------------------
@cli.command()
def update_config(key_path: str, value: str):
    """Update a config key"""
    config.set(key_path, value)
    typer.echo(f"Config '{key_path}' updated to '{value}'")


# @cli.command()
# def metrics_list(limit: int = 20):
#     """List recent stored perfwatch metrics"""
#     from perfwatch.db.store import list_metrics

#     rows = list_metrics(limit)
#     if not rows:
#         typer.echo("No metrics found")
#         return

#     # Print a compact summary table
#     for r in rows:
#         data = r.get('data') or {}
#         func = data.get('func_name') or data.get('name') or '<unknown>'
#         duration = data.get('duration_ms') or 0
#         qcount = len(data.get('queries') or [])
#         typer.echo(f"[{r['created_at']}] {r['request_id']} - {func} - {duration:.2f}ms - {qcount} queries")


# @cli.command()
# def metrics_show(request_id: str):
#     """Pretty-print a stored perfwatch profile by request_id"""
#     from perfwatch.db.store import get

#     profile = get(request_id)
#     if not profile:
#         typer.echo(f"No profile found for request_id {request_id}")
#         raise typer.Exit(code=2)

#     def _print_node(node, indent=0):
#         spacer = ' ' * indent
#         name = node.get('func_name', '<unknown>')
#         duration = node.get('duration_ms', 0.0)
#         calls = node.get('call_count', 0)
#         queries = node.get('queries', []) or []
#         typer.echo(f"{spacer}- {name} [{duration:.2f}ms, calls={calls}] (queries={len(queries)})")
#         for q in queries:
#             sql = q.get('sql', 'N/A')
#             t = q.get('time_ms', 0.0)
#             # truncate long SQL
#             sql_short = sql if len(sql) < 200 else sql[:197] + '...'
#             typer.echo(f"{spacer}    Q: {sql_short} ({t:.2f}ms)")
#         for child in node.get('children', []):
#             _print_node(child, indent + 4)

#     typer.echo(f"Profile {request_id}:")
#     _print_node(profile)

# TODO: add create-user, apply-config, dashboard, embed-status
if __name__ == "__main__":
    cli()