"""Basic tracking implementation."""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
import logging
import uuid
import asyncio
from pydantic import BaseModel, Field, validator
from enum import Enum
from reasonflow.observability.tracking_interface import TrackingInterface
from reasonflow.observability.tracker import TaskTracker
from reasonflow.orchestrator.state_manager import StateManager
from reasonchain.memory import SharedMemory

logger = logging.getLogger(__name__)

class BasicMetricType(str, Enum):
    """Metric types supported by basic tracker."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TASK_DURATION = "task_duration"
    WORKFLOW_DURATION = "workflow_duration"

class BasicEventType(str, Enum):
    """Event types supported by basic tracker."""
    TASK = "task"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    RESOURCE = "resource"
    DATA = "data"
    INTEGRATION = "integration"

class BasicEventStatus(str, Enum):
    """Event statuses supported by basic tracker."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"
class BasicHardwareType(str, Enum):
    """Hardware types for task execution."""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    HYBRID = "hybrid"

class BasicRuntimeMode(str, Enum):
    """Runtime modes for task execution."""
    SYNC = "sync"
    ASYNC = "async"
    BATCH = "batch"

class BasicLLMConfig(BaseModel):
    """LLM metrics configuration."""
    track_tokens: bool = True
    track_latency: bool = True
    track_cost: bool = True
    track_cache: bool = True
    track_memory: bool = True

class BasicVectorDBConfig(BaseModel):
    """VectorDB metrics configuration."""
    track_latency: bool = True
    track_throughput: bool = True
    track_cache: bool = True
    track_memory: bool = True

class BasicTaskConfig(BaseModel):
    """Task metrics configuration."""
    enabled: bool = True
    collection_interval: int = 60
    retention_days: int = 7
    track_memory: bool = True
    track_cpu: bool = True
    track_gpu: bool = False
    hardware_type: BasicHardwareType = BasicHardwareType.CPU
    runtime_mode: BasicRuntimeMode = BasicRuntimeMode.ASYNC

class BasicWorkflowConfig(BaseModel):
    """Workflow metrics configuration."""
    enabled: bool = True
    collection_interval: int = 300
    retention_days: int = 30

class BasicMetricsConfig(BaseModel):
    """Complete metrics configuration."""
    task: BasicTaskConfig = Field(default_factory=BasicTaskConfig)
    workflow: BasicWorkflowConfig = Field(default_factory=BasicWorkflowConfig)
    llm: BasicLLMConfig = Field(default_factory=BasicLLMConfig)
    vectordb: BasicVectorDBConfig = Field(default_factory=BasicVectorDBConfig)

class MetricValue(BaseModel):
    """Model for a single metric value."""
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: str
    metric_type: BasicMetricType
    name: str

class TaskMetric(BaseModel):
    """Model for task-specific metrics."""
    task_id: str
    workflow_id: str
    metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    status: str = "processing"

class WorkflowMetric(BaseModel):
    """Model for workflow-level metrics."""
    workflow_id: str
    task_count: int = 0
    success_count: int = 0
    total_duration: float = 0
    start_time: str
    end_time: Optional[str] = None
    status: str = "processing"
    tasks: Dict[str, TaskMetric] = Field(default_factory=dict)

class Event(BaseModel):
    """Model for tracking events."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: BasicEventType
    event_name: str
    status: BasicEventStatus
    source: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: Dict[str, Any] = Field(default_factory=dict)

class BasicMetricsCollector:
    """Simple metrics collector implementation using Pydantic models."""
    
    def __init__(self):
        self.metrics: Dict[str, List[MetricValue]] = {}
        self.start_times: Dict[str, datetime] = {}
        self.workflow_metrics: Dict[str, WorkflowMetric] = {}
        self.task_metrics: Dict[str, TaskMetric] = {}
        self.system_metrics: Dict[str, MetricValue] = {}
    
    async def start_tracking(self, task_id: str, workflow_id: str) -> None:
        """Start tracking a task."""
        current_time = datetime.now(timezone.utc)
        self.start_times[task_id] = current_time
        
        if workflow_id not in self.workflow_metrics:
            self.workflow_metrics[workflow_id] = WorkflowMetric(
                workflow_id=workflow_id,
                start_time=current_time.isoformat()
            )
            
        workflow_metric = self.workflow_metrics[workflow_id]
        workflow_metric.task_count += 1
        
        task_metric = TaskMetric(
            task_id=task_id,
            workflow_id=workflow_id,
            start_time=current_time.isoformat(),
            status="processing"
        )
        workflow_metric.tasks[task_id] = task_metric
        self.task_metrics[task_id] = task_metric
    
    async def stop_tracking(self, task_id: str, workflow_id: str, status: str = "completed") -> Dict[str, Any]:
        """Stop tracking a task and return metrics."""
        metrics = {}
        current_time = datetime.now(timezone.utc)
        
        if task_id in self.start_times:
            duration = (current_time - self.start_times[task_id]).total_seconds()
            del self.start_times[task_id]
            metrics["duration"] = duration
            
            if workflow_id in self.workflow_metrics:
                workflow_metric = self.workflow_metrics[workflow_id]
                if status == "completed":
                    workflow_metric.success_count += 1
                workflow_metric.total_duration += duration
                
                if task_id in workflow_metric.tasks:
                    task_metric = workflow_metric.tasks[task_id]
                    task_metric.end_time = current_time.isoformat()
                    task_metric.duration = duration
                    task_metric.status = status
                    
                if task_id in self.task_metrics:
                    self.task_metrics[task_id].end_time = current_time.isoformat()
                    self.task_metrics[task_id].duration = duration
                    self.task_metrics[task_id].status = status
                    
        return metrics

    async def record_metric(self, value: float, name: str, metric_type: Union[str, BasicMetricType], labels: Optional[Dict[str, str]] = None, tags: Optional[Dict[str, str]] = None, timestamp: Optional[datetime] = None) -> None:
        """Record a metric with labels/tags."""
        # Convert string metric_type to enum if needed
        if isinstance(metric_type, str):
            try:
                metric_type = BasicMetricType(metric_type.lower())
            except ValueError:
                # Handle invalid metric type
                logger.error(f"Invalid metric type: {metric_type}")
                return
        elif isinstance(metric_type, BasicMetricType):
            # If it's already a MetricType enum, use it directly
            pass
        else:
            # Handle invalid type
            logger.error(f"Invalid metric type: {metric_type}")
            return
            
        # Use tags if provided, otherwise use labels, or empty dict as fallback
        metric_labels = tags or labels or {}
        current_time = timestamp or datetime.now(timezone.utc)
        
        try:
            metric_value = MetricValue(
                value=value,
                labels=metric_labels,
                timestamp=current_time.isoformat(),
                metric_type=metric_type.value,  # Use the string value of the enum
                name=name
            )
            
            metric_key = f"{metric_type.value}_{name}"
            if metric_key not in self.metrics:
                self.metrics[metric_key] = []
            
            self.metrics[metric_key].append(metric_value)
            
            # Store task-specific metrics
            if "task_id" in metric_labels:
                task_id = metric_labels["task_id"]
                if task_id in self.task_metrics:
                    task_metric = self.task_metrics[task_id]
                    if metric_type.value not in task_metric.metrics:
                        task_metric.metrics[metric_type.value] = {}
                    task_metric.metrics[metric_type.value][name] = value
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")

    async def record_workflow_metrics(self, workflow_id: str, metrics: Dict[str, Any]) -> None:
        """Record workflow-level metrics."""
        if workflow_id in self.workflow_metrics:
            workflow_metric = self.workflow_metrics[workflow_id]
            for key, value in metrics.items():
                if hasattr(workflow_metric, key):
                    setattr(workflow_metric, key, value)

    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get all metrics for a workflow."""
        if workflow_id in self.workflow_metrics:
            return self.workflow_metrics[workflow_id].dict()
        return {}

    async def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get all metrics for a task."""
        if task_id in self.task_metrics:
            return self.task_metrics[task_id].dict()
        return {}

    async def get_metrics(self, names: List[str], start_time: datetime, end_time: datetime, tags: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics by names and time range."""
        result = {}
        for name in names:
            result[name] = []
            for metric_key, metrics in self.metrics.items():
                if name in metric_key:
                    filtered_metrics = [
                        m.dict() for m in metrics 
                        if datetime.fromisoformat(m.timestamp) >= start_time 
                        and datetime.fromisoformat(m.timestamp) <= end_time
                        and all(m.labels.get(k) == v for k, v in tags.items())
                    ]
                    result[name].extend(filtered_metrics)
        return result

    async def cleanup(self) -> None:
        """Cleanup metrics data."""
        self.metrics.clear()
        self.start_times.clear()
        self.workflow_metrics.clear()
        self.task_metrics.clear()
        self.system_metrics.clear()

class BasicTracker(TrackingInterface):
    """Basic tracker implementation with enhanced functionality."""
    
    def __init__(self, metrics_collector: Optional[BasicMetricsCollector] = None):
        """Initialize basic tracker with optional metrics collector."""
        self.shared_memory = SharedMemory()
        self.task_tracker = TaskTracker(shared_memory=self.shared_memory)
        self.state_manager = StateManager()
        self.metrics_collector = metrics_collector or BasicMetricsCollector()
        self.workflow_states = {}
        self.task_states = {}
        self.task_history = {}
        self.workflow_history = {}
        self.system_events = []
    
    async def track_workflow(self, workflow_id: str, event_type: str, event_name: str, event_status: str, source: str, data: Dict[str, Any]) -> str:
        """Track workflow with enhanced metrics and state management."""
        try:
            if not workflow_id:
                workflow_id = str(uuid.uuid4())
                
            logger.info(f"Tracking workflow {workflow_id}: {event_type}")
            
            # Update workflow state
            state = self.workflow_states.get(workflow_id, {})
            state.update({
                "workflow_id": workflow_id,
                "status": event_status,
                "event_type": event_type,
                "event_name": event_name,
                "source": source,
                "data": data,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
            self.workflow_states[workflow_id] = state
            
            # Save state to state manager
            self.state_manager.save_state(workflow_id, state)
            
            # Add to workflow history
            if workflow_id not in self.workflow_history:
                self.workflow_history[workflow_id] = []
            self.workflow_history[workflow_id].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "event_name": event_name,
                "status": event_status,
                "data": data
            })
            
            if event_status == "completed":
                metrics = {
                    "total_duration": data.get("duration", 0),
                    "task_count": data.get("task_count", 0),
                    "success_count": len([t for t in data.get("task_ids", [])]),
                    "end_time": datetime.now(timezone.utc).isoformat()
                }
                await self.metrics_collector.record_workflow_metrics(workflow_id, metrics)
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error tracking workflow: {str(e)}")
            raise

    async def track_task(self, task_id: str, workflow_id: str, event_type: str, event_name: str, event_status: str, source: str, data: Dict[str, Any]) -> str:
        """Track task with enhanced metrics and state management."""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())
                
            logger.info(f"Tracking task {task_id} in workflow {workflow_id}: {event_type}")
            
            # Update task state
            task_state = {
                "task_id": task_id,
                "workflow_id": workflow_id,
                "status": event_status,
                "event_type": event_type,
                "event_name": event_name,
                "source": source,
                "data": data,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            self.task_states[task_id] = task_state
            
            # Add to task history
            if task_id not in self.task_history:
                self.task_history[task_id] = []
            self.task_history[task_id].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": event_type,
                "event_name": event_name,
                "status": event_status,
                "data": data
            })
            
            # Track in task tracker
            self.task_tracker.log(task_id, data.get("name", ""), event_status)
            
            if event_status == "processing":
                await self.metrics_collector.start_tracking(task_id, workflow_id)
            elif event_status in ["completed", "failed"]:
                metrics = await self.metrics_collector.stop_tracking(task_id, workflow_id, event_status)
                
                # Record task-specific metrics
                if metrics:
                    await self.metrics_collector.record_metric(
                        value=metrics.get("duration", 0.0),
                        name="duration",
                        metric_type="task_duration",
                        labels={
                            "task_id": task_id,
                            "workflow_id": workflow_id,
                            "status": event_status
                        }
                    )
                
                # Record additional task metrics if provided
                if "metrics" in data:
                    task_metrics = data["metrics"]
                    if isinstance(task_metrics, dict):
                        for metric_type, metrics_data in task_metrics.items():
                            if isinstance(metrics_data, dict):
                                for name, value in metrics_data.items():
                                    await self.metrics_collector.record_metric(
                                        value=float(value) if isinstance(value, (int, float)) else 1.0,
                                        name=name,
                                        metric_type=metric_type,
                                        labels={
                                            "task_id": task_id,
                                            "workflow_id": workflow_id,
                                            "metric_type": metric_type
                                        }
                                    )
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error tracking task: {str(e)}")
            raise

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow status."""
        try:
            status = self.workflow_states.get(workflow_id, {})
            metrics = await self.metrics_collector.get_workflow_metrics(workflow_id)
            tasks = {
                task_id: task_state 
                for task_id, task_state in self.task_states.items() 
                if task_state.get("workflow_id") == workflow_id
            }
            return {
                "status": status,
                "metrics": metrics,
                "tasks": tasks,
                "health": await self.check_system_health()
            }
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {}

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status."""
        try:
            task_state = self.task_states.get(task_id, {})
            task_metrics = await self.metrics_collector.get_task_metrics(task_id)
            return {
                "status": task_state,
                "metrics": task_metrics,
                "history": self.task_history.get(task_id, [])
            }
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return {}

    async def get_workflow_metrics(self, workflow_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive workflow metrics."""
        try:
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            if start_time is None:
                start_time = end_time - timedelta(hours=1)
                
            metrics = await self.metrics_collector.get_workflow_metrics(workflow_id)
            return {
                "workflow_id": workflow_id,
                "metrics": metrics,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}")
            return {}

    async def get_task_metrics(self, task_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive task metrics."""
        try:
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            if start_time is None:
                start_time = end_time - timedelta(hours=1)
                
            metrics = await self.metrics_collector.get_task_metrics(task_id)
            return {
                "task_id": task_id,
                "metrics": metrics,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting task metrics: {str(e)}")
            return {}

    async def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Get task event history."""
        try:
            return self.task_history.get(task_id, [])
        except Exception as e:
            logger.error(f"Error getting task history: {str(e)}")
            return []

    async def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get workflow event history."""
        try:
            return self.workflow_history.get(workflow_id, [])
        except Exception as e:
            logger.error(f"Error getting workflow history: {str(e)}")
            return []

    async def track_system_event(self, event_name: str, metadata: Dict[str, Any], status: str = "completed") -> str:
        """Track system events like user logins, system updates, etc."""
        try:
            event_id = str(uuid.uuid4())
            event_data = {
                "id": event_id,
                "event_name": event_name,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata
            }
            
            self.system_events.append(event_data)
            
            # Record as a metric
            await self.metrics_collector.record_metric(
                value=1.0,
                name="system_events",
                metric_type="counter",
                labels={
                    "event_name": event_name,
                    "status": status
                }
            )
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error tracking system event: {str(e)}")
            raise

    async def check_system_health(self) -> Dict[str, Any]:
        """Check health status of all components."""
        try:
            current_time = datetime.now(timezone.utc)
            components = {
                "metrics_collector": len(self.metrics_collector.metrics) > 0,
                "task_tracker": True,  # Basic component always available
                "state_manager": True,  # Basic component always available
                "memory": self.shared_memory is not None
            }
            
            # Check recent activity
            recent_events = [
                event for event in self.system_events
                if (current_time - datetime.fromisoformat(event["timestamp"])).total_seconds() < 3600
            ]
            
            return {
                "status": "healthy" if all(components.values()) else "degraded",
                "components": components,
                "last_check": current_time.isoformat(),
                "recent_activity": len(recent_events)
            }
        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        try:
            await self.metrics_collector.cleanup()
            self.workflow_states.clear()
            self.task_states.clear()
            self.task_history.clear()
            self.workflow_history.clear()
            self.system_events.clear()
            logger.info("Successfully cleaned up all resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise 