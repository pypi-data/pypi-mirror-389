import os
import yaml
from typing import Dict, Optional

class DBConfigLoader:
    DEFAULT_CONFIGS = {
        "faiss": {
            "dimension": 384,
            "metric": "l2",
            "index_type": "IndexFlatL2",
            "use_gpu": False
        },
        "pinecone": {
            "environment": os.getenv("PINECONE_ENVIRONMENT", ""),
            "project_name": os.getenv("PINECONE_PROJECT", ""),
            "dimension": 384,
            "metric": "cosine"
        },
        "milvus": {
            "host": "localhost",
            "port": 19530,
            "collection_name": "documents",
            "dimension": 384
        },
        "qdrant": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "documents",
            "dimension": 384
        }
    }

    def __init__(self, config_file: str = "db_config.yaml"):
        self.config_file = config_file
        self.db_config = self._load_config()
        
    def _load_config(self) -> Dict:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Configuration file '{self.config_file}' not found. Using default configurations.")
            return self.DEFAULT_CONFIGS
            
    def get_config(self, db_type: str) -> Dict:
        """Get configuration for specific database type"""
        if db_type not in self.db_config:
            if db_type in self.DEFAULT_CONFIGS:
                return self.DEFAULT_CONFIGS[db_type]
            raise ValueError(f"No configuration found for database type: {db_type}")
        return self.db_config[db_type]

# Example usage
if __name__ == "__main__":
    loader = DBConfigLoader()
    
    # Load configuration for FAISS
    faiss_config = loader.get_config("faiss")
    print("FAISS Config:", faiss_config)
    
    # Load configuration for Milvus
    milvus_config = loader.get_config("milvus")
    print("Milvus Config:", milvus_config)
