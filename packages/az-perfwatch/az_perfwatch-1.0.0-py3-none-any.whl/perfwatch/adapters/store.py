import os
import sqlite3
import json
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

DB_PATH = os.environ.get("PERFWATCH_DB") or os.path.join(os.getcwd(), "perfwatch.db")

def init_db():
    """Initialize database with tables
    
    ⚠️ IMPORTANT: This function should ONLY be called via CLI command:
        perfwatch migrate
    
    It will DROP existing tables and recreate them. Never call this
    automatically on import or startup - user must explicitly run migration.
    """
    # First, ensure db directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS metrics")
    cursor.execute("DROP TABLE IF EXISTS function_metrics")
    cursor.execute("DROP TABLE IF EXISTS query_metrics")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # 1. API Level - Complete request metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            data TEXT,           -- Complete function profiling data as JSON
            request_payload TEXT, -- Request payload data (headers, body, etc.)
            response_data TEXT,   -- Response data (status, headers, body)
            method TEXT,         -- HTTP method
            endpoint TEXT,       -- Request endpoint
            start_time TEXT,     -- When request started
            end_time TEXT,       -- When request completed
            total_time REAL,     -- Total execution time in ms
            status_code INTEGER, -- HTTP status code
            environment TEXT,    -- dev/staging/prod
            host TEXT,          -- Server hostname
            host_ip TEXT,       -- Server IP
            client_ip TEXT,     -- Client IP
            user_agent TEXT,    -- Browser/client info
            memory_used INTEGER, -- Peak memory usage in bytes
            cpu_time REAL,      -- Total CPU time used
            
            -- API-level resource metrics
            memory_before_mb REAL,
            memory_after_mb REAL,
            memory_delta_mb REAL,
            memory_bytes INTEGER,
            memory_peak_bytes INTEGER,
            objects_created INTEGER,
            objects_destroyed INTEGER,
            object_count_delta INTEGER,
            gc_gen0_collections INTEGER,
            gc_gen1_collections INTEGER,
            gc_gen2_collections INTEGER,
            cpu_percent REAL,
            cpu_time_user REAL,
            cpu_time_system REAL,
            thread_count INTEGER,
            io_read_bytes INTEGER,
            io_write_bytes INTEGER,
            
            created_at TEXT,
            UNIQUE(request_id)
        )
    """)
    
    # 2. Function Level - Individual function metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS function_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,     -- Link to parent API request
            function_name TEXT,
            parent_function TEXT, -- Parent function name
            function_path TEXT,  -- Full path: parent1 > parent2 > this
            duration_ms REAL,
            call_count INTEGER,
            
            -- Memory metrics
            memory_before_mb REAL,
            memory_after_mb REAL,
            memory_delta_mb REAL,
            memory_bytes INTEGER,
            memory_peak_bytes INTEGER,
            
            -- GC & Objects
            objects_created INTEGER,
            objects_destroyed INTEGER,
            object_count_delta INTEGER,
            gc_gen0_collections INTEGER,
            gc_gen1_collections INTEGER,
            gc_gen2_collections INTEGER,
            gc_enabled INTEGER,
            gc_objects_before INTEGER,
            gc_objects_after INTEGER,
            
            -- CPU & I/O
            cpu_percent REAL,
            cpu_time_user REAL,
            cpu_time_system REAL,
            thread_count INTEGER,
            io_read_bytes INTEGER,
            io_write_bytes INTEGER,
            
            -- Source location
            file_path TEXT,
            line_number INTEGER,
            error TEXT,
            
            created_at TEXT,
            FOREIGN KEY (request_id) REFERENCES metrics(request_id)
        )
    """)
    
    # 3. Query Level - Individual database queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,     -- Link to parent API request
            function_name TEXT,  -- Which function executed this query
            query_type TEXT,     -- SELECT, INSERT, UPDATE, DELETE, etc.
            sql TEXT,            -- The actual SQL query
            duration_ms REAL,
            params TEXT,         -- JSON array of parameters
            rows_affected INTEGER,
            database_type TEXT,  -- sqlite, postgres, mysql, mongodb
            
            created_at TEXT,
            FOREIGN KEY (request_id) REFERENCES metrics(request_id)
        )
    """)
    
    # Users table for authentication (if needed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_endpoint ON metrics(endpoint)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON metrics(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_total_time ON metrics(total_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_code ON metrics(status_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_endpoint_created ON metrics(endpoint, created_at)")
    
    # Function metrics indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_request ON function_metrics(request_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_name ON function_metrics(function_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_func_duration ON function_metrics(duration_ms)")
    
    # Query metrics indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_request ON query_metrics(request_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_func ON query_metrics(function_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_duration ON query_metrics(duration_ms)")
    
    conn.commit()
    conn.close()

def store_metrics(request_id, data, request_payload=None, response_data=None):
    """Store metrics in the database
    
    Args:
        request_id: Unique identifier for the request
        data: Complete function profiling data
        request_payload: Request details (headers, body, etc.)
        response_data: Response details (status, headers, body)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    # Extract API-level metrics
    gc_collected = data.get('gc_collected', {})
    
    # 1. Store API-level metrics
    cursor.execute(
        """INSERT INTO metrics (
            request_id, data, request_payload, response_data,
            method, endpoint, start_time, end_time, total_time,
            status_code, environment, host, host_ip, client_ip,
            user_agent, memory_used, cpu_time,
            memory_before_mb, memory_after_mb, memory_delta_mb,
            memory_bytes, memory_peak_bytes,
            objects_created, objects_destroyed, object_count_delta,
            gc_gen0_collections, gc_gen1_collections, gc_gen2_collections,
            cpu_percent, cpu_time_user, cpu_time_system,
            thread_count, io_read_bytes, io_write_bytes,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
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
            data.get('memory_before_mb', 0),
            data.get('memory_after_mb', 0),
            data.get('memory_delta_mb', 0),
            data.get('memory_bytes', 0),
            data.get('memory_peak_bytes', 0),
            data.get('objects_created', 0),
            data.get('objects_destroyed', 0),
            data.get('object_count_delta', 0),
            gc_collected.get('gen0', 0),
            gc_collected.get('gen1', 0),
            gc_collected.get('gen2', 0),
            data.get('cpu_percent', 0),
            data.get('cpu_time_user', 0),
            data.get('cpu_time_system', 0),
            data.get('thread_count', 0),
            data.get('io_read_bytes', 0),
            data.get('io_write_bytes', 0),
            now
        )
    )
    
    # 2. Store function-level metrics (recursively traverse tree)
    def store_function_metrics(node, parent_name='', path=''):
        if not node:
            return
        
        func_name = node.get('func_name', 'unknown')
        current_path = f"{path} > {func_name}" if path else func_name
        gc_collected = node.get('gc_collected', {})
        gc_stats_before = node.get('gc_stats_before', {})
        gc_stats_after = node.get('gc_stats_after', {})
        
        cursor.execute("""
            INSERT INTO function_metrics (
                request_id, function_name, parent_function, function_path,
                duration_ms, call_count,
                memory_before_mb, memory_after_mb, memory_delta_mb,
                memory_bytes, memory_peak_bytes,
                objects_created, objects_destroyed, object_count_delta,
                gc_gen0_collections, gc_gen1_collections, gc_gen2_collections,
                gc_enabled, gc_objects_before, gc_objects_after,
                cpu_percent, cpu_time_user, cpu_time_system,
                thread_count, io_read_bytes, io_write_bytes,
                file_path, line_number, error,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_id,
            func_name,
            parent_name,
            current_path,
            node.get('duration_ms', 0),
            node.get('call_count', 1),
            node.get('memory_before_mb', 0),
            node.get('memory_after_mb', 0),
            node.get('memory_delta_mb', 0),
            node.get('memory_bytes', 0),
            node.get('memory_peak_bytes', 0),
            node.get('objects_created', 0),
            node.get('objects_destroyed', 0),
            node.get('object_count_delta', 0),
            gc_collected.get('gen0', 0),
            gc_collected.get('gen1', 0),
            gc_collected.get('gen2', 0),
            1 if node.get('gc_enabled', True) else 0,
            gc_stats_before.get('objects', 0),
            gc_stats_after.get('objects', 0),
            node.get('cpu_percent', 0),
            node.get('cpu_time_user', 0),
            node.get('cpu_time_system', 0),
            node.get('thread_count', 0),
            node.get('io_read_bytes', 0),
            node.get('io_write_bytes', 0),
            node.get('file_path'),
            node.get('line_number'),
            node.get('error'),
            now
        ))
        
        # Store queries for this function
        queries = node.get('queries', [])
        for query in queries:
            sql = query.get('sql', '')
            query_type = sql.split()[0].upper() if sql else 'UNKNOWN'
            
            cursor.execute("""
                INSERT INTO query_metrics (
                    request_id, function_name, query_type, sql,
                    duration_ms, params, rows_affected, database_type,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                func_name,
                query_type,
                sql,
                query.get('time_ms', 0),
                json.dumps(query.get('params', [])),
                query.get('rows_affected', 0),
                query.get('database_type', 'unknown'),
                now
            ))
        
        # Recursively store children
        for child in node.get('children', []):
            store_function_metrics(child, func_name, current_path)
    
    # Store all functions starting from root
    store_function_metrics(data)
    
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
