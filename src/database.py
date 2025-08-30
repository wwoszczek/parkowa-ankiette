"""
Supabase PostgreSQL database configuration and connection management
"""

import os
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load environment variables
load_dotenv()

class SupabaseDB:
    def __init__(self):
        self.connection_string = self._get_connection_string()
        
    def _get_connection_string(self) -> str:
        """Get database connection string from environment or Streamlit secrets"""
        try:
            # Try environment variable first
            if os.getenv("SUPABASE_DATABASE_URL"):
                return os.getenv("SUPABASE_DATABASE_URL")
            
            # Fallback to Streamlit secrets
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                return st.secrets["supabase"]["database_url"]
                
            raise Exception("Brak konfiguracji bazy danych. Ustaw SUPABASE_DATABASE_URL w .env lub skonfiguruj secrets.toml")
        except Exception as e:
            st.error(f"Błąd konfiguracji bazy danych: {e}")
            raise e
    
    def get_connection(self):
        """Get simple, fast database connection"""
        try:
            return psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor,
                sslmode='require'
            )
        except Exception as e:
            st.error(f"Błąd połączenia z bazą danych: {e}")
            raise e
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute query and return results with explicit connection management"""
        connection = None
        try:
            connection = self.get_connection()
            
            with connection.cursor() as cur:
                cur.execute(query, params)
                
                # For SELECT queries, return results
                if query.strip().lower().startswith('select'):
                    results = [dict(row) for row in cur.fetchall()]
                    return results
                
                # For other queries, commit and return affected rows
                connection.commit()
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
            
            with connection.cursor() as cur:
                cur.executemany(query, params_list)
                connection.commit()
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
def get_db() -> SupabaseDB:
    """Get cached database instance"""
    return SupabaseDB()
