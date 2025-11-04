import json
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import threading
import schedule
import time

# Database imports (lazy loaded)
_db_modules = {}


def _get_db_module(db_type: str):
    """Lazy load database modules"""
    if db_type not in _db_modules:
        if db_type == "mongodb":
            try:
                from pymongo import MongoClient
                _db_modules["mongodb"] = MongoClient
            except ImportError:
                raise ImportError("pymongo is required for MongoDB storage. Install with: pip install pymongo")
        elif db_type == "mysql":
            try:
                import mysql.connector
                _db_modules["mysql"] = mysql.connector
            except ImportError:
                raise ImportError("mysql-connector-python is required for MySQL storage. Install with: pip install mysql-connector-python")
        elif db_type == "postgresql":
            try:
                import psycopg2
                _db_modules["postgresql"] = psycopg2
            except ImportError:
                raise ImportError("psycopg2 is required for PostgreSQL storage. Install with: pip install psycopg2-binary")
        elif db_type == "sqlite":
            import sqlite3
            _db_modules["sqlite"] = sqlite3
    return _db_modules[db_type]


class LogStorage(ABC):
    """Abstract base class for log storage"""
    
    @abstractmethod
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store a log entry"""
        pass
    
    @abstractmethod
    def cleanup_old_logs(self, days: int) -> int:
        """Remove logs older than specified days. Returns count of deleted logs."""
        pass
    
    @abstractmethod
    def close(self):
        """Close any open connections"""
        pass


class LocalFileStorage(LogStorage):
    """Store logs in local JSON files with automatic cleanup"""
    
    def __init__(self, log_dir: str = "logs", cleanup_days: int = 7):
        self.log_dir = Path(log_dir)
        self.cleanup_days = cleanup_days
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Start cleanup scheduler in background thread
        self._start_cleanup_scheduler()
    
    def _get_log_file_path(self) -> Path:
        """Generate log file path based on current date"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"logs_{date_str}.jsonl"
    
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store log in daily JSONL file"""
        try:
            log_file = self._get_log_file_path()
            with open(log_file, "a", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False)
                f.write("\n")
            return True
        except Exception as e:
            print(f"❌ Failed to store log locally: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = None) -> int:
        """Delete log files older than specified days"""
        cleanup_days = days or self.cleanup_days
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)
        deleted_count = 0
        
        try:
            for log_file in self.log_dir.glob("logs_*.jsonl"):
                # Extract date from filename
                try:
                    date_str = log_file.stem.replace("logs_", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
                        print(f"🗑️  Deleted old log file: {log_file.name}")
                except ValueError:
                    continue
            
            return deleted_count
        except Exception as e:
            print(f"❌ Error during log cleanup: {e}")
            return deleted_count
    
    def _start_cleanup_scheduler(self):
        """Start background thread for periodic cleanup"""
        def run_scheduler():
            schedule.every().day.at("02:00").do(self.cleanup_old_logs)
            while True:
                schedule.run_pending()
                time.sleep(3600)  # Check every hour
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def close(self):
        """No cleanup needed for file storage"""
        pass


class MongoDBStorage(LogStorage):
    """Store logs in MongoDB with TTL index for automatic cleanup"""
    
    def __init__(self, connection_string: str, database_name: str = "logs_db", 
                 collection_name: str = "logs", cleanup_days: int = 7):
        MongoClient = _get_db_module("mongodb")
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.cleanup_days = cleanup_days
        
        # Create TTL index for automatic cleanup
        self._create_ttl_index()
    
    def _create_ttl_index(self):
        """Create TTL index on timestamp field for automatic cleanup"""
        try:
            self.collection.create_index(
                "created_at",
                expireAfterSeconds=self.cleanup_days * 86400  # Convert days to seconds
            )
            print(f"✅ MongoDB TTL index created (cleanup after {self.cleanup_days} days)")
        except Exception as e:
            print(f"⚠️  Warning: Could not create TTL index: {e}")
    
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store log in MongoDB"""
        try:
            log_data["created_at"] = datetime.now()
            self.collection.insert_one(log_data)
            return True
        except Exception as e:
            print(f"❌ Failed to store log in MongoDB: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = None) -> int:
        """Manually delete old logs (TTL index handles this automatically)"""
        cleanup_days = days or self.cleanup_days
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)
        
        try:
            result = self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            return result.deleted_count
        except Exception as e:
            print(f"❌ Error during MongoDB cleanup: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


class MySQLStorage(LogStorage):
    """Store logs in MySQL with automatic cleanup"""
    
    def __init__(self, connection_string: str, table_name: str = "logs", cleanup_days: int = 7):
        mysql = _get_db_module("mysql")
        
        # Parse connection string
        conn_params = self._parse_connection_string(connection_string)
        self.conn = mysql.connect(**conn_params)
        self.table_name = table_name
        self.cleanup_days = cleanup_days
        
        # Create table if not exists
        self._create_table()
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()
    
    def _parse_connection_string(self, conn_str: str) -> Dict:
        """Parse MySQL connection string"""
        # Format: mysql://user:password@host:port/database
        from urllib.parse import urlparse
        parsed = urlparse(conn_str)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 3306,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/")
        }
    
    def _create_table(self):
        """Create logs table if not exists"""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                route VARCHAR(500),
                method VARCHAR(10),
                status_code INT,
                processing_time_ms FLOAT,
                log_data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at),
                INDEX idx_route (route),
                INDEX idx_status (status_code)
            )
        """)
        self.conn.commit()
        cursor.close()
        print(f"✅ MySQL table '{self.table_name}' ready")
    
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store log in MySQL"""
        try:
            cursor = self.conn.cursor()
            
            # Extract key fields
            timestamp_str = log_data.get("timestamp")
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S") if timestamp_str else datetime.now()
            route = log_data.get("request", {}).get("route", "")
            method = log_data.get("request", {}).get("method", "")
            status_code = log_data.get("response", {}).get("status", 0)
            processing_time = float(log_data.get("performance", {}).get("processingTime", "0").replace(" ms", ""))
            
            cursor.execute(f"""
                INSERT INTO {self.table_name} 
                (timestamp, route, method, status_code, processing_time_ms, log_data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (timestamp, route, method, status_code, processing_time, json.dumps(log_data)))
            
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Failed to store log in MySQL: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = None) -> int:
        """Delete logs older than specified days"""
        cleanup_days = days or self.cleanup_days
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                DELETE FROM {self.table_name}
                WHERE created_at < %s
            """, (cutoff_date,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return deleted_count
        except Exception as e:
            print(f"❌ Error during MySQL cleanup: {e}")
            return 0
    
    def _start_cleanup_scheduler(self):
        """Start background thread for periodic cleanup"""
        def run_scheduler():
            schedule.every().day.at("02:00").do(self.cleanup_old_logs)
            while True:
                schedule.run_pending()
                time.sleep(3600)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def close(self):
        """Close MySQL connection"""
        self.conn.close()


class PostgreSQLStorage(LogStorage):
    """Store logs in PostgreSQL with automatic cleanup"""
    
    def __init__(self, connection_string: str, table_name: str = "logs", cleanup_days: int = 7):
        psycopg2 = _get_db_module("postgresql")
        self.conn = psycopg2.connect(connection_string)
        self.table_name = table_name
        self.cleanup_days = cleanup_days
        
        # Create table if not exists
        self._create_table()
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()
    
    def _create_table(self):
        """Create logs table if not exists"""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                route VARCHAR(500),
                method VARCHAR(10),
                status_code INT,
                processing_time_ms FLOAT,
                log_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at ON {self.table_name}(created_at)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_route ON {self.table_name}(route)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_status ON {self.table_name}(status_code)")
        self.conn.commit()
        cursor.close()
        print(f"✅ PostgreSQL table '{self.table_name}' ready")
    
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store log in PostgreSQL"""
        try:
            cursor = self.conn.cursor()
            
            # Extract key fields
            timestamp_str = log_data.get("timestamp")
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S") if timestamp_str else datetime.now()
            route = log_data.get("request", {}).get("route", "")
            method = log_data.get("request", {}).get("method", "")
            status_code = log_data.get("response", {}).get("status", 0)
            processing_time = float(log_data.get("performance", {}).get("processingTime", "0").replace(" ms", ""))
            
            cursor.execute(f"""
                INSERT INTO {self.table_name} 
                (timestamp, route, method, status_code, processing_time_ms, log_data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (timestamp, route, method, status_code, processing_time, json.dumps(log_data)))
            
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Failed to store log in PostgreSQL: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = None) -> int:
        """Delete logs older than specified days"""
        cleanup_days = days or self.cleanup_days
        cutoff_date = datetime.now() - timedelta(days=cleanup_days)
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                DELETE FROM {self.table_name}
                WHERE created_at < %s
            """, (cutoff_date,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return deleted_count
        except Exception as e:
            print(f"❌ Error during PostgreSQL cleanup: {e}")
            return 0
    
    def _start_cleanup_scheduler(self):
        """Start background thread for periodic cleanup"""
        def run_scheduler():
            schedule.every().day.at("02:00").do(self.cleanup_old_logs)
            while True:
                schedule.run_pending()
                time.sleep(3600)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def close(self):
        """Close PostgreSQL connection"""
        self.conn.close()


class SQLiteStorage(LogStorage):
    """Store logs in SQLite with automatic cleanup"""
    
    def __init__(self, db_path: str = "logs.db", table_name: str = "logs", cleanup_days: int = 7):
        sqlite3 = _get_db_module("sqlite")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.table_name = table_name
        self.cleanup_days = cleanup_days
        
        # Create table if not exists
        self._create_table()
        
        # Start cleanup scheduler
        self._start_cleanup_scheduler()
    
    def _create_table(self):
        """Create logs table if not exists"""
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                route TEXT,
                method TEXT,
                status_code INTEGER,
                processing_time_ms REAL,
                log_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created_at ON {self.table_name}(created_at)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_route ON {self.table_name}(route)")
        self.conn.commit()
        cursor.close()
        print(f"✅ SQLite table '{self.table_name}' ready")
    
    def store_log(self, log_data: Dict[str, Any]) -> bool:
        """Store log in SQLite"""
        try:
            cursor = self.conn.cursor()
            
            # Extract key fields
            timestamp = log_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            route = log_data.get("request", {}).get("route", "")
            method = log_data.get("request", {}).get("method", "")
            status_code = log_data.get("response", {}).get("status", 0)
            processing_time = float(log_data.get("performance", {}).get("processingTime", "0").replace(" ms", ""))
            
            cursor.execute(f"""
                INSERT INTO {self.table_name} 
                (timestamp, route, method, status_code, processing_time_ms, log_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, route, method, status_code, processing_time, json.dumps(log_data)))
            
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Failed to store log in SQLite: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = None) -> int:
        """Delete logs older than specified days"""
        cleanup_days = days or self.cleanup_days
        cutoff_date = (datetime.now() - timedelta(days=cleanup_days)).strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                DELETE FROM {self.table_name}
                WHERE created_at < ?
            """, (cutoff_date,))
            deleted_count = cursor.rowcount
            self.conn.commit()
            cursor.close()
            return deleted_count
        except Exception as e:
            print(f"❌ Error during SQLite cleanup: {e}")
            return 0
    
    def _start_cleanup_scheduler(self):
        """Start background thread for periodic cleanup"""
        def run_scheduler():
            schedule.every().day.at("02:00").do(self.cleanup_old_logs)
            while True:
                schedule.run_pending()
                time.sleep(3600)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
    
    def close(self):
        """Close SQLite connection"""
        self.conn.close()


def create_log_storage(storage_type: str, connection_string: Optional[str] = None, 
                       cleanup_days: int = 7, **kwargs) -> LogStorage:
    """
    Factory function to create appropriate log storage instance.
    
    Args:
        storage_type: Type of storage ('local', 'mongodb', 'mysql', 'postgresql', 'sqlite')
        connection_string: Database connection string (not needed for local storage)
        cleanup_days: Days after which logs should be deleted (default: 7)
        **kwargs: Additional storage-specific arguments
        
    Returns:
        LogStorage instance
        
    Examples:
        # Local file storage
        storage = create_log_storage('local', cleanup_days=7)
        
        # MongoDB
        storage = create_log_storage('mongodb', 
            connection_string='mongodb://localhost:27017',
            database_name='logs_db',
            cleanup_days=7)
        
        # MySQL
        storage = create_log_storage('mysql',
            connection_string='mysql://user:pass@localhost:3306/logs_db',
            cleanup_days=7)
        
        # PostgreSQL
        storage = create_log_storage('postgresql',
            connection_string='postgresql://user:pass@localhost:5432/logs_db',
            cleanup_days=7)
        
        # SQLite
        storage = create_log_storage('sqlite',
            db_path='logs.db',
            cleanup_days=7)
    """
    storage_type = storage_type.lower()
    
    if storage_type == "local":
        log_dir = kwargs.get("log_dir", "logs")
        return LocalFileStorage(log_dir=log_dir, cleanup_days=cleanup_days)
    
    elif storage_type == "mongodb":
        if not connection_string:
            raise ValueError("connection_string is required for MongoDB storage")
        database_name = kwargs.get("database_name", "logs_db")
        collection_name = kwargs.get("collection_name", "logs")
        return MongoDBStorage(connection_string, database_name, collection_name, cleanup_days)
    
    elif storage_type == "mysql":
        if not connection_string:
            raise ValueError("connection_string is required for MySQL storage")
        table_name = kwargs.get("table_name", "logs")
        return MySQLStorage(connection_string, table_name, cleanup_days)
    
    elif storage_type == "postgresql":
        if not connection_string:
            raise ValueError("connection_string is required for PostgreSQL storage")
        table_name = kwargs.get("table_name", "logs")
        return PostgreSQLStorage(connection_string, table_name, cleanup_days)
    
    elif storage_type == "sqlite":
        db_path = kwargs.get("db_path", "logs.db")
        table_name = kwargs.get("table_name", "logs")
        return SQLiteStorage(db_path, table_name, cleanup_days)
    
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}. "
                        f"Supported types: local, mongodb, mysql, postgresql, sqlite")