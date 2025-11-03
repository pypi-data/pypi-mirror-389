import logging
from typing import Dict, Optional
import os
import requests
from urllib.parse import urljoin
from reasonchain.memory import Memory, SharedMemory
from reasonflow.observability.tracker import TaskTracker

class APIConnectorAgent:
    def __init__(self, base_url: str, api_key: Optional[str] = None, memory=None, shared_memory=None, task_tracker=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv("API_KEY")
        self.memory = memory or Memory()
        self.shared_memory = shared_memory
        self.task_tracker = task_tracker or TaskTracker()
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def request(self, method: str, endpoint: str, task_id: Optional[str] = None, **kwargs) -> Dict:
        try:
            url = urljoin(f"{self.base_url}/", endpoint.lstrip('/'))
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()

            # Save the response in shared memory
            if self.shared_memory:
                self.shared_memory.store("last_api_response", response.json())

            # Track success
            if task_id:
                self.task_tracker.log(task_id, endpoint, "success")

            return {
                "status": "success",
                "status_code": response.status_code,
                "data": response.json() if response.content else None
            }
        except requests.exceptions.RequestException as e:
            # Log the error in memory and tracker
            if self.memory:
                self.memory.store_short_term({"error": str(e)})
            if task_id:
                self.task_tracker.log(task_id, endpoint, "failed")
            return {
                "status": "error",
                "message": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }


            
    def get(self, endpoint: str, **kwargs) -> Dict:
        return self.request("GET", endpoint, **kwargs)
        
    def post(self, endpoint: str, **kwargs) -> Dict:
        return self.request("POST", endpoint, **kwargs)
        
    def put(self, endpoint: str, **kwargs) -> Dict:
        return self.request("PUT", endpoint, **kwargs)
        
    def delete(self, endpoint: str, **kwargs) -> Dict:
        return self.request("DELETE", endpoint, **kwargs) 