import os
import sqlite3
import json
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

# Try importing PostgreSQL and MySQL connectors (optional dependencies)
try:
    import psycopg2
    import psycopg2.extras
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import mysql.connector
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

DB_PATH = os.environ.get("PERFWATCH_DB") or os.path.join(os.getcwd(), "perfwatch.db")

def get_db_connection() -> Tuple[Any, str]:
    """Get database connection based on config
    
    Returns:
        Tuple[connection, engine]: Database connection and engine type
    
    Raises:
        ValueError: If database config is invalid or missing
        ImportError: If required database driver is not installed
    """
    from perfwatch.config import _config_instance as config
    
    try:
        db_config = config.validate_db_config()
    except ValueError as e:
        raise ValueError(f"\n{str(e)}\n\nRun: perfwatch create-default-config") from e
    
    engine = db_config["engine"]
    
    # SQLite connection
    if engine == "sqlite":
        db_path = db_config["path"]
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        conn = sqlite3.connect(db_path)
        return conn, "sqlite"
    
    # PostgreSQL connection
    elif engine == "postgresql":
        if not HAS_POSTGRES:
            raise ImportError(
                "❌ PostgreSQL support not installed!\n"
                "Install with: pip install psycopg2-binary"
            )
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["name"],
            user=db_config["user"],
            password=db_config["password"]
        )
        return conn, "postgresql"
    
    # MySQL connection
    elif engine == "mysql":
        if not HAS_MYSQL:
            raise ImportError(
                "❌ MySQL support not installed!\n"
                "Install with: pip install mysql-connector-python"
            )
        conn = mysql.connector.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["name"],
            user=db_config["user"],
            password=db_config["password"]
        )
        return conn, "mysql"
    
    raise ValueError(f"Unsupported database engine: {engine}")

def init_db():
    """Initialize database with tables
    
    ⚠️ IMPORTANT: This function should ONLY be called via CLI command:
        perfwatch migrate
    
    It will DROP existing tables and recreate them. Never call this
    automatically on import or startup - user must explicitly run migration.
    """
    conn, engine = get_db_connection()
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS metrics")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # SQL syntax varies by database engine
    if engine == "sqlite":
        pk_metrics = "id INTEGER PRIMARY KEY AUTOINCREMENT"
        pk_users = "id INTEGER PRIMARY KEY AUTOINCREMENT"
        placeholder = "?"
    elif engine == "postgresql":
        pk_metrics = "id SERIAL PRIMARY KEY"
        pk_users = "id SERIAL PRIMARY KEY"
        placeholder = "%s"
    elif engine == "mysql":
        pk_metrics = "id INT AUTO_INCREMENT PRIMARY KEY"
        pk_users = "id INT AUTO_INCREMENT PRIMARY KEY"
        placeholder = "%s"
    else:
        raise ValueError(f"Unsupported database engine: {engine}")
    
    # Create metrics table - store function profiling data as JSON
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS metrics (
            {pk_metrics},
            request_id TEXT,
            data TEXT,
            request_payload TEXT,
            response_data TEXT,
            method TEXT,
            endpoint TEXT,
            start_time TEXT,
            end_time TEXT,
            total_time REAL,
            status_code INTEGER,
            environment TEXT,
            host TEXT,
            host_ip TEXT,
            client_ip TEXT,
            user_agent TEXT,
            memory_used {'INTEGER' if engine == 'sqlite' else 'BIGINT'},
            cpu_time REAL,
            created_at TEXT,
            {'UNIQUE(request_id)' if engine == 'sqlite' else 'CONSTRAINT unique_request UNIQUE(request_id)'}
        )
    """)
    
    # Users table for dashboard authentication
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            {pk_users},
            username TEXT {'UNIQUE' if engine == 'sqlite' else ''} NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            is_active {'INTEGER' if engine == 'sqlite' else 'TINYINT'} DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
            {', CONSTRAINT unique_username UNIQUE(username)' if engine != 'sqlite' else ''}
        )
    """)
    
    conn.commit()
    conn.close()

def store_metrics(request_id, data, request_payload=None, response_data=None):
    """Store metrics in the database
    
    Args:
        request_id: Unique identifier for the request
        data: Complete function profiling data
        request_payload: Request data (headers, body, etc.)
        response_data: Response data (status, headers, body)
    """
    conn, engine = get_db_connection()
    cursor = conn.cursor()
    
    # Determine placeholder based on engine
    placeholder = "?" if engine == "sqlite" else "%s"
    
    now = datetime.utcnow().isoformat()
    
    # Extract method and endpoint from the root function name
    func_name = data.get('func_name', '')
    if func_name.startswith('Request:'):
        endpoint = func_name.replace('Request:', '')
    else:
        endpoint = func_name
        
    # If function name starts with route_, parse it
    if func_name.startswith('route_'):
        parts = func_name.split('_', 2)
        if len(parts) > 2:
            method = parts[1].upper()
            endpoint = '/' + parts[2].replace('_', '/')
    else:
        method = request_payload.get('method', 'GET') if request_payload else 'GET'
    
    # Extract timing information
    start_time = data.get('start_time', now)
    end_time = data.get('end_time', now) if data.get('end_time') else now
    total_time = data.get('duration_ms', 0.0)
    
    # Get response status
    status_code = response_data.get('status_code', 200) if response_data else 200
    
    # Get environment info
    try:
        import socket
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
    except:
        hostname = 'unknown'
        host_ip = 'unknown'
    
    # Extract client info
    client_info = request_payload or {}
    client_ip = client_info.get('client_ip', '')
    user_agent = client_info.get('user_agent', '')
    
    # Get environment from common env vars
    environment = (
        os.environ.get('ENV') or 
        os.environ.get('ENVIRONMENT') or 
        os.environ.get('DJANGO_ENV') or 
        os.environ.get('FLASK_ENV') or 
        'development'
    )
    
    # Calculate resource usage
    memory_used = data.get('memory_peak_bytes', 0)
    cpu_time = data.get('cpu_time', 0.0)
    
    query = f"""INSERT INTO metrics (
        request_id, data, request_payload, response_data,
        method, endpoint, start_time, end_time, total_time,
        status_code, environment, host, host_ip, client_ip,
        user_agent, memory_used, cpu_time, created_at
    ) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 
              {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
              {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
              {placeholder}, {placeholder}, {placeholder}, {placeholder}, 
              {placeholder}, {placeholder})"""
    
    cursor.execute(query, (
        request_id,
        json.dumps(data),
        json.dumps(request_payload) if request_payload else '{}',
        json.dumps(response_data) if response_data else '{}',
        method,
        endpoint,
        start_time,
        end_time,
        total_time,
        status_code,
        environment,
        hostname,
        host_ip,
        client_ip,
        user_agent,
        memory_used,
        cpu_time,
        now
    ))
    conn.commit()
    conn.close()

def get_metrics(filter_params=None, last_n=100):
    """Get stored metrics data with advanced filtering and sorting
    
    Args:
        filter_params: Dictionary of filters to apply
            - start_time: ISO datetime string
            - end_time: ISO datetime string
            - min_time: Minimum response time in ms
            - max_time: Maximum response time in ms
            - endpoint: Exact endpoint match
            - endpoint_pattern: LIKE pattern for endpoint
            - method: HTTP method
            - status_code: HTTP status code
            - severity: normal/warning/critical
            - environment: dev/staging/prod
            - host: Server hostname
            - sort_by: Field to sort by (created_at, total_time, etc)
            - sort_order: ASC or DESC
        last_n: Limit number of results (None for no limit)
    """
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    base_query = "SELECT * FROM metrics"
    where_clauses = []
    params = []
    
    if filter_params:
        # Handle time range filters
        if 'start_time' in filter_params:
            where_clauses.append("created_at >= ?")
            params.append(filter_params['start_time'])
        if 'end_time' in filter_params:
            where_clauses.append("created_at <= ?")
            params.append(filter_params['end_time'])
            
        # Handle min/max response time filters    
        if 'min_time' in filter_params:
            where_clauses.append("total_time >= ?")
            params.append(filter_params['min_time'])
        if 'max_time' in filter_params:
            where_clauses.append("total_time <= ?")
            params.append(filter_params['max_time'])
            
        # Handle other exact match filters    
        for key in ['endpoint', 'method', 'status_code', 'severity', 'environment', 'host']:
            if key in filter_params:
                where_clauses.append(f"{key} = ?")
                params.append(filter_params[key])
                
        # Handle pattern matching for endpoints
        if 'endpoint_pattern' in filter_params:
            where_clauses.append("endpoint LIKE ?")
            params.append(f"%{filter_params['endpoint_pattern']}%")
    
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    
    # Add sorting
    sort_field = filter_params.get('sort_by', 'created_at') if filter_params else 'created_at'
    sort_order = filter_params.get('sort_order', 'DESC') if filter_params else 'DESC'
    if sort_field in ['created_at', 'total_time', 'memory_used', 'cpu_time']:
        base_query += f" ORDER BY {sort_field} {sort_order}"
    else:
        base_query += " ORDER BY created_at DESC"
        
    if last_n:
        base_query += " LIMIT ?"
        params.append(last_n)
    
    cursor.execute(base_query, params)
    metrics = []
    
    for row in cursor.fetchall():
        metric_dict = {}
        for idx, col in enumerate(cursor.description):
            value = row[idx]
            # Parse JSON fields
            if col[0] in ['request_data', 'response_data', 'data']:
                try:
                    value = json.loads(value) if value else {}
                except:
                    value = {}
            metric_dict[col[0]] = value
        metrics.append(metric_dict)
    
    conn.close()
    return metrics

def list_metrics(limit=50):
    """Return the most recent metrics (as parsed JSON) up to limit entries"""
    return get_metrics(last_n=limit)

def get(request_id):
    """Get metrics by request_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data, request_payload, response_data, method, endpoint, created_at 
        FROM metrics 
        WHERE request_id=?
    """, (request_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    try:
        # Parse the stored JSON data
        profile_data = json.loads(row[0])
        request_data = json.loads(row[1]) if row[1] else {}
        response_data = json.loads(row[2]) if row[2] else {}
        
        # Combine everything into one response
        return {
            'request_id': request_id,
            'method': row[3],
            'endpoint': row[4],
            'created_at': row[5],
            'request': request_data,
            'response': response_data,
            **profile_data  # Include all the profiling data (functions, queries, etc.)
        }
    except json.JSONDecodeError:
        # Fallback to raw data if JSON parsing fails
        return {
            'request_id': request_id,
            'data': row[0],
            'request': row[1],
            'response': row[2],
            'method': row[3],
            'endpoint': row[4],
            'created_at': row[5]
        }

def list_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, created_at FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "created_at": r[2]} for r in rows]


def get_user_by_username(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, created_at FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "username": row[1], "password": row[2], "created_at": row[3]}


def create_user(username: str, password_hash: str) -> bool:
    """Create a user with a password hash. Returns True on success, False if username exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def list_metrics(limit: int = 50):
    """Return the most recent metrics (as parsed JSON) up to `limit` entries."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT request_id, data, created_at FROM metrics ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        request_id, data, created_at = row
        try:
            parsed_data = json.loads(data)
            parsed_data['request_id'] = request_id
            parsed_data['created_at'] = created_at
            result.append(parsed_data)
        except json.JSONDecodeError:
            continue
    return result

def get_performance_stats(hours=24, environment=None):
    """Get detailed performance statistics for the last N hours
    
    Args:
        hours: Number of hours to look back
        environment: Filter by environment (dev/staging/prod)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate time range
    time_ago = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    # Build WHERE clause
    where_clause = "WHERE created_at > ?"
    params = [time_ago]
    
    if environment:
        where_clause += " AND environment = ?"
        params.append(environment)
    
    # Get overall stats
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total_requests,
            AVG(total_time) as avg_response_time,
            MAX(total_time) as max_response_time,
            MIN(total_time) as min_response_time,
            AVG(memory_used) as avg_memory_used,
            MAX(memory_used) as peak_memory_used,
            AVG(cpu_time) as avg_cpu_time,
            COUNT(CASE WHEN status_code >= 500 THEN 1 END) as error_count,
            COUNT(CASE WHEN total_time > 1000 THEN 1 END) as slow_count,
            COUNT(DISTINCT host) as unique_hosts,
            COUNT(DISTINCT client_ip) as unique_clients
        FROM metrics
        {where_clause}
    """, params)
    
    stats_row = cursor.fetchone()
    
    # Get top 10 slowest endpoints
    cursor.execute(f"""
        SELECT 
            endpoint,
            method,
            COUNT(*) as call_count,
            AVG(total_time) as avg_time,
            MAX(total_time) as max_time,
            MIN(total_time) as min_time,
            AVG(memory_used) as avg_memory,
            AVG(cpu_time) as avg_cpu
        FROM metrics
        {where_clause}
        GROUP BY endpoint, method
        ORDER BY avg_time DESC
        LIMIT 10
    """, params)
    
    slow_endpoints = [{
        'endpoint': row[0],
        'method': row[1],
        'call_count': row[2],
        'avg_time': row[3],
        'max_time': row[4],
        'min_time': row[5],
        'avg_memory': row[6],
        'avg_cpu': row[7]
    } for row in cursor.fetchall()]
    
    # Get status code distribution
    cursor.execute(f"""
        SELECT 
            status_code,
            COUNT(*) as count,
            AVG(total_time) as avg_time
        FROM metrics
        {where_clause}
        GROUP BY status_code
        ORDER BY count DESC
    """, params)
    
    status_codes = [{
        'status_code': row[0],
        'count': row[1],
        'avg_time': row[2]
    } for row in cursor.fetchall()]
    
    # Get hourly request counts
    cursor.execute(f"""
        SELECT 
            strftime('%Y-%m-%d %H:00:00', created_at) as hour,
            COUNT(*) as request_count,
            AVG(total_time) as avg_time,
            COUNT(CASE WHEN status_code >= 500 THEN 1 END) as error_count
        FROM metrics
        {where_clause}
        GROUP BY hour
        ORDER BY hour DESC
    """, params)
    
    hourly_stats = [{
        'hour': row[0],
        'request_count': row[1],
        'avg_time': row[2],
        'error_count': row[3]
    } for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'summary': {
            'total_requests': stats_row[0],
            'avg_response_time': stats_row[1],
            'max_response_time': stats_row[2],
            'min_response_time': stats_row[3],
            'avg_memory_used': stats_row[4],
            'peak_memory_used': stats_row[5],
            'avg_cpu_time': stats_row[6],
            'error_count': stats_row[7],
            'slow_request_count': stats_row[8],
            'unique_hosts': stats_row[9],
            'unique_clients': stats_row[10]
        },
        'slow_endpoints': slow_endpoints,
        'status_codes': status_codes,
        'hourly_stats': hourly_stats
    }

def _calculate_severity(total_time: float, query_count: int = 0) -> str:
    """Calculate severity based on response time and query count"""
    if total_time > 1000 or query_count > 10:  # More than 1s or 10 queries
        return 'critical'
    elif total_time > 500 or query_count > 5:  # More than 500ms or 5 queries
        return 'warning'
    return 'normal'

def get(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metrics for a specific request_id.
    This is the legacy function kept for backward compatibility.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the basic request info
    cursor.execute("""
        SELECT metrics.*, profiles.function_data
        FROM metrics 
        LEFT JOIN (
            SELECT request_id, 
                   json_group_array(
                       json_object(
                           'function_name', function_name,
                           'total_time', total_time,
                           'start_time', start_time,
                           'end_time', end_time,
                           'memory_used', memory_used,
                           'cpu_time', cpu_time,
                           'error', error,
                           'queries', (
                               SELECT json_group_array(
                                   json_object(
                                       'sql', query,
                                       'params', params,
                                       'total_time', total_time,
                                       'rows_affected', rows_affected
                                   )
                               )
                               FROM queries 
                               WHERE queries.profile_id = profiles.id
                           )
                       )
                   ) as function_data
            FROM profiles
            GROUP BY request_id
        ) profiles ON metrics.request_id = profiles.request_id
        WHERE metrics.request_id = ?
    """, (request_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    # Convert to legacy format for backward compatibility
    _, request_id, method, endpoint, status_code, total_time, start_time, end_time, \
    environment, host, client_ip, user_agent, created_at, function_data = row
    
    try:
        functions = json.loads(function_data) if function_data else []
    except json.JSONDecodeError:
        functions = []
    
    return {
        'request_id': request_id,
        'method': method,
        'endpoint': endpoint,
        'total_time': total_time,
        'start_time': start_time,
        'end_time': end_time,
        'functions': functions,
        'environment': environment,
        'created_at': created_at
    }


# ==========================================
# USER MANAGEMENT FUNCTIONS FOR DATABASE
# ==========================================

def create_user(username: str, password_hash: str, email: Optional[str] = None, full_name: Optional[str] = None) -> bool:
    """Create user in database"""
    try:
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        
        placeholder = "?" if engine == "sqlite" else "%s"
        query = f"""
            INSERT INTO users (username, password_hash, email, full_name, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """
        cursor.execute(query, (username, password_hash, email, full_name, created_at))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user from database"""
    try:
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = "?" if engine == "sqlite" else "%s"
        query = f"""
            SELECT id, username, password_hash, email, full_name, is_active, created_at
            FROM users WHERE username = {placeholder}
        """
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'email': row[3],
                'full_name': row[4],
                'is_active': bool(row[5]),
                'created_at': row[6]
            }
        return None
    except Exception:
        return None


def list_all_users() -> List[Dict[str, Any]]:
    """List all users from database"""
    try:
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, full_name, is_active, created_at
            FROM users ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'is_active': bool(row[4]),
                'created_at': row[5]
            }
            for row in rows
        ]
    except Exception:
        return []


def delete_user(username: str) -> bool:
    """Delete user from database"""
    try:
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        
        placeholder = "?" if engine == "sqlite" else "%s"
        query = f"DELETE FROM users WHERE username = {placeholder}"
        cursor.execute(query, (username,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    except Exception:
        return False
