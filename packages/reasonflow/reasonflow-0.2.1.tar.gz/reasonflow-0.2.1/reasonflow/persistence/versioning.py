from typing import Dict, List, Optional
import os
from datetime import datetime
import json
from .database import Database

class VersionManager:
    def __init__(self):
        self.db = Database()
        self._initialize_tables()
        
    def _initialize_tables(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS versions (
                        id TEXT PRIMARY KEY,
                        entity_id TEXT,
                        entity_type TEXT,
                        version_number INTEGER,
                        data JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except Exception as e:
            print(f"Error initializing version tables: {str(e)}")
            
    def create_version(self, entity_id: str, entity_type: str, data: Dict) -> Optional[str]:
        try:
            # Get current version number
            current_version = self.get_latest_version(entity_id, entity_type)
            version_number = (current_version["version_number"] + 1) if current_version else 1
            
            version_id = f"{entity_id}-v{version_number}"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO versions (id, entity_id, entity_type, version_number, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (version_id, entity_id, entity_type, version_number, json.dumps(data)))
                
            return version_id
            
        except Exception as e:
            print(f"Error creating version: {str(e)}")
            return None
            
    def get_version(self, version_id: str) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM versions WHERE id = ?", (version_id,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "entity_id": row[1],
                        "entity_type": row[2],
                        "version_number": row[3],
                        "data": json.loads(row[4]),
                        "created_at": row[5]
                    }
                return None
                
        except Exception as e:
            print(f"Error getting version: {str(e)}")
            return None
            
    def get_latest_version(self, entity_id: str, entity_type: str) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM versions 
                    WHERE entity_id = ? AND entity_type = ?
                    ORDER BY version_number DESC LIMIT 1
                """, (entity_id, entity_type))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "entity_id": row[1],
                        "entity_type": row[2],
                        "version_number": row[3],
                        "data": json.loads(row[4]),
                        "created_at": row[5]
                    }
                return None
                
        except Exception as e:
            print(f"Error getting latest version: {str(e)}")
            return None
            
    def list_versions(self, entity_id: str, entity_type: str) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM versions 
                    WHERE entity_id = ? AND entity_type = ?
                    ORDER BY version_number DESC
                """, (entity_id, entity_type))
                
                versions = []
                for row in cursor.fetchall():
                    versions.append({
                        "id": row[0],
                        "entity_id": row[1],
                        "entity_type": row[2],
                        "version_number": row[3],
                        "data": json.loads(row[4]),
                        "created_at": row[5]
                    })
                return versions
                
        except Exception as e:
            print(f"Error listing versions: {str(e)}")
            return [] 