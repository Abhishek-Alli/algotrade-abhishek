"""
Database connection module
Supports both PostgreSQL and SQLite
"""
import os
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logger.warning("psycopg2 not available. Install with: pip install psycopg2-binary")

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("sqlite3 not available")


class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, db_type: str = None):
        self.db_type = db_type or Config.DB_TYPE
        self.connection = None
        self.connection_pool = None
        
        if self.db_type == 'postgresql':
            self._init_postgresql()
        else:
            self._init_sqlite()
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connection"""
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        
        try:
            # Use connection string if provided
            if Config.DB_URL:
                self.connection_string = Config.DB_URL
            else:
                # Build connection string from components
                self.connection_string = (
                    f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@"
                    f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
                )
            
            # Create connection pool
            self.connection_pool = pool.SimpleConnectionPool(
                1, 20,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            
            if self.connection_pool:
                logger.info("PostgreSQL connection pool created")
                self._create_tables()
            else:
                raise Exception("Failed to create PostgreSQL connection pool")
                
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL: {e}")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite connection"""
        if not SQLITE_AVAILABLE:
            raise ImportError("sqlite3 not available")
        
        self.db_path = 'market_data.db'
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        logger.info(f"SQLite connection established: {self.db_path}")
        self._create_tables()
    
    def get_connection(self):
        """Get database connection"""
        if self.db_type == 'postgresql':
            if self.connection_pool:
                return self.connection_pool.getconn()
            else:
                raise Exception("PostgreSQL connection pool not initialized")
        else:
            if not self.connection:
                self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            return self.connection
    
    def return_connection(self, conn):
        """Return connection to pool (PostgreSQL only)"""
        if self.db_type == 'postgresql' and self.connection_pool:
            self.connection_pool.putconn(conn)
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute SQL query"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                if self.db_type == 'postgresql':
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(query, params if params else None)
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    return [dict(zip(columns, row)) for row in results]
            else:
                conn.commit()
                return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and self.db_type == 'postgresql':
                self.return_connection(conn)
            elif conn and self.db_type == 'sqlite':
                pass  # SQLite connection stays open
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        if self.db_type == 'postgresql':
            self._create_postgresql_tables()
        else:
            self._create_sqlite_tables()
    
    def _create_postgresql_tables(self):
        """Create PostgreSQL tables"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # OHLCV Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    open DECIMAL(20, 8),
                    high DECIMAL(20, 8),
                    low DECIMAL(20, 8),
                    close DECIMAL(20, 8),
                    volume DECIMAL(20, 8),
                    timeframe VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp, timeframe)
                )
            ''')
            
            # Create index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe 
                ON ohlcv_data(symbol, timeframe, timestamp DESC)
            ''')
            
            # News Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(50),
                    headline TEXT,
                    source VARCHAR(100),
                    published_at TIMESTAMP,
                    sentiment_score DECIMAL(5, 3),
                    content TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_news_symbol_published 
                ON news_data(symbol, published_at DESC)
            ''')
            
            # Sentiment Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(50),
                    platform VARCHAR(50),
                    text TEXT,
                    timestamp TIMESTAMP,
                    sentiment_score DECIMAL(5, 3),
                    engagement_score DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("PostgreSQL tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def _create_sqlite_tables(self):
        """Create SQLite tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # OHLCV Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ohlcv_data (
                    symbol TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    timeframe TEXT,
                    PRIMARY KEY (symbol, timestamp, timeframe)
                )
            ''')
            
            # News Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    headline TEXT,
                    source TEXT,
                    published_at TEXT,
                    sentiment_score REAL,
                    content TEXT,
                    url TEXT
                )
            ''')
            
            # Sentiment Data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    platform TEXT,
                    text TEXT,
                    timestamp TEXT,
                    sentiment_score REAL,
                    engagement_score REAL
                )
            ''')
            
            conn.commit()
            logger.info("SQLite tables created/verified")
            
        except Exception as e:
            logger.error(f"Error creating SQLite tables: {e}")
            raise
    
    def close(self):
        """Close database connections"""
        if self.db_type == 'postgresql' and self.connection_pool:
            self.connection_pool.closeall()
            logger.info("PostgreSQL connection pool closed")
        elif self.db_type == 'sqlite' and self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")


# Global database instance
_db_instance = None

def get_db():
    """Get database instance (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


