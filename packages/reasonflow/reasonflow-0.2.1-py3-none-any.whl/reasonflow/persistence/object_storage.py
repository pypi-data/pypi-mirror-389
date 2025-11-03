from typing import Dict, Optional, BinaryIO
import os
import boto3
from botocore.exceptions import ClientError
import minio

class ObjectStorage:
    def __init__(self, provider: str = "s3"):
        self.provider = provider
        
        if provider == "s3":
            self.client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        elif provider == "minio":
            self.client = minio.Minio(
                os.getenv("MINIO_ENDPOINT", "localhost:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY"),
                secret_key=os.getenv("MINIO_SECRET_KEY"),
                secure=False
            )
            
    def upload_file(self, file_path: str, bucket: str, object_name: Optional[str] = None) -> bool:
        try:
            if not object_name:
                object_name = os.path.basename(file_path)
                
            if self.provider == "s3":
                self.client.upload_file(file_path, bucket, object_name)
            else:
                self.client.fput_object(bucket, object_name, file_path)
                
            return True
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return False
            
    def download_file(self, bucket: str, object_name: str, file_path: str) -> bool:
        try:
            if self.provider == "s3":
                self.client.download_file(bucket, object_name, file_path)
            else:
                self.client.fget_object(bucket, object_name, file_path)
                
            return True
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return False
            
    def list_objects(self, bucket: str, prefix: str = "") -> list:
        try:
            if self.provider == "s3":
                response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                return [obj['Key'] for obj in response.get('Contents', [])]
            else:
                objects = self.client.list_objects(bucket, prefix=prefix)
                return [obj.object_name for obj in objects]
                
        except Exception as e:
            print(f"Error listing objects: {str(e)}")
            return []
            
    def delete_object(self, bucket: str, object_name: str) -> bool:
        try:
            if self.provider == "s3":
                self.client.delete_object(Bucket=bucket, Key=object_name)
            else:
                self.client.remove_object(bucket, object_name)
                
            return True
        except Exception as e:
            print(f"Error deleting object: {str(e)}")
            return False 