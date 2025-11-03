from typing import Dict, List, Optional, BinaryIO
import os
from datetime import datetime
import hashlib
from reasonflow.persistence.object_storage import ObjectStorage
from reasonflow.integrations.rag_integrations import RAGIntegration

class DocumentManager:
    def __init__(self, storage_provider: str = "s3", index_path: Optional[str] = None):
        self.storage = ObjectStorage(storage_provider)
        self.rag = RAGIntegration()
        self.index_path = index_path or os.getenv("DOCUMENT_INDEX_PATH", "./document_index")
        
        # Load existing index if available
        if os.path.exists(self.index_path):
            self.rag.load_index(self.index_path)
            
    def upload_document(self, file_path: str, metadata: Dict) -> Optional[str]:
        try:
            # Generate document ID
            doc_id = hashlib.md5(f"{file_path}-{datetime.now()}".encode()).hexdigest()
            
            # Upload to object storage
            bucket = os.getenv("DOCUMENT_BUCKET", "reasonflow-documents")
            object_name = f"documents/{doc_id}/{os.path.basename(file_path)}"
            
            if not self.storage.upload_file(file_path, bucket, object_name):
                return None
                
            # Index document content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            document = {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
                "storage_path": object_name
            }
            
            self.rag.add_documents([document])
            self.rag.save_index(self.index_path)
            
            return doc_id
            
        except Exception as e:
            print(f"Error uploading document: {str(e)}")
            return None
            
    def get_document(self, doc_id: str) -> Optional[Dict]:
        try:
            results = self.rag.search(f"id:{doc_id}", k=1)
            if results:
                return results[0]["document"]
            return None
        except Exception as e:
            print(f"Error getting document: {str(e)}")
            return None
            
    def delete_document(self, doc_id: str) -> bool:
        try:
            document = self.get_document(doc_id)
            if not document:
                return False
                
            # Delete from object storage
            bucket = os.getenv("DOCUMENT_BUCKET", "reasonflow-documents")
            self.storage.delete_object(bucket, document["storage_path"])
            
            # Note: For simplicity, we're not removing from the FAISS index
            # In a production system, you'd want to rebuild the index
            
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
            
    def search_documents(self, query: str, limit: int = 10) -> List[Dict]:
        try:
            return self.rag.search(query, k=limit)
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return [] 