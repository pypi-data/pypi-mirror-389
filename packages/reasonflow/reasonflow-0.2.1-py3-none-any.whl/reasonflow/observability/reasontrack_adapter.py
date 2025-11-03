"""ReasonTrack adapter for comprehensive tracking."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging
import asyncio
import os
import time
import uuid

from reasonflow.observability.tracking_interface import TrackingInterface
from reasonflow.observability.reasontrack_management_initializer import ManagementInitializer, get_reasontrack_config

# Import from specific modules to avoid circular imports
from reasontrack.core.alert_manager import Alert, AlertManager, AlertSeverity
from reasontrack.core.event_manager import EventManager, EventData, EventType, EventStatus
from reasontrack.core.health_checker import HealthChecker
from reasontrack.core.metrics_collector import MetricsCollector, MetricType
from reasontrack.core.state_manager import StateManager
from reasontrack.storage.metrics_store import MetricStorage
from reasontrack.storage.event_store import EventStorage
from reasontrack.storage.state_store import StateStorage
from reasontrack.utils.config_validator import ConfigValidator, ReasonTrackConfig
from reasontrack.utils.metrics_config import MetricsConfig, LLMConfig, VectorDBConfig, TaskConfig, HardwareType, RuntimeMode
from reasontrack.core.version_manager import VersionManager
logger = logging.getLogger(__name__)

class ReasonTrackAdapter(TrackingInterface):
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ReasonTrack adapter with enhanced functionality."""
        super().__init__()
        
        # Validate configuration
        self.config = config
        
        # Initialize using ManagementInitializer
        self.manager = ManagementInitializer(config=config)
        
        # Get components from manager
        self.metric_storage = self.manager.metric_storage
        self.event_storage = self.manager.event_storage
        self.state_storage = self.manager.state_storage
        self.alert_manager = self.manager.alert_manager
        self.event_manager = self.manager.event_manager
        self.state_manager = self.manager.state_manager
        self.version_manager = self.manager.version_manager
        self.metrics_collector = self.manager.metrics_collector
        self.health_checker = self.manager.health_checker
        
    async def track_workflow(self, workflow_id: str, event_type: str, event_name: str, event_status: str, source: str, data: Dict[str, Any]) -> str:
        """Track workflow with comprehensive metrics and state management.
        
        Args:
            workflow_id: Unique identifier for the workflow (if None, will be auto-generated)
            event_type: Type of workflow event (e.g., started, completed, failed)
            event_name: Name of the workflow event
            event_status: Status of the event
            source: Source of the event
            data: Additional workflow data including metadata and metrics
            
        Returns:
            str: The workflow ID
        """
        try:
            # Generate workflow_id if not provided
            if not workflow_id:
                workflow_id = str(uuid.uuid4())
                
            # Extract metadata if present
            metadata = data.pop("metadata", {})
            
            # Create workflow state
            workflow_state = {
                "id": workflow_id,  # Include ID in state
                "status": event_type,
                "version": data.get("version", "1.0.0"),
                "progress": data.get("progress", 0),
                "total_tasks": data.get("total_tasks", 0),
                "completed_tasks": data.get("completed_tasks", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
                **data
            }
            
            # Save workflow state with metadata
            await self.state_manager.save_state(
                workflow_id=workflow_id,
                state=workflow_state,
                metadata=metadata
            )
            
            # Create event data dictionary
            event_metadata = {
                "workflow_id": workflow_id,
                "workflow_state": workflow_state,
                **data,
                **metadata
            }
            
            # Track workflow event
            await self.event_manager.track_event(
                name=event_name,
                source=source,
                event_type=event_type,
                metadata=event_metadata,
                status=event_status
            )

            # Record workflow metrics if completed
            if event_type == "completed":
                metrics = {
                    "total_duration": float(data.get("duration", 0)),
                    "task_count": float(workflow_state["total_tasks"]),
                    "completed_tasks": float(workflow_state["completed_tasks"]),
                    "success_rate": (float(workflow_state["completed_tasks"]) / float(workflow_state["total_tasks"])) * 100 if workflow_state["total_tasks"] > 0 else 0
                }
                
                await self.metrics_collector.start_tracking(
                    workflow_id=workflow_id,
                    metrics=metrics,
                    tags={
                        "event_type": event_type,
                        "workflow_type": metadata.get("type", "default"),
                        "priority": metadata.get("priority", "medium")
                    }
                )

            return workflow_id  # Return the workflow ID for reference

        except Exception as e:
            logger.error(f"Error tracking workflow: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.ERROR,
                context={"workflow_id": workflow_id, "event_type": event_type}
            )
            raise

    async def track_task(self, task_id: str, workflow_id: str, event_type: str, event_name: str, event_status: str, source: str, data: Dict[str, Any]) -> str:
        """Track task with comprehensive metrics and state management.
        
        Args:
            task_id: Unique identifier for the task (if None, will be auto-generated)
            workflow_id: ID of the parent workflow
            event_type: Type of task event (e.g., started, completed, failed)
            event_name: Name of the task event
            event_status: Status of the event
            source: Source of the event
            data: Additional task data including metrics and state information
            
        Returns:
            str: The task ID
        """
        try:
            # Generate task_id if not provided
            if not task_id:
                task_id = str(uuid.uuid4())
                
            # Create task state data
            task_state = {
                "id": task_id,  # Include ID in state
                "workflow_id": workflow_id,  # Include workflow ID in state
                "status": event_type,
                "name": data.get("name", "unknown_task"),
                "start_time": data.get("start_time", datetime.now(timezone.utc).isoformat()),
                "end_time": data.get("end_time") if event_type == "completed" else None,
                "progress": data.get("progress", 0),
                "current_stage": data.get("current_stage"),
                "stages_completed": data.get("stages_completed", []),
                "stages_remaining": data.get("stages_remaining", []),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **{k: v for k, v in data.items() if k not in ["metrics"]}
            }
            
            # Save task state
            await self.state_manager.save_state(
                workflow_id=workflow_id,
                task_id=task_id,
                state=task_state
            )
            
            # Create event metadata
            event_metadata = {
                "task_id": task_id,
                "workflow_id": workflow_id,
                "task_state": task_state,
                **{k: v for k, v in data.items() if k != "metrics"}
            }
            
            # Track task event
            await self.event_manager.track_event(
                name=event_name,
                source=source,
                event_type=event_type,
                metadata=event_metadata,
                status=event_status
            )
            
            # Handle metrics for completed tasks
            if event_type == "completed" and "metrics" in data:
                task_metrics = data["metrics"]
                if isinstance(task_metrics, dict):
                    for metric_type, metrics_data in task_metrics.items():
                        if isinstance(metrics_data, dict):
                            metrics = {
                                name: float(value) if isinstance(value, (int, float)) else 1.0
                                for name, value in metrics_data.items()
                            }
                            
                            # Add task completion metrics
                            if metric_type == "performance":
                                start_time = datetime.fromisoformat(task_state["start_time"])
                                end_time = datetime.fromisoformat(task_state["end_time"]) if task_state["end_time"] else datetime.now(timezone.utc)
                                metrics.update({
                                    "duration_seconds": (end_time - start_time).total_seconds(),
                                    "stages_completed_count": len(task_state["stages_completed"]),
                                    "progress_percentage": task_state["progress"]
                                })
                            
                            await self.metrics_collector.record_metric(
                                metric_type=MetricType.GAUGE,
                                name=metric_type,
                                value=metrics,
                                tags={
                                    "task_id": task_id,
                                    "workflow_id": workflow_id,
                                    "metric_type": metric_type,
                                    "task_name": task_state["name"],
                                    "task_status": event_type
                                },
                                timestamp=datetime.now(timezone.utc)
                            )
            
            return task_id  # Return the task ID for reference

        except Exception as e:
            logger.error(f"Error tracking task: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.ERROR,
                context={"task_id": task_id, "workflow_id": workflow_id}
            )
            raise

    async def get_task_metrics(self, task_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get task metrics with enhanced error handling."""
        try:
            metrics = await self.metrics_collector.get_task_metrics(task_id=task_id, start_time=start_time, end_time=end_time)
            return {
                "task_id": task_id,
                "metrics": metrics or {}
            }
        except Exception as e:
            logger.error(f"Error getting task metrics: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"task_id": task_id}
            )
            return {
                "task_id": task_id,
                "metrics": {},
                "error": str(e)
            }

    async def get_workflow_metrics(self, workflow_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get comprehensive workflow metrics."""
        try:
            metrics = await self.metrics_collector.get_workflow_metrics(workflow_id=workflow_id, start_time=start_time, end_time=end_time)
            return {
                "workflow_id": workflow_id,
                "metrics": metrics or {}
            }
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"workflow_id": workflow_id}
            )
            return {
                "workflow_id": workflow_id,
                "metrics": {},
                "error": str(e)
            }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status with metrics."""
        try:
            state = await self.state_manager.get_state(entity_id=workflow_id)
            health = await self.health_checker.check_health()
            
            return {
                "workflow_id": workflow_id,
                "status": state.get("status", "unknown") if state else "unknown",
                "health": health,
                "last_update": state.get("timestamp") if state else None
            }
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"workflow_id": workflow_id}
            )
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status."""
        try:
            state = await self.state_manager.get_state(entity_id=task_id)
            return {
                "task_id": task_id,
                "status": state.get("status", "unknown") if state else "unknown",
                "data": state.get("data", {}) if state else {},
                "last_update": state.get("timestamp") if state else None
            }
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"task_id": task_id}
            )
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def check_system_health(self) -> Dict[str, Any]:
        """Check health status of all components."""
        try:
            return await self.health_checker.check_overall_health()
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.ERROR,
                context={"component": "system_health"}
            )
            raise

    async def track_error(self, error: Exception, severity: AlertSeverity, context: Dict[str, Any]) -> None:
        """Track errors with enhanced context."""
        try:
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_name=f"{context.get('component', 'general')}_error",
                message=str(error),
                severity=severity,
                metadata=context
            )
            await self.alert_manager.trigger_alert(alert)
        except Exception as e:
            logger.error(f"Error in error tracking: {str(e)}")

    async def cleanup(self) -> None:
        """Cleanup all resources using the manager."""
        try:
            await self.manager.cleanup()
            logger.info("Successfully cleaned up all resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task event history.
        
        Args:
            task_id: ID of the task to get history for
            
        Returns:
            List of task events with timestamps
        """
        try:
            events = await self.event_manager.get_events(
                entity_id=task_id,
                event_type=EventType.TASK
            )
            return [event.dict() for event in events] if events else []
        except Exception as e:
            logger.error(f"Error getting task history: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"task_id": task_id}
            )
            return []

    async def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get workflow event history.
        
        Args:
            workflow_id: ID of the workflow to get history for
            
        Returns:
            List of workflow events with timestamps
        """
        try:
            events = await self.event_manager.get_events(
                entity_id=workflow_id,
                event_type=EventType.WORKFLOW
            )
            return [event.dict() for event in events] if events else []
        except Exception as e:
            logger.error(f"Error getting workflow history: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.WARNING,
                context={"workflow_id": workflow_id}
            )
            return []

    async def track_system_event(self, event_name: str, metadata: Dict[str, Any], status: EventStatus = EventStatus.COMPLETED) -> str:
        """Track system events like user logins, system updates, etc.
        
        Args:
            event_name: Name of the system event
            metadata: Additional metadata about the event
            status: Status of the event (default: COMPLETED)
            
        Returns:
            str: The generated event ID
            
        Raises:
            Exception: If there's an error storing the event
        """
        try:
            event_id = str(uuid.uuid4())
            event_data = {
                "id": event_id,
                "event_type": EventType.SYSTEM.value,
                "event_name": event_name,
                "status": status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata
            }
            
            await self.manager.event_storage.store_event(event_data)
            
            # Also track as a metric for system events
            await self.metrics_collector.record_metric(
                metric_type=MetricType.COUNTER,
                name="system_events",
                value=1.0,
                tags={
                    "event_type": "system",
                    "event_name": event_name,
                    "status": status.value
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"Successfully tracked system event: {event_name} with ID: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking system event: {str(e)}")
            await self.track_error(
                error=e,
                severity=AlertSeverity.ERROR,
                context={
                    "component": "system_event",
                    "event_name": event_name
                }
            )
            raise