import heapq
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
from ..tasks.task import Task
from ..tasks.task_types import TASK_TYPES
from ..observability.tracker import TaskTracker
from reasonchain.memory import SharedMemory
from ..observability.basic_tracker import BasicMetricsCollector, BasicMetricType, BasicEventType, BasicEventStatus
from reasontrack.storage.event_store import EventType, EventStatus
from reasontrack.utils.metrics_types import MetricType
import asyncio
logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self, shared_memory: Optional[SharedMemory] = None, tracker_type: str = "basic", metrics_collector: Optional[BasicMetricsCollector] = None):
        self.tasks: Dict[str, Task] = {}
        self.task_queue = []  # Priority queue using heapq
        self.task_status = {}  # Dictionary to track task statuses
        self.waiting_tasks = []  # Tasks waiting for dependencies
        self.completed_tasks = []  # List of completed task names
        self.shared_memory = shared_memory or SharedMemory()
        self.tracker = TaskTracker(shared_memory=self.shared_memory)
        self.task_executors = {}  # Dictionary to store task type executors
        self.tracker_type = tracker_type
        self.metrics_collector = metrics_collector or BasicMetricsCollector()
        self.event_type = BasicEventType if tracker_type == "basic" else EventType
        self.event_status = BasicEventStatus if tracker_type == "basic" else EventStatus
        self.metric_type = BasicMetricType if tracker_type == "basic" else MetricType
        
        # Initialize all available task types
        self.initialize_task_types()

    def register_task_type(self, task_type: str, executor_class: Any) -> None:
        """Register a new task type executor"""
        self.task_executors[task_type] = executor_class()

    def initialize_task_types(self):
        """Initialize all available task types"""
        for task_type, executor_class in TASK_TYPES.items():
            if executor_class is not None:
                self.register_task_type(task_type, executor_class)

    async def execute_task(self, task_id: str, task_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using its registered executor with tracking and metrics."""
        if task_type not in self.task_executors:
            raise ValueError(f"Unknown task type: {task_type}")
            
        start_time = datetime.now(timezone.utc)
        common_tags = {"task_id": task_id, "task_type": task_type}
        
        try:
            logger.info(f"Executing task {task_id} of type {task_type}")
            
            # Track task start
            await self.track_task_event(
                task_id=task_id,
                event_type=self.event_type.TASK,
                event_name=f"{task_type.title()} Task",
                event_status=self.event_status.PROCESSING,
                data={
                    "task_type": task_type,
                    "start_time": start_time.isoformat(),
                    "config": config,
                    "current_stage": "initialization"
                }
            )
            
            # Execute task
            executor = self.task_executors[task_type]
            if asyncio.iscoroutinefunction(executor.execute):
                result = await executor.execute(config)
            else:
                result = executor.execute(config)
            
            # Calculate duration
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Track task completion
            await self.track_task_event(
                task_id=task_id,
                event_type=self.event_type.TASK,
                event_name=f"{task_type.title()} Task",
                event_status=self.event_status.COMPLETED,
                data={
                    "task_type": task_type,
                    "duration": duration,
                    "end_time": end_time.isoformat(),
                    "result": result
                }
            )
            
            # Record task metrics
            await self.record_task_metrics(
                task_id=task_id,
                task_type=task_type,
                duration=duration,
                result=result,
                tags=common_tags
            )
            
            self.update_task_status(task_id, "completed")
            return result
            
        except Exception as e:
            error_time = datetime.now(timezone.utc)
            error_duration = (error_time - start_time).total_seconds()
            
            # Track task failure
            await self.track_task_event(
                task_id=task_id,
                event_type=self.event_type.TASK,
                event_name=f"{task_type.title()} Task",
                event_status=self.event_status.FAILED,
                data={
                    "task_type": task_type,
                    "error": str(e),
                    "duration": error_duration,
                    "end_time": error_time.isoformat()
                }
            )
            
            # Record failure metrics
            await self.metrics_collector.record_metric(
                metric_type=self.metric_type.COUNTER,
                name="task_failure",
                value=1.0,
                tags={**common_tags, "error": str(e)},
                timestamp=error_time
            )
            
            self.update_task_status(task_id, "failed")
            return {"error": str(e)}

    async def track_task_event(self, task_id: str, event_type: BasicEventType, event_name: str, event_status: BasicEventStatus, data: Dict[str, Any]) -> None:
        """Track task events with metrics."""
        try:
            if self.metrics_collector:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name=f"task_{event_status.value}",
                    value=1.0,
                    tags={
                        "task_id": task_id,
                        "event_type": event_type.value,
                        "event_name": event_name
                    }
                )
        except Exception as e:
            logger.error(f"Error recording task event metric: {str(e)}")

    async def record_task_metrics(self, task_id: str, task_type: str, duration: float, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record comprehensive task metrics."""
        try:
            if not self.metrics_collector:
                return
                
            # Record duration
            await self.metrics_collector.record_metric(
                metric_type=self.metric_type.GAUGE,
                name="task_duration",
                value=duration,
                tags=tags
            )
            
            # Record success
            await self.metrics_collector.record_metric(
                metric_type=self.metric_type.COUNTER,
                name="task_success",
                value=1.0,
                tags=tags
            )
            
            # Record task-specific metrics
            if task_type == "llm":
                await self._record_llm_metrics(task_id, result, tags)
            elif task_type == "data_retrieval":
                await self._record_data_retrieval_metrics(task_id, result, tags)
            elif task_type == "data_ingestion":
                await self._record_data_ingestion_metrics(task_id, result, tags)
            elif task_type == "browser":
                await self._record_browser_metrics(task_id, result, tags)
            elif task_type == "shell":
                await self._record_shell_metrics(task_id, result, tags)
            elif task_type == "python":
                await self._record_python_metrics(task_id, result, tags)
            elif task_type == "filesystem":
                await self._record_filesystem_metrics(task_id, result, tags)
                
        except Exception as e:
            logger.error(f"Error recording task metrics: {str(e)}")

    async def _record_llm_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record LLM-specific metrics."""
        try:
            # Handle case where result might not be a dictionary
            if not isinstance(result, dict):
                logger.warning(f"LLM result is not a dictionary: {type(result)}")
                return
                
            llm_output = result.get("output", {})
            if isinstance(llm_output, dict):
                llm_metadata = llm_output.get("metadata", {})
            else:
                llm_metadata = {}
                
            usage = llm_metadata.get("usage", {}) if isinstance(llm_metadata, dict) else {}
            
            metrics_to_record = {
                "llm_output_tokens": usage.get("completion_tokens", 0),
                "llm_input_tokens": usage.get("prompt_tokens", 0),
                "llm_memory_used": usage.get("memory_used", 0),
                "llm_cost": usage.get("total_cost", 0)
            }
            
            for name, value in metrics_to_record.items():
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name=name,
                    value=float(value),
                    tags=tags
                )
                
        except Exception as e:
            logger.error(f"Error recording LLM metrics: {str(e)}")

    async def _record_data_retrieval_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record data retrieval specific metrics."""
        try:
            metadata = result.get("metadata", {})
            summary = result.get("summary", {})
            
            metrics_to_record = {
                "vectordb_total_results": float(summary.get("total_results", 0)),
                "vectordb_avg_score": float(summary.get("avg_score", 0.0)),
                "vectordb_latency": float(summary.get("latency", 0.0)),
                "vectordb_cost": float(metadata.get("cost", 0.0))
            }
            
            for name, value in metrics_to_record.items():
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.GAUGE,
                    name=name,
                    value=value,
                    tags=tags
                )
                
        except Exception as e:
            logger.error(f"Error recording data retrieval metrics: {str(e)}")

    async def _record_data_ingestion_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record data ingestion specific metrics."""
        pass

    async def _record_browser_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record browser specific metrics."""
        pass

    async def _record_shell_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record shell specific metrics."""
        pass

    async def _record_python_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record python specific metrics."""
        pass

    async def _record_filesystem_metrics(self, task_id: str, result: Dict[str, Any], tags: Dict[str, str]) -> None:
        """Record filesystem specific metrics."""
        pass

    def is_empty(self) -> bool:
        """Check if there are no more tasks to process."""
        return len(self.tasks) == 0 or all(
            task.status in ["completed", "failed"] for task in self.tasks.values()
        )

    def add_task(self, task_dict: Dict) -> None:
        """Add a task to the manager."""
        try:
            task = Task(
                id=task_dict["id"],
                name=task_dict["name"],
                priority=task_dict.get("priority", 1),
                dependencies=task_dict.get("dependencies", []),
                status=task_dict.get("status", "pending"),
                metadata=task_dict.get("metadata", {})
            )
            self.tasks[task.id] = task
            self.task_status[task.id] = task.status
            if task.is_ready(self.completed_tasks):
                heapq.heappush(self.task_queue, (-task.priority, task))
            else:
                self.waiting_tasks.append(task)
        except Exception as e:
            logger.error(f"Error adding task: {str(e)}")

    def get_next_task(self) -> Optional[Dict]:
        """Get the next task to execute."""
        self.resolve_dependencies()
        while self.task_queue:
            _, task = heapq.heappop(self.task_queue)
            if task.id in self.tasks and self.tasks[task.id].status == "pending":
                return {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "priority": task.priority
                }
        return None

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status."""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            self.task_status[task_id] = status
            if status == "completed":
                self.completed_tasks.append(self.tasks[task_id].name)
            self.tracker.log(task_id, self.tasks[task_id].name, status)

    async def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get comprehensive task metrics."""
        try:
            if not self.metrics_collector:
                return {}
            return await self.metrics_collector.get_task_metrics(task_id)
        except Exception as e:
            logger.error(f"Error getting task metrics: {str(e)}")
            return {}

    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if self.metrics_collector:
                await self.metrics_collector.cleanup()
            logger.info("Successfully cleaned up task manager resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def resolve_dependencies(self):
        """Check waiting tasks and move ready tasks to the queue."""
        ready_tasks = [
            task for task in self.waiting_tasks if task.is_ready(self.completed_tasks)
        ]
        for task in ready_tasks:
            heapq.heappush(self.task_queue, (-task.priority, task))
            self.waiting_tasks.remove(task)

    def retry_failed_tasks(self):
        """Re-add failed tasks to the queue."""
        for task_id, status in list(self.task_status.items()):
            if status == "failed":
                task = self.tasks.get(task_id)
                if task:
                    task.status = "pending"  # Reset status
                    heapq.heappush(self.task_queue, (-task.priority, task))
                    print(f"Retrying task: {task}")
                    self.tracker.log(task.id, task.name, "pending")

    def list_all_tasks(self) -> List[Task]:
        """List all tasks."""
        return [task for _, task in self.task_queue]

    def validate_dependencies(self, workflow_config: Dict) -> bool:
        """Validate dependencies to ensure no circular or missing dependencies."""
        try:
            dependency_map = {dep["to"]: dep["from"] for dep in workflow_config["dependencies"]}
            visited = set()

            def check_cycle(task_id, stack):
                if task_id in stack:
                    raise ValueError(f"Circular dependency detected: {stack}")
                if task_id not in visited:
                    visited.add(task_id)
                    stack.append(task_id)
                    if task_id in dependency_map:
                        check_cycle(dependency_map[task_id], stack)
                    stack.pop()

            for task_id in workflow_config["tasks"]:
                check_cycle(task_id, [])
            return True
        except Exception as e:
            print(f"Dependency validation failed: {e}")
            return False

    def prioritize_and_validate(self):
        """Validate and prioritize tasks based on dependencies and priority."""
        self.resolve_dependencies()
        # Re-prioritize tasks in the queue
        self.task_queue = sorted(self.task_queue, key=lambda x: (-x[1].priority, x[1].id))
        heapq.heapify(self.task_queue)

    def list_completed_tasks(self) -> List[str]:
        """List all completed task names."""
        return self.completed_tasks

