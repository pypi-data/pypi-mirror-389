import os
import toml

DEFAULT_CONFIG = {
    "db": {
        "engine": "sqlite",  # Default: sqlite (change to postgresql or mysql if needed)
        # SQLite config
        "path": "./perfwatch.db",
        # PostgreSQL/MySQL config (only if engine = "postgresql" or "mysql")
        "host": "",
        "port": "",
        "name": "",
        "user": "",
        "password": ""
    },
    "thresholds": {
        "function_ms": 100,
        "query_ms": 50
    },
    "profiling": {
        "enabled": False  
    },
    "auth": {
        "users": {}  # Users now stored in database, not config
    }
}

class PerfWatchConfig:
    def __init__(self, config_file="perfwatch.conf"):
        self.config_file = config_file
        self._config = DEFAULT_CONFIG.copy()
        self.load()
        
    def validate_db_config(self):
        """Validate database configuration based on engine type"""
        db_config = self._config.get("db", {})
        engine = db_config.get("engine", "").lower()
        
        # Validate engine type
        supported_engines = ["sqlite", "postgresql", "mysql"]
        if not engine:
            raise ValueError(
                "❌ Database engine not configured!\n"
                "Please set 'db.engine' in perfwatch.conf to one of: sqlite, postgresql, mysql"
            )
        
        if engine not in supported_engines:
            raise ValueError(
                f"❌ Unsupported database engine: '{engine}'\n"
                f"Supported engines: {', '.join(supported_engines)}"
            )
        
        # Validate SQLite configuration
        if engine == "sqlite":
            db_path = db_config.get("path")
            if not db_path:
                raise ValueError(
                    "❌ SQLite database path not configured!\n"
                    "Please set 'db.path' in perfwatch.conf\n"
                    "Example: db.path = './perfwatch.db'"
                )
            return {"engine": "sqlite", "path": db_path}
        
        # Validate PostgreSQL/MySQL configuration
        required_fields = ["host", "port", "name", "user", "password"]
        missing_fields = [f for f in required_fields if not db_config.get(f)]
        
        if missing_fields:
            raise ValueError(
                f"❌ {engine.upper()} configuration incomplete!\n"
                f"Missing fields: {', '.join(missing_fields)}\n\n"
                f"Required in perfwatch.conf:\n"
                f"  db.host = 'localhost'\n"
                f"  db.port = {5432 if engine == 'postgresql' else 3306}\n"
                f"  db.name = 'perfwatch'\n"
                f"  db.user = 'your_user'\n"
                f"  db.password = 'your_password'"
            )
        
        return {
            "engine": engine,
            "host": db_config["host"],
            "port": int(db_config["port"]),
            "name": db_config["name"],
            "user": db_config["user"],
            "password": db_config["password"]
        }

    def load(self):
        if os.path.exists(self.config_file):
            user_config = toml.load(self.config_file)
            self._merge(self._config, user_config)

    def save(self):
        with open(self.config_file, "w") as f:
            toml.dump(self._config, f)

    def get(self, key_path, default=None):
        keys = key_path.split(".")
        cfg = self._config
        for k in keys:
            cfg = cfg.get(k, {})
        return cfg or default

    def set(self, key_path, value):
        keys = key_path.split(".")
        cfg = self._config
        for k in keys[:-1]:
            cfg = cfg.setdefault(k, {})
        cfg[keys[-1]] = value
        self.save()

    def _merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

# Singleton instance for library-wide usage
_config_instance = PerfWatchConfig()

def save_user_config(config_dict):
    _config_instance._merge(_config_instance._config, config_dict)
    _config_instance.save()
