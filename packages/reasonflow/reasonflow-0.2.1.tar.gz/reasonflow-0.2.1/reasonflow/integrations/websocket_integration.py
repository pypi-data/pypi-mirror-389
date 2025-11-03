from typing import Optional, Dict, Any
import asyncio
import json
import logging
from fastapi import WebSocket
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketNotifier:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
        
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
            
    async def notify_task_completion(self, client_id: str, task_data: Dict[str, Any]):
        """Send task completion notification to a specific client"""
        if client_id in self.active_connections:
            try:
                message = {
                    "type": "task_completion",
                    "data": {
                        "task_id": task_data.get("task_id"),
                        "task_type": task_data.get("task_type"),
                        "status": task_data.get("status"),
                        "timestamp": datetime.now().isoformat(),
                        "next_task": task_data.get("next_task"),
                        "result_summary": task_data.get("result_summary")
                    }
                }
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"Sent task completion notification to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending notification to client {client_id}: {str(e)}")
                
    async def notify_workflow_completion(self, client_id: str, workflow_data: Dict[str, Any]):
        """Send workflow completion notification to a specific client"""
        if client_id in self.active_connections:
            try:
                message = {
                    "type": "workflow_completion",
                    "data": {
                        "workflow_id": workflow_data.get("workflow_id"),
                        "status": workflow_data.get("status"),
                        "timestamp": datetime.now().isoformat(),
                        "summary": workflow_data.get("summary")
                    }
                }
                await self.active_connections[client_id].send_json(message)
                logger.debug(f"Sent workflow completion notification to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending workflow notification to client {client_id}: {str(e)}")

# Global instance for easy access
notifier = WebSocketNotifier() 