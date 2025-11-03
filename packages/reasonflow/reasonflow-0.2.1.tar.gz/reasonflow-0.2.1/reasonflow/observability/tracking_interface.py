from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class TrackingInterface(ABC):
    """Abstract base class defining the tracking interface for ReasonFlow.
    
    This interface provides a standardized way to track workflows, tasks, and metrics
    across different tracking implementations (basic and advanced).
    """
    
    @abstractmethod
    async def track_workflow(self, workflow_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Track workflow events with comprehensive data.

        Args:
            workflow_id: Unique identifier for the workflow
            event_type: Type of event (started, completed, failed, etc.)
            data: Additional data about the workflow event
        """
        pass
    
    @abstractmethod
    async def track_task(self, task_id: str, workflow_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Track task events with detailed metrics.

        Args:
            task_id: Unique identifier for the task
            workflow_id: ID of the workflow this task belongs to
            event_type: Type of event (started, completed, failed, etc.)
            data: Additional data about the task event including metrics
        """
        pass
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow status including metrics.

        Args:
            workflow_id: ID of the workflow to get status for

        Returns:
            Dict containing workflow status, metrics, and event history
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status including metrics.

        Args:
            task_id: ID of the task to get status for

        Returns:
            Dict containing task status, metrics, and event history
        """
        pass

    @abstractmethod
    async def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get comprehensive task metrics.

        Args:
            task_id: ID of the task to get metrics for

        Returns:
            Dict containing all tracked metrics for the task
        """
        pass
    
    @abstractmethod
    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get aggregated workflow metrics.

        Args:
            workflow_id: ID of the workflow to get metrics for

        Returns:
            Dict containing aggregated metrics for the entire workflow
        """
        pass

    @abstractmethod
    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get complete task event history.

        Args:
            task_id: ID of the task to get history for

        Returns:
            List of task events in chronological order
        """
        pass

    @abstractmethod
    async def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get complete workflow event history.

        Args:
            workflow_id: ID of the workflow to get history for

        Returns:
            List of workflow events in chronological order
        """
        pass 

    @abstractmethod
    async def check_system_health(self) -> Dict[str, Any]:
        """Check health status of all tracking components.

        Returns:
            Dict containing health status of all components
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the tracker.
        
        This method should be called when the tracker is no longer needed
        to ensure proper resource cleanup.
        """
        pass

   