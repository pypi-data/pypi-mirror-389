import os
from typing import Dict, Any, Optional
import sqlite3
import psycopg2
from contextlib import contextmanager

class Database:
    def __init__(self, db_type: str = "sqlite", connection_string: Optional[str] = None):
        self.db_type = db_type
        self.connection_string = connection_string or os.getenv("DB_CONNECTION_STRING")
        
        if db_type == "sqlite":
            self.connection_string = self.connection_string or "reasonflow.db"
            
    @contextmanager
    def get_connection(self):
        try:
            if self.db_type == "sqlite":
                conn = sqlite3.connect(self.connection_string)
            else:
                conn = psycopg2.connect(self.connection_string)
            yield conn
            conn.commit()
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()
            
    def initialize_tables(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflows (
                        id TEXT PRIMARY KEY,
                        state JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except Exception as e:
            print(f"Error initializing tables: {str(e)}") 