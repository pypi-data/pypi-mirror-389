"""
PerfWatch Dashboard Authentication System
DATABASE-based authentication - users stored in SQLite
"""
from typing import Optional, Dict
from passlib.context import CryptContext

# Password hashing context - using pbkdf2 for compatibility
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"], 
    deprecated="auto"
)


class PerfWatchAuth:
    """PerfWatch dashboard authentication - DATABASE-based"""
    
    @staticmethod
    def verify_password(username: str, password: str) -> bool:
        """Verify username and password against DATABASE"""
        from perfwatch.db.store import get_user_by_username
        
        user = get_user_by_username(username)
        if not user:
            return False
        
        if not user.get('is_active', True):
            return False
        
        stored_hash = user['password_hash']
        return pwd_context.verify(password, stored_hash)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)


# Session management (simple in-memory for now)
_active_sessions = {}

# Session timeout: 15 minutes
SESSION_TIMEOUT_MINUTES = 15


def create_session(username: str) -> str:
    """Create a new session for authenticated user - expires in 15 minutes"""
    import uuid
    from datetime import datetime, timedelta
    
    session_id = str(uuid.uuid4())
    _active_sessions[session_id] = {
        'username': username,
        'created_at': datetime.now(),
        'last_activity': datetime.now(),
        'expires_at': datetime.now() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    }
    return session_id


def verify_session(session_id: str) -> Optional[str]:
    """Verify session and return username if valid. Auto-extends on activity."""
    from datetime import datetime, timedelta
    
    session = _active_sessions.get(session_id)
    if not session:
        return None
    
    now = datetime.now()
    
    # Check if session expired (either absolute timeout or idle timeout)
    if now > session['expires_at']:
        destroy_session(session_id)
        return None
    
    # Check idle timeout (15 minutes since last activity)
    idle_limit = session['last_activity'] + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    if now > idle_limit:
        destroy_session(session_id)
        return None
    
    # Session is valid - update last activity and extend expiry
    session['last_activity'] = now
    session['expires_at'] = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    return session['username']


def destroy_session(session_id: str) -> bool:
    """Destroy a session immediately"""
    if session_id in _active_sessions:
        del _active_sessions[session_id]
        return True
    return False

