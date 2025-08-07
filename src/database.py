"""
Neon PostgreSQL database configuration and connection management
"""

import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load environment variables
load_dotenv()

class NeonDB:
    def __init__(self):
        self.connection_string = self._get_connection_string()
        
    def _get_connection_string(self) -> str:
        """Get database connection string from environment or Streamlit secrets"""
        try:
            # Try environment variable first
            if os.getenv("NEON_DATABASE_URL"):
                return os.getenv("NEON_DATABASE_URL")
            
            # Fallback to Streamlit secrets
            if hasattr(st, 'secrets') and 'neon' in st.secrets:
                return st.secrets["neon"]["database_url"]
                
            raise Exception("Brak konfiguracji bazy danych. Ustaw NEON_DATABASE_URL w .env lub skonfiguruj secrets.toml")
        except Exception as e:
            st.error(f"Błąd konfiguracji bazy danych: {e}")
            raise e
    
    def get_connection(self):
        """Get database connection with very aggressive timeouts to prevent idle connections"""
        try:
            # Check if we should use pooled or unpooled connection
            connection_string = self.connection_string
            
            # If using pooler, modify to use unpooled connection for timeout settings
            if 'pooler.gwc.azure.neon.tech' in connection_string:
                # Replace pooler with direct connection to avoid startup parameter issues
                connection_string = connection_string.replace('-pooler.gwc.azure.neon.tech', '.gwc.azure.neon.tech')
            
            conn = psycopg2.connect(
                connection_string,
                cursor_factory=RealDictCursor,
                sslmode='require',
                connect_timeout=10,
                application_name='parkowa-ankiette-v2'
            )
            
            # Set timeout parameters after connection is established
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '60s'")
                cur.execute("SET idle_in_transaction_session_timeout = '30s'")
                cur.execute("SET lock_timeout = '15s'")
                # Note: idle_session_timeout and tcp_user_timeout might not be available in all PostgreSQL versions
                try:
                    cur.execute("SET idle_session_timeout = '15s'")
                except:
                    pass  # Ignore if not supported
            
            conn.commit()
            return conn
            
        except Exception as e:
            st.error(f"Błąd połączenia z bazą danych: {e}")
            raise e
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute query and return results with explicit connection management"""
        connection = None
        try:
            connection = self.get_connection()
            # Set autocommit to avoid hanging transactions
            connection.autocommit = True
            
            with connection.cursor() as cur:
                cur.execute(query, params)
                
                # For SELECT queries, return results
                if query.strip().lower().startswith('select'):
                    results = [dict(row) for row in cur.fetchall()]
                    return results
                
                # For other queries, return affected rows (autocommit handles commit)
                return cur.rowcount
                    
        except Exception as e:
            st.error(f"Błąd wykonywania zapytania: {e}")
            raise e
        finally:
            # ALWAYS close connection explicitly
            if connection and not connection.closed:
                connection.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets with explicit connection management"""
        connection = None
        try:
            connection = self.get_connection()
            connection.autocommit = True
            
            with connection.cursor() as cur:
                cur.executemany(query, params_list)
                return cur.rowcount
        except Exception as e:
            st.error(f"Błąd wykonywania zapytań wsadowych: {e}")
            raise e
        finally:
            # ALWAYS close connection explicitly
            if connection and not connection.closed:
                connection.close()

# Global database instance
@st.cache_resource
def get_db() -> NeonDB:
    """Get cached database instance"""
    return NeonDB()


def cleanup_connections():
    """Force cleanup of any hanging database connections and kill idle sessions"""
    try:
        # Clear Streamlit cache to force new DB instance
        get_db.clear()
        
        # Try to kill any remaining idle sessions directly in DB
        try:
            temp_db = NeonDB()
            temp_db.execute_query("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND state = 'idle'
                AND pid != pg_backend_pid()
            """)
        except:
            pass  # Ignore errors, this is cleanup
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return True
    except Exception as e:
        st.error(f"Błąd czyszczenia połączeń: {e}")
        return False
