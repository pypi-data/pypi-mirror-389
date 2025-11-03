from typing import Dict, Any, Optional
import os
import firebase_admin
from firebase_admin import credentials, db, auth, storage

class FirebaseIntegration:
    def __init__(self, credentials_path: Optional[str] = None):
        try:
            cred_path = credentials_path or os.getenv("FIREBASE_CREDENTIALS")
            if not cred_path:
                raise ValueError("Firebase credentials not found")
                
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv("FIREBASE_DATABASE_URL"),
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
            })
            
            self.db = db
            self.auth = auth
            self.bucket = storage.bucket()
            
        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            
    def authenticate_user(self, email: str, password: str) -> Dict:
        try:
            user = self.auth.get_user_by_email(email)
            return {
                "status": "success",
                "user_id": user.uid,
                "email": user.email
            }
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    def save_workflow_state(self, workflow_id: str, state: Dict) -> bool:
        try:
            ref = self.db.reference(f'workflows/{workflow_id}')
            ref.set(state)
            return True
        except Exception as e:
            print(f"Error saving workflow state: {str(e)}")
            return False
            
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict]:
        try:
            ref = self.db.reference(f'workflows/{workflow_id}')
            return ref.get()
        except Exception as e:
            print(f"Error getting workflow state: {str(e)}")
            return None
            
    def upload_file(self, file_path: str, destination: str) -> Optional[str]:
        try:
            blob = self.bucket.blob(destination)
            blob.upload_from_filename(file_path)
            return blob.public_url
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return None
            
    def download_file(self, source: str, destination: str) -> bool:
        try:
            blob = self.bucket.blob(source)
            blob.download_to_filename(destination)
            return True
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False 