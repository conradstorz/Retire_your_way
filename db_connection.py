"""
Database Connection Abstraction Layer

Provides a unified interface for both SQLite (local development) and PostgreSQL (cloud deployment).
Automatically detects the environment and uses the appropriate database connection.

For Streamlit Cloud deployment with PostgreSQL:
1. Create a free Supabase account (supabase.com)
2. Create a new project and get your connection string
3. Add to Streamlit secrets (.streamlit/secrets.toml):
   [postgres]
   host = "your-project.supabase.co"
   port = 5432
   database = "postgres"
   user = "postgres"
   password = "your-password"

For local development:
- Uses SQLite by default (no configuration needed)
"""

import os
from typing import Optional, Any, List, Tuple
from contextlib import contextmanager
import streamlit as st


class DatabaseConnection:
    """Abstract database connection that works with both SQLite and PostgreSQL."""
    
    def __init__(self):
        """Initialize database connection based on environment."""
        self.db_type = self._detect_database_type()
        self.connection_params = self._get_connection_params()
        
        if self.db_type == 'postgresql':
            import psycopg2
            self.db_module = psycopg2
        else:
            import sqlite3
            self.db_module = sqlite3
    
    def _detect_database_type(self) -> str:
        """Detect which database to use based on environment."""
        # Check Streamlit secrets first
        try:
            if hasattr(st, 'secrets') and 'postgres' in st.secrets:
                return 'postgresql'
        except Exception:
            # No secrets file or secrets not configured - that's ok
            pass
        
        # Check environment variables
        if os.getenv('DATABASE_URL'):  # Render, Heroku, Railway
            return 'postgresql'
        
        # Default to SQLite for local development
        return 'sqlite'
    
    def _get_connection_params(self) -> dict:
        """Get connection parameters based on database type."""
        if self.db_type == 'postgresql':
            # Try Streamlit secrets first
            try:
                if hasattr(st, 'secrets') and 'postgres' in st.secrets:
                    pg = st.secrets['postgres']
                    return {
                        'host': pg.get('host'),
                        'port': pg.get('port', 5432),
                        'database': pg.get('database', 'postgres'),
                        'user': pg.get('user'),
                        'password': pg.get('password')
                    }
            except Exception:
                # No secrets configured - fall through to DATABASE_URL
                pass
            
            # Try DATABASE_URL environment variable (Render, Heroku, Railway)
            db_url = os.getenv('DATABASE_URL')
            if db_url:
                # Parse DATABASE_URL
                # Format: postgres://user:pass@host:port/database or postgresql://...
                if db_url.startswith('postgres://'):
                    db_url = db_url.replace('postgres://', 'postgresql://')
                
                from urllib.parse import urlparse
                parsed = urlparse(db_url)
                return {
                    'host': parsed.hostname,
                    'port': parsed.port or 5432,
                    'database': parsed.path[1:],  # Remove leading /
                    'user': parsed.username,
                    'password': parsed.password
                }
        
        # SQLite default
        return {'database': 'user_data.db'}
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (context manager)."""
        if self.db_type == 'postgresql':
            conn = self.db_module.connect(**self.connection_params)
        else:
            conn = self.db_module.connect(self.connection_params['database'])
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """
        Execute a SELECT query and return all results.
        
        Args:
            query: SQL query with placeholders
            params: Query parameters
            
        Returns:
            List of tuples containing query results
        """
        # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s)
        if self.db_type == 'postgresql':
            query = self._convert_placeholders(query)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query with placeholders
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s)
        if self.db_type == 'postgresql':
            query = self._convert_placeholders(query)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute the same query multiple times with different parameters.
        
        Args:
            query: SQL query with placeholders
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        # Convert SQLite placeholders (?) to PostgreSQL placeholders (%s)
        if self.db_type == 'postgresql':
            query = self._convert_placeholders(query)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def _convert_placeholders(self, query: str) -> str:
        """Convert SQLite placeholders (?) to PostgreSQL placeholders (%s)."""
        return query.replace('?', '%s')
    
    def create_table_if_not_exists(self, table_name: str, schema: str):
        """
        Create a table if it doesn't exist.
        
        Args:
            table_name: Name of the table
            schema: Table schema (SQL CREATE TABLE statement without CREATE TABLE IF NOT EXISTS)
        """
        if self.db_type == 'postgresql':
            # PostgreSQL uses SERIAL instead of AUTOINCREMENT
            schema = schema.replace('AUTOINCREMENT', 'GENERATED BY DEFAULT AS IDENTITY')
            schema = schema.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            
            # PostgreSQL uses TEXT for all text types
            schema = schema.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 
                                   "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        self.execute_update(query)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        if self.db_type == 'postgresql':
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """
            result = self.execute_query(query, (table_name,))
            return result[0][0] if result else False
        else:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        if self.db_type == 'postgresql':
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = %s 
                    AND column_name = %s
                )
            """
            result = self.execute_query(query, (table_name, column_name))
            return result[0][0] if result else False
        else:
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(query)
            columns = [row[1] for row in result]
            return column_name in columns
    
    def add_column_if_not_exists(self, table_name: str, column_name: str, 
                                  column_type: str, default_value: Any = None):
        """Add a column to a table if it doesn't exist."""
        if self.column_exists(table_name, column_name):
            return
        
        if self.db_type == 'postgresql':
            # PostgreSQL syntax
            default_clause = f"DEFAULT {default_value}" if default_value is not None else ""
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {default_clause}"
        else:
            # SQLite syntax
            default_clause = f"DEFAULT {default_value}" if default_value is not None else ""
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} {default_clause}"
        
        self.execute_update(query)
    
    def get_last_insert_id(self, cursor) -> int:
        """Get the ID of the last inserted row."""
        if self.db_type == 'postgresql':
            return cursor.fetchone()[0]
        else:
            return cursor.lastrowid


# Global database connection instance
_db_connection = None


def get_db() -> DatabaseConnection:
    """Get the global database connection instance."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection
