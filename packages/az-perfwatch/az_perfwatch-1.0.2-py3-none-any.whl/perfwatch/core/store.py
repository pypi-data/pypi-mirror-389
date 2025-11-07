"""Core store functionality for perfwatch"""
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta
import sqlite3
import os

class PerfwatchStore:
    """SQLite-based store for perfwatch metrics"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize the database connection"""
        # Store will use perfwatch.db.store functions which handle multi-database
        # No need to store db_path here anymore
        pass

    def _init_db(self):
        """Deprecated - use perfwatch.db.store.init_db() via CLI instead"""
        pass

    def store_metrics(self, request_id: str, data: Dict[str, Any], request_payload: Dict[str, Any] = None, response_data: Dict[str, Any] = None) -> None:
        """Store API metrics in the database
        
        Args:
            request_id: Unique identifier for the request
            data: Complete function profiling data
            request_payload: Request data (headers, body, etc.)
            response_data: Response data (status, headers, body)
        """
        with sqlite3.connect(self.db_path) as conn:
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
            
            cursor.execute(
                """INSERT INTO metrics (
                    request_id, data, request_payload, response_data,
                    method, endpoint, start_time, end_time, total_time,
                    status_code, environment, host, host_ip, client_ip,
                    user_agent, memory_used, cpu_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    now
                )
            )
            conn.commit()

    def get_api_stats(self, hours=24, environment=None, search=None, start_time=None, end_time=None) -> Dict[str, Any]:
        """Get API statistics for the dashboard
        
        Args:
            hours: Number of hours to look back (used if start_time/end_time not provided)
            environment: Filter by environment (dev/staging/prod)
            search: Search term to filter endpoints
            start_time: Optional start timestamp (epoch seconds)
            end_time: Optional end timestamp (epoch seconds)
        """
        from perfwatch.db.store import get_db_connection
        
        print(f"Getting API stats with hours={hours}, environment={environment}, search={search}, start_time={start_time}, end_time={end_time}")
        
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        
        # Determine placeholder based on engine
        placeholder = "?" if engine == "sqlite" else "%s"
        
        # Calculate time range
        if start_time and end_time:
            # Use custom timestamp range
            start_date = datetime.fromtimestamp(start_time).isoformat()
            end_date = datetime.fromtimestamp(end_time).isoformat()
            where_clause = f"WHERE created_at >= {placeholder} AND created_at <= {placeholder}"
            params = [start_date, end_date]
            print(f"📅 Using custom date range: {start_date} to {end_date}")
        else:
            # Use hours-based range
            time_ago = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            where_clause = f"WHERE created_at > {placeholder}"
            params = [time_ago]
        
        if environment:
            where_clause += f" AND environment = {placeholder}"
            params.append(environment)
        
        if search:
            where_clause += f" AND endpoint LIKE {placeholder}"
            params.append(f"%{search}%")
        
        print(f"🔍 SQL WHERE clause: {where_clause}")
        print(f"📋 SQL params: {params}")
        
        try:
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
                    COUNT(CASE WHEN total_time > 1000 THEN 1 END) as slow_count
                FROM metrics
                {where_clause}
            """, params)
            
            stats_row = cursor.fetchone()
            
            # Get ALL APIs (not just top 10) - pagination will be handled at view level
            cursor.execute(f"""
                SELECT 
                    request_id,
                    endpoint,
                    method,
                    total_time,
                    memory_used,
                    cpu_time,
                    status_code,
                    client_ip,
                    user_agent,
                    data,
                    created_at
                FROM metrics
                {where_clause}
                ORDER BY total_time DESC
            """, params)
            
            heaviest_apis = []
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[9]) if row[9] else {}
                    
                    # Count queries recursively from execution tree
                    def count_queries_recursive(function_data):
                        if not function_data:
                            return 0
                        query_count = len(function_data.get('queries', []))
                        for child in function_data.get('children', []):
                            query_count += count_queries_recursive(child)
                        return query_count
                    
                    query_count = count_queries_recursive(data)
                    
                    heaviest_apis.append({
                        'id': row[0],
                        'endpoint': row[1] or '',
                        'method': row[2] or 'GET',
                        'total_time': float(row[3]) if row[3] is not None else 0.0,
                        'memory_used': int(row[4]) if row[4] is not None else 0,
                        'cpu_time': float(row[5]) if row[5] is not None else 0.0,
                        'status_code': row[6] or 200,
                        'client_ip': row[7] or '',
                        'user_agent': row[8] or '',
                        'query_count': query_count,
                        'severity': self._calculate_severity(float(row[3]), query_count),
                        'last_called': row[10]  # created_at timestamp
                    })
                except (json.JSONDecodeError, AttributeError, TypeError):
                    continue
            
            # Calculate severity counts
            counts = {
                'critical': len([a for a in heaviest_apis if a['severity'] == 'critical']),
                'warning': len([a for a in heaviest_apis if a['severity'] == 'warning']),
                'normal': len([a for a in heaviest_apis if a['severity'] == 'normal']),
                'total': stats_row[0] if stats_row else 0
            }
            
            conn.close()

            return {
                'counts': counts,
                'heaviest_apis': heaviest_apis,
                'summary': {
                    'total_requests': stats_row[0] if stats_row else 0,
                    'avg_response_time': stats_row[1] if stats_row else 0,
                    'max_response_time': stats_row[2] if stats_row else 0,
                    'min_response_time': stats_row[3] if stats_row else 0,
                    'avg_memory_used': stats_row[4] if stats_row else 0,
                    'peak_memory_used': stats_row[5] if stats_row else 0,
                    'avg_cpu_time': stats_row[6] if stats_row else 0,
                    'error_count': stats_row[7] if stats_row else 0,
                    'slow_request_count': stats_row[8] if stats_row else 0
                }
            }
        except Exception as e:
            # If there's any database error, return empty metrics
            print(f"❌ Error getting API stats: {e}")
            if 'conn' in locals():
                conn.close()
            return {
                'counts': {
                    'critical': 0,
                    'warning': 0,
                    'normal': 0,
                    'total': 0
                },
                'heaviest_apis': [],
                'summary': {
                    'total_requests': 0,
                    'avg_response_time': 0,
                    'max_response_time': 0,
                    'min_response_time': 0,
                    'avg_memory_used': 0,
                    'peak_memory_used': 0,
                    'avg_cpu_time': 0,
                    'error_count': 0,
                    'slow_request_count': 0
                }
            }

    def get_api_details(self, api_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific API call"""
        from perfwatch.db.store import get_db_connection
        
        conn, engine = get_db_connection()
        cursor = conn.cursor()
        placeholder = "?" if engine == "sqlite" else "%s"
        
        cursor.execute(f"""
            SELECT endpoint, method, total_time, data, request_payload, response_data, created_at, status_code
            FROM metrics 
            WHERE request_id = {placeholder}
        """, (api_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'error': 'API details not found'}

        endpoint, method, total_time, data, request_payload, response_data, created_at, status_code = row
        
        # Parse the profiling data
        func_data = json.loads(data) if data else {}
        
        # Count queries from all functions in the call tree
        def count_queries_recursive(function_data):
            query_count = len(function_data.get('queries', []))
            for child in function_data.get('children', []):
                query_count += count_queries_recursive(child)
            return query_count

        # Build hierarchical function tree
        def build_function_tree(root_func):
            if not root_func:
                return None

            # Create current node
            node = {
                'name': root_func.get('func_name', 'Unknown'),
                'duration': root_func.get('duration_ms', 0),
                'start_time': root_func.get('start_time'),
                'end_time': root_func.get('end_time'),
                'queries': [
                    {
                        'sql': q.get('sql', ''),
                        'params': q.get('params', []),
                        'duration': q.get('duration_ms', 0) or q.get('time_ms', 0),
                        'rows_affected': q.get('rows_affected', 0),
                        'function_name': q.get('function_name', root_func.get('func_name', 'Unknown'))
                    }
                    for q in root_func.get('queries', [])
                ],
                'source': root_func.get('source'),
                'error': root_func.get('error'),
                'children': []
            }

            # Add children recursively
            for child in root_func.get('children', []):
                child_node = build_function_tree(child)
                if child_node:
                    node['children'].append(child_node)

            return node
        
        query_count = count_queries_recursive(func_data)
        execution_tree = build_function_tree(func_data)
        
        # Analyze slow reasons
        slow_reasons = self._analyze_slow_reasons(func_data, total_time, query_count)

        # Parse response data
        response_dict = json.loads(response_data) if response_data else {}
        if not isinstance(response_dict, dict):
            response_dict = {}

        return {
            'endpoint': endpoint,
            'method': method or 'GET',
            'total_time': total_time,
            'request': json.loads(request_payload) if request_payload else {},
            'response': response_dict,
            'status': status_code,
            'execution_tree': execution_tree,
            'severity': self._calculate_severity(total_time, query_count),
            'created_at': created_at,
            'start_time': func_data.get('start_time'),
            'slow_reasons': slow_reasons,  # NEW: Detailed analysis of why it's slow
            # Keep the flat functions list for backward compatibility
            'functions': [
                {
                    'name': node['name'],
                    'duration': node['duration'],
                    'start_time': node['start_time'],
                    'end_time': node['end_time'],
                    'queries': node['queries'],
                    'source': node['source'],
                    'error': node['error']
                }
                for node in _flatten_tree(execution_tree) if node
            ],
            # Add memory and performance metrics for Memory Metrics button
            'memory_delta_mb': func_data.get('memory_delta_mb', 0),
            'memory_before_mb': func_data.get('memory_before_mb', 0),
            'memory_after_mb': func_data.get('memory_after_mb', 0),
            'gc_enabled': func_data.get('gc_enabled', False),
            'gc_collected': func_data.get('gc_collected', {}),
            'objects_created': func_data.get('objects_created', 0),
            'objects_destroyed': func_data.get('objects_destroyed', 0),
            'cpu_percent': func_data.get('cpu_percent', 0),
            'cpu_time_user': func_data.get('cpu_time_user', 0),
            'cpu_time_system': func_data.get('cpu_time_system', 0),
            'io_read_bytes': func_data.get('io_read_bytes', 0),
            'io_write_bytes': func_data.get('io_write_bytes', 0)
        }

    def _calculate_severity(self, total_time: float, query_count: int) -> str:
        """Calculate severity based on response time and query count from perfwatch.conf thresholds"""
        from perfwatch.config import _config_instance
        
        # Get thresholds from config (in milliseconds)
        function_threshold = _config_instance.get('thresholds.function_ms', 100)
        query_threshold = _config_instance.get('thresholds.query_ms', 50)
        
        # Critical: more than 10x threshold or too many queries
        if total_time > (function_threshold * 10) or query_count > 10:
            return 'critical'
        # Warning: more than 5x threshold or several queries
        elif total_time > (function_threshold * 5) or query_count > 5:
            return 'warning'
        return 'normal'
    
    def _analyze_slow_reasons(self, func_data: Dict[str, Any], total_time: float, query_count: int) -> List[Dict[str, Any]]:
        """Analyze why an API is slow and return detailed reasons"""
        from perfwatch.config import _config_instance
        
        reasons = []
        
        # Get thresholds
        function_threshold = _config_instance.get('thresholds.function_ms', 100)
        query_threshold = _config_instance.get('thresholds.query_ms', 50)
        
        # Recursively analyze all functions and queries
        def analyze_node(node, path=""):
            node_name = node.get('func_name', 'Unknown')
            node_duration = node.get('duration_ms', 0)
            node_queries = node.get('queries', [])
            node_memory = node.get('memory_bytes', 0)
            node_memory_peak = node.get('memory_peak_bytes', 0)
            node_cpu_time = node.get('cpu_time', 0)
            node_file = node.get('file_path', '')
            node_line = node.get('line_number', '')
            
            # Check if this function itself is slow
            if node_duration > function_threshold * 5:
                reason = {
                    'type': 'slow_function',
                    'severity': 'critical' if node_duration > function_threshold * 10 else 'warning',
                    'function': node_name,
                    'duration': round(node_duration, 2),
                    'threshold': function_threshold,
                    'message': f'Function "{node_name}" took {round(node_duration, 2)}ms (threshold: {function_threshold}ms)',
                    'impact_percent': round((node_duration / total_time) * 100, 1) if total_time > 0 else 0,
                    'suggestions': []
                }
                
                # Add memory info if significant
                if node_memory > 1024 * 1024:  # > 1MB
                    reason['memory_used'] = round(node_memory / (1024 * 1024), 2)  # MB
                if node_memory_peak > 1024 * 1024:  # > 1MB
                    reason['memory_peak'] = round(node_memory_peak / (1024 * 1024), 2)  # MB
                
                # Add CPU time if available
                if node_cpu_time > 0:
                    reason['cpu_time'] = round(node_cpu_time, 2)
                
                # Add source location
                if node_file and node_line:
                    reason['source_location'] = f'{node_file}:{node_line}'
                
                # Generate smart suggestions based on analysis
                if node_memory_peak > 50 * 1024 * 1024:
                    reason['suggestions'].append('🔴 Critical: Very high memory usage - process data in chunks or use generators')
                elif node_memory_peak > 10 * 1024 * 1024:
                    reason['suggestions'].append('⚠️ High memory usage - consider chunking or pagination')
                
                if node_duration > function_threshold * 20:
                    reason['suggestions'].append('🔴 Extremely slow - consider async processing or caching')
                elif node_duration > function_threshold * 10:
                    reason['suggestions'].append('⚠️ Very slow - optimize algorithm or add caching')
                
                if len(node_queries) > 10:
                    reason['suggestions'].append(f'🔴 {len(node_queries)} queries executed - use select_related/prefetch_related or caching')
                elif len(node_queries) > 5:
                    reason['suggestions'].append(f'⚠️ {len(node_queries)} queries - optimize with eager loading')
                
                reasons.append(reason)
            
            # Check for memory-heavy functions (separate entry only if not already flagged)
            elif node_memory_peak > 10 * 1024 * 1024:  # Only if not already in slow_function
                reasons.append({
                    'type': 'high_memory_usage',
                    'severity': 'critical' if node_memory_peak > 50 * 1024 * 1024 else 'warning',
                    'function': node_name,
                    'memory_peak': round(node_memory_peak / (1024 * 1024), 2),
                    'message': f'Function "{node_name}" used {round(node_memory_peak / (1024 * 1024), 2)}MB peak memory',
                    'suggestions': ['Consider processing data in chunks or using generators to reduce memory usage'],
                    'source_location': f'{node_file}:{node_line}' if node_file and node_line else None
                })
            
            # Analyze queries in this function
            total_query_time = 0
            slow_queries = []
            n_plus_one_candidates = []
            
            for idx, query in enumerate(node_queries):
                query_duration = query.get('duration_ms', 0) or query.get('time_ms', 0)
                total_query_time += query_duration
                query_sql = query.get('sql', '').strip()
                
                if query_duration > query_threshold * 5:
                    slow_queries.append({
                        'sql': query_sql[:150] + '...' if len(query_sql) > 150 else query_sql,
                        'duration': round(query_duration, 2),
                        'rows_affected': query.get('rows_affected', 0)
                    })
                
                # Detect potential N+1 queries (similar queries in loop)
                if idx > 0:
                    prev_query = node_queries[idx - 1].get('sql', '').strip()
                    # Check if queries are similar (basic check)
                    if query_sql and prev_query and query_sql.split()[0:3] == prev_query.split()[0:3]:
                        n_plus_one_candidates.append(query_sql[:100])
            
            # Report slow queries with details
            for sq in slow_queries:
                reason = {
                    'type': 'slow_query',
                    'severity': 'critical' if sq['duration'] > query_threshold * 10 else 'warning',
                    'function': node_name,
                    'query': sq['sql'],
                    'full_query': sq['sql'],
                    'duration': sq['duration'],
                    'threshold': query_threshold,
                    'message': f'Query in "{node_name}" took {sq["duration"]}ms (threshold: {query_threshold}ms)',
                    'impact_percent': round((sq['duration'] / total_time) * 100, 1) if total_time > 0 else 0,
                    'suggestions': []
                }
                
                # Add source location
                if node_file and node_line:
                    reason['source_location'] = f'{node_file}:{node_line}'
                
                # Add rows affected if available
                if sq['rows_affected'] > 0:
                    reason['rows_affected'] = sq['rows_affected']
                
                # Generate specific suggestions based on query characteristics
                sql_upper = sq['sql'].upper()
                
                if sq['rows_affected'] > 10000:
                    reason['suggestions'].append('🔴 Critical: >10k rows returned - add LIMIT, pagination, or cursor-based pagination')
                elif sq['rows_affected'] > 1000:
                    reason['suggestions'].append('⚠️ Large result set (>1k rows) - add LIMIT or pagination')
                
                if 'JOIN' in sql_upper:
                    join_count = sql_upper.count('JOIN')
                    if join_count > 3:
                        reason['suggestions'].append(f'🔴 Complex query with {join_count} JOINs - consider denormalization or caching')
                    else:
                        reason['suggestions'].append('⚠️ JOIN detected - ensure indexes on join columns')
                
                if 'SELECT *' in sql_upper:
                    reason['suggestions'].append('⚠️ SELECT * used - select only required columns')
                
                if 'WHERE' not in sql_upper and 'LIMIT' not in sql_upper:
                    reason['suggestions'].append('🔴 Full table scan - add WHERE clause or indexes')
                
                if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
                    reason['suggestions'].append('⚠️ ORDER BY without LIMIT - add LIMIT for performance')
                
                if sq['duration'] > query_threshold * 20:
                    reason['suggestions'].append('🔴 Extremely slow - check execution plan and indexes')
                
                if 'LIKE' in sql_upper and sql_upper.count('%') > 0:
                    reason['suggestions'].append('⚠️ LIKE with wildcards - consider full-text search')
                
                reasons.append(reason)
            
            # Report N+1 query pattern
            if len(n_plus_one_candidates) > 3:
                reasons.append({
                    'type': 'n_plus_one_query',
                    'severity': 'critical',
                    'function': node_name,
                    'query_count': len(n_plus_one_candidates),
                    'message': f'Potential N+1 query pattern in "{node_name}" ({len(n_plus_one_candidates)} similar queries)',
                    'impact_percent': round((total_query_time / total_time) * 100, 1) if total_time > 0 else 0,
                    'example_query': n_plus_one_candidates[0] if n_plus_one_candidates else '',
                    'suggestions': [
                        '🔴 N+1 pattern detected - use select_related() or prefetch_related() in Django',
                        '⚠️ Or use JOIN in raw SQL to reduce query count',
                        '⚠️ Consider caching if data doesn\'t change frequently'
                    ],
                    'source_location': f'{node_file}:{node_line}' if node_file and node_line else None
                })
            
            # Check if this function is query-heavy
            if len(node_queries) > 5:
                reasons.append({
                    'type': 'too_many_queries',
                    'severity': 'warning' if len(node_queries) <= 10 else 'critical',
                    'function': node_name,
                    'query_count': len(node_queries),
                    'total_query_time': round(total_query_time, 2),
                    'message': f'Function "{node_name}" executed {len(node_queries)} queries (total: {round(total_query_time, 2)}ms)',
                    'impact_percent': round((total_query_time / total_time) * 100, 1) if total_time > 0 else 0,
                    'suggestions': [
                        '🔴 High query count - use bulk operations (bulk_create, bulk_update)',
                        '⚠️ Or use caching for frequently accessed data',
                        '⚠️ Consider combining queries or using aggregation'
                    ],
                    'source_location': f'{node_file}:{node_line}' if node_file and node_line else None
                })
            
            # Recursively analyze children
            for child in node.get('children', []):
                analyze_node(child, path + "/" + node_name)
        
        # Start analysis from root
        analyze_node(func_data)
        
        # Add overall analysis
        if query_count > 10:
            reasons.append({
                'type': 'overall_query_count',
                'severity': 'critical' if query_count > 20 else 'warning',
                'query_count': query_count,
                'message': f'Total of {query_count} database queries executed',
                'suggestions': [
                    '🔴 High total query count - use select_related()/prefetch_related()',
                    '⚠️ Implement query result caching',
                    '⚠️ Consider database connection pooling'
                ]
            })
        
        if total_time > 1000:
            reasons.append({
                'type': 'overall_slow',
                'severity': 'critical',
                'duration': round(total_time, 2),
                'message': f'Total request time {round(total_time, 2)}ms exceeds 1 second',
                'suggestions': [
                    '🔴 Request too slow - implement async processing (Celery/background tasks)',
                    '⚠️ Add Redis/Memcached caching layer',
                    '⚠️ Break into smaller paginated requests',
                    '⚠️ Use CDN for static content delivery'
                ]
            })
        
        # Sort by impact
        reasons.sort(key=lambda x: x.get('impact_percent', 0), reverse=True)
        
        return reasons

def _flatten_tree(node, result=None):
    """Helper function to flatten tree for backward compatibility"""
    if result is None:
        result = []
    if node:
        result.append(node)
        for child in node.get('children', []):
            _flatten_tree(child, result)
    return result

# Create a function to get the global store instance
def get_store() -> PerfwatchStore:
    """Get the global store instance"""
    return PerfwatchStore()

def store_metrics(data: Dict[str, Any]) -> None:
    """Store API metrics"""
    store = get_store()
    store.store_metrics(data)

def get_api_stats(hours: int = 24, environment: Optional[str] = None, search: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None) -> Dict[str, Any]:
    """Get API statistics for the dashboard
    
    Args:
        hours: Number of hours to look back (used if start_time/end_time not provided)
        environment: Optional environment filter
        search: Optional search query for endpoint filtering
        start_time: Optional start timestamp (epoch seconds)
        end_time: Optional end timestamp (epoch seconds)
    """
    store = get_store()
    return store.get_api_stats(hours, environment, search, start_time, end_time)

def get_api_details(api_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific API call"""
    store = get_store()
    return store.get_api_details(api_id)