from typing import List, Dict, Any, Optional
import uuid

class Task:
    def __init__(
        self,
        name: str,
        id: Optional[str] = None,
        priority: int = 1,
        dependencies: Optional[List[str]] = None,
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = status
        self.metadata = metadata or {}

    def is_ready(self, completed_tasks: List[str]) -> bool:
        """Check if all dependencies are completed."""
        return all(dep in completed_tasks for dep in self.dependencies)

    def __lt__(self, other):
        """Compare tasks based on priority for heapq."""
        return self.priority > other.priority

    def __str__(self):
        return f"Task(id={self.id}, name={self.name}, priority={self.priority}, status={self.status})"
