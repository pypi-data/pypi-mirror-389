from typing import Dict, Any, List, Optional
import logging
import networkx as nx
from datetime import datetime, timezone, timedelta
import asyncio
import re

from reasonflow.observability import TrackerFactory
from reasonflow.integrations.websocket_integration import notifier

from reasonchain.memory import SharedMemory
from reasonflow.agents.custom_agent_builder import CustomAgentBuilder
from reasontrack.storage.event_store import EventType, EventStatus
from reasontrack.utils.metrics_types import MetricType
from reasonflow.observability.basic_tracker import BasicMetricType, BasicEventType, BasicEventStatus
logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Workflow execution engine with comprehensive tracking support."""

    def __init__(self, 
                 task_manager=None,
                 tracker_type: str = "reasontrack",
                 tracker=None,
                 metrics_collector=None,
                 metrics_config=None,
                 state_storage=None,
                 metrics_storage=None,
                 alert_manager=None,
                 workflow_id: Optional[str] = None,
                 client_id: Optional[str] = None):
        """Initialize workflow engine with tracking support.
        
        Args:
            task_manager: Optional task manager instance
            tracker_type: Type of tracker to use (default: "reasontrack")
            tracker: Optional pre-initialized tracker instance
            metrics_collector: Optional pre-initialized metrics collector
            metrics_config: Optional metrics configuration
            state_storage: Optional pre-initialized state storage
            metrics_storage: Optional pre-initialized metrics storage
            alert_manager: Optional pre-initialized alert manager
            workflow_id: Optional workflow ID to initialize with
            client_id: Optional client ID for WebSocket notifications
        """
        self.workflow_id = workflow_id
        self.client_id = client_id
        self.workflow_graph = nx.DiGraph()
        self.task_manager = task_manager
        self.shared_memory = SharedMemory()
        self.agent_builder = CustomAgentBuilder()
        self._resources = []  # Track resources that need cleanup
        self.task_results = {}  # Store task results for dependency resolution
        self.event_type = BasicEventType if tracker_type == "basic" else EventType
        self.event_status = BasicEventStatus if tracker_type == "basic" else EventStatus
        self.metric_type = BasicMetricType if tracker_type == "basic" else MetricType


        try:
            if tracker:
                # Use pre-initialized components
                self.tracker = tracker
                self.metrics_collector = metrics_collector
                self.metrics_config = metrics_config
                self.state_storage = state_storage
                self.metrics_storage = metrics_storage
                self.alert_manager = alert_manager
                
                # Add resources for cleanup if they're not None
                for resource in [tracker, metrics_collector, state_storage, metrics_storage, alert_manager]:
                    if resource:
                        self._resources.append(resource)
                
                logger.info("Using pre-initialized ReasonTrack components")
                if workflow_id:
                    logger.info(f"Initialized with workflow ID: {workflow_id}")
            else:
                # Initialize new basic tracker as fallback
                logger.warning("No pre-initialized components provided, falling back to basic tracker")
                self.tracker = TrackerFactory.create_tracker(
                    "basic",
                    metrics_collector=None
                )
                self._resources.append(self.tracker)
                self.metrics_config = None
                self.metrics_collector = None
                self.state_storage = None
                self.metrics_storage = None
                self.alert_manager = None
            
        except Exception as e:
            logger.error(f"Error setting up workflow engine: {str(e)}")
            # Initialize basic tracker as fallback
            self.tracker = TrackerFactory.create_tracker(
                "basic",
                metrics_collector=None
            )
            self._resources.append(self.tracker)
            self.metrics_config = None
            self.metrics_collector = None
            self.state_storage = None
            self.metrics_storage = None
            self.alert_manager = None

    async def add_task(self, task_id: str, task_type: str, config: Dict[str, Any]) -> None:
        """Add a task to the workflow with tracking.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of task (llm, data_retrieval, etc.)
            config: Task configuration dictionary
        """
        try:
            # Validate task configuration
            if not isinstance(config, dict):
                raise ValueError(f"Task {task_id} configuration must be a dictionary")

            # Add node to workflow graph with proper configuration
            if task_type == "llm":
                if "agent" not in config:
                    raise ValueError(f"LLM task {task_id} missing 'agent' in config")
                if "params" not in config:
                    raise ValueError(f"LLM task {task_id} missing 'params' in config")
                    
                self.workflow_graph.add_node(
                    task_id,
                    task_type=task_type,
                    config=config,
                    agent=config["agent"]
                )
                
            elif task_type == "data_retrieval":
                if "agent_config" not in config:
                    raise ValueError(f"Data retrieval task {task_id} missing 'agent_config'")
                if "params" not in config:
                    raise ValueError(f"Data retrieval task {task_id} missing 'params'")
                    
                self.workflow_graph.add_node(
                    task_id,
                    task_type=task_type,
                    config=config
                )
                
            else:
                # Handle custom task types
                self.workflow_graph.add_node(
                    task_id,
                    task_type=task_type,
                    config=config
                )
            
            # Track task addition
            if self.tracker:
                try:
                    await self.tracker.track_task(
                        task_id=task_id,
                        workflow_id=self.workflow_id,
                        event_type=self.event_type.TASK.value,
                        event_name="Task Added",
                        event_status=self.event_status.COMPLETED,
                        source="reasonflow",
                        data={
                            "task_type": task_type,
                            "config": self._make_config_serializable(config),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                except Exception as track_error:
                    logger.error(f"Error tracking task addition: {str(track_error)}")
                    
        except Exception as e:
            logger.error(f"Error adding task {task_id}: {str(e)}")
            raise

    def _make_config_serializable(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Make configuration serializable for tracking.
        
        Args:
            config: Configuration dictionary to make serializable
            
        Returns:
            Dict[str, Any]: Serializable configuration
        """
        try:
            if not isinstance(config, dict):
                if hasattr(config, 'to_dict'):
                    return config.to_dict()
                elif hasattr(config, '__dict__'):
                    return str(config.__class__.__name__)
                return str(config)
                
            serializable = {}
            for key, value in config.items():
                if isinstance(value, dict):
                    serializable[key] = self._make_config_serializable(value)
                elif isinstance(value, (list, tuple, set)):
                    serializable[key] = [
                        self._make_config_serializable(item) if isinstance(item, (dict, object))
                        else str(item) if hasattr(item, '__dict__')
                        else item
                        for item in value
                    ]
                elif hasattr(value, 'to_dict'):
                    # Use to_dict method if available
                    serializable[key] = value.to_dict()
                elif hasattr(value, '__dict__'):
                    # For objects, just store the class name
                    serializable[key] = str(value.__class__.__name__)
                else:
                    # Handle basic types directly
                    serializable[key] = value
            return serializable
        except Exception as e:
            logger.error(f"Error making config serializable: {str(e)}")
            return str(config)

    async def add_dependency(self, from_task: str, to_task: str) -> None:
        """Add a dependency between tasks with tracking."""
        try:
            self.workflow_graph.add_edge(from_task, to_task)
            
            # Track dependency addition
            if self.tracker:
                await self.tracker.track_workflow(
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.WORKFLOW.value,
                    event_name="Dependency Added",
                    event_status=self.event_status.COMPLETED,
                    source="reasonflow",
                    data={
                        "from_task": from_task,
                        "to_task": to_task,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
        except Exception as e:
            logger.error(f"Error adding dependency: {str(e)}")
            raise

    def set_workflow_context(self, workflow_id: str, config: Dict[str, Any]) -> None:
        """Set workflow context with ID and configuration.
        
        Args:
            workflow_id: Unique identifier for the workflow
            config: Workflow configuration dictionary
        """
        try:
            if not workflow_id:
                raise ValueError("Workflow ID cannot be None or empty")
                
            self.workflow_id = workflow_id
            self.workflow_graph = nx.DiGraph()
            self.task_results = {}
            
            # Store workflow config
            self.workflow_config = config
            
            logger.info(f"Set workflow context for ID: {workflow_id}")
        except Exception as e:
            logger.error(f"Error setting workflow context: {str(e)}")
            raise

    async def _execute_task(self, task_id: str, task_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with enhanced tracking.
        
        Args:
            task_id: Task identifier
            task_type: Type of task
            config: Task configuration
            
        Returns:
            Dict[str, Any]: Task execution results
        """
        
        start_time = datetime.now(timezone.utc)
        common_tags = {"task_id": task_id, "workflow_id": self.workflow_id, "task_type": task_type}
        
        try:
            logger.info(f"Executing task {task_id} of type {task_type}")
            logger.info(f"Task config: {config}")
            logger.info(f"WebSocket client_id: {self.client_id}")
            
            # Track task start
            if self.tracker:
                await self.tracker.track_task(
                    task_id=task_id,
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.TASK.value,
                    event_name=f"{task_type.title()} Task",
                    event_status=self.event_status.PROCESSING,
                    source="reasonflow",
                    data={
                        "task_type": task_type,
                        "start_time": start_time.isoformat(),
                        "config": self._make_config_serializable(config),
                        "current_stage": "initialization",
                        "stages_completed": [],
                        "stages_remaining": ["preparation", "execution", "post_processing"]
                    }
                )
            
            # Resolve placeholders in config
            resolved_config = self._resolve_placeholders(task_id, config)
            
            # Execute task based on type
            if task_type == "browser":
                # Track browser task metrics start
                if self.metrics_collector and self.metrics_config:
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="browser_task_start",
                        value=1.0,
                        tags={"task_id": task_id, "workflow_id": self.workflow_id},
                        timestamp=start_time
                    )
                
                # Ensure actions are properly passed in the config
                if "actions" not in resolved_config:
                    logger.warning(f"No actions specified in browser task {task_id}")
                    resolved_config["actions"] = []
                    
                if "agent_config" not in resolved_config:
                    resolved_config["agent_config"] = {
                        "headless": True,
                        "browser_type": "chromium",
                        "timeout": 30000
                    }
                
                # Log actions being executed
                logger.info(f"Executing browser task with {len(resolved_config.get('actions', []))} actions")
                for idx, action in enumerate(resolved_config.get('actions', [])):
                    logger.info(f"Action {idx + 1}: {action.get('type')} - {action.get('config', {})}")
                logger.info(f"Resolved config: {resolved_config}")
                # Execute browser task with full configuration
                if asyncio.iscoroutinefunction(self.task_manager.execute_task):
                    result = await self.task_manager.execute_task(task_id, task_type, resolved_config)
                else:
                    result = self.task_manager.execute_task(task_id, task_type, resolved_config)
                # Track browser-specific metrics
                if self.metrics_collector and self.metrics_config:
                    browser_metadata = result.get("metadata", {})
                    
                    # Track page load time
                    if "load_time" in browser_metadata:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="browser_page_load_time",
                            value=float(browser_metadata["load_time"]),
                            tags=common_tags,
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track download metrics
                    if "download" in browser_metadata:
                        download_info = browser_metadata["download"]
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="browser_download_size",
                            value=float(download_info.get("size", 0)),
                            tags={**common_tags, "mime_type": download_info.get("mime_type", "unknown")},
                            timestamp=datetime.now(timezone.utc)
                        )
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="browser_download_time",
                            value=float(download_info.get("download_time", 0)),
                            tags={**common_tags, "mime_type": download_info.get("mime_type", "unknown")},
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track extraction metrics
                    if "extraction" in browser_metadata:
                        extraction_info = browser_metadata["extraction"]
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="browser_extraction_count",
                            value=float(extraction_info.get("items_extracted", 0)),
                            tags=common_tags,
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track errors
                    if "errors" in browser_metadata:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.COUNTER,
                            name="browser_errors",
                            value=float(len(browser_metadata["errors"])),
                            tags=common_tags,
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                    # Track action completion
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.COUNTER,
                        name="browser_actions_completed",
                        value=float(len(resolved_config.get('actions', []))),
                        tags=common_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                # Log the results
                logger.info(f"Browser task completed with results: {result}")
                
            elif task_type in ["llm", "data_retrieval"]:
                # Track task metrics start
                if self.metrics_collector and self.metrics_config:
                    metric_config = self.metrics_config.llm if task_type == "llm" else self.metrics_config.vectordb
                    if metric_config:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name=f"{task_type}_task_start",
                            value=1.0,
                            tags={"task_id": task_id, "workflow_id": self.workflow_id},
                            timestamp=start_time
                        )
                
                # # Create and execute agent
                # agent = self.agent_builder.create_agent(agent_type=task_type, config=resolved_config)
                # if asyncio.iscoroutinefunction(agent.execute):
                #     result = await agent.execute(**resolved_config.get("params", {}))
                # else:
                #     result = agent.execute(**resolved_config.get("params", {}))
                if asyncio.iscoroutinefunction(self.task_manager.execute_task):
                    result = await self.task_manager.execute_task(task_id, task_type, resolved_config)
                else:
                    result = self.task_manager.execute_task(task_id, task_type, resolved_config)

                # Track LLM-specific metrics if available
                if task_type == "llm" and self.metrics_collector and self.metrics_config:
                    # Handle case where result might be a string or unexpected format
                    if isinstance(result, dict):
                        llm_metadata = result.get("output", {})
                        if isinstance(llm_metadata, dict):
                            llm_metadata = llm_metadata.get("metadata", {})
                        else:
                            llm_metadata = {}
                    else:
                        llm_metadata = {}
                    
                    provider = llm_metadata.get("provider") if isinstance(llm_metadata, dict) else None
                    model = llm_metadata.get("model") if isinstance(llm_metadata, dict) else None
                    usage = llm_metadata.get("usage", {}) if isinstance(llm_metadata, dict) else {}
                    
                    # Track token usage
                    if "completion_tokens" in usage:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.COUNTER,
                            name="llm_output_tokens",
                            value=float(usage["completion_tokens"]),
                            tags={**common_tags, "provider": provider, "model": model},
                            timestamp=datetime.now(timezone.utc)
                        )
                    if "prompt_tokens" in usage:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.COUNTER,
                            name="llm_input_tokens",
                            value=float(usage["prompt_tokens"]),
                            tags={**common_tags, "provider": provider, "model": model},
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track memory usage if available
                    if "memory_used" in usage:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="llm_memory_used",
                            value=float(usage["memory_used"]),
                            tags={**common_tags, "provider": provider, "model": model},
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track cost if available
                    if "total_cost" in usage:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.COUNTER,
                            name="llm_cost",
                            value=float(usage["total_cost"]),
                            tags={**common_tags, "provider": provider, "model": model},
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track latency
                    for timing_key in ["completion_time", "prompt_time", "total_time", "queue_time"]:
                        if timing_key in usage:
                            await self.metrics_collector.record_metric(
                                metric_type=self.metric_type.GAUGE,
                                name=f"llm_latency_{timing_key.replace('_time', '')}",
                                value=float(usage[timing_key]),
                                tags={**common_tags, "provider": provider, "model": model},
                                timestamp=datetime.now(timezone.utc)
                            )
                    
                    # Track cache hits
                    if "cache_hit" in llm_metadata:
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.COUNTER,
                            name="llm_cache_hits",
                            value=1.0 if llm_metadata["cache_hit"] else 0.0,
                            tags={**common_tags, "provider": provider, "model": model},
                            timestamp=datetime.now(timezone.utc)
                        )
                    
                    # Track hardware metrics if available
                    hardware_info = llm_metadata.get("hardware_info", {})
                    if hardware_info:
                        for metric_name, value in hardware_info.items():
                            if isinstance(value, (int, float)):
                                await self.metrics_collector.record_metric(
                                    metric_type=self.metric_type.GAUGE,
                                    name=f"llm_hardware_{metric_name}",
                                    value=float(value),
                                    tags={**common_tags, "provider": provider, "model": model},
                                    timestamp=datetime.now(timezone.utc)
                                )
                
                elif task_type == "data_retrieval" and self.metrics_collector and self.metrics_config:
                    # Extract VectorDB metadata
                    metadata = result.get("metadata", {})
                    summary = result.get("summary", {})
                    index_stats = metadata.get("index_stats", {})
                    
                    # Track full metadata in event manager
                    if self.tracker:
                        await self.tracker.track_task(
                            task_id=task_id,
                            workflow_id=self.workflow_id,
                            event_type=self.event_type.TASK.value,
                            event_name="VectorDB Operation",
                            event_status=self.event_status.COMPLETED,
                            source="reasonflow",
                            data={
                                "operation_type": metadata.get("query_type", "semantic_search"),
                                "query": metadata.get("query", ""),
                                "top_k": metadata.get("top_k", 0),
                                "num_results": metadata.get("num_results", 0),
                                "provider": metadata.get("provider", "unknown"),
                                "embedding_model": metadata.get("embedding_model", "unknown"),
                                "embedding_provider": metadata.get("embedding_provider", "unknown"),
                                "timestamp": metadata.get("timestamp"),
                                "cache_hit": metadata.get("cache_hit", False),
                                "index_stats": index_stats,
                                "summary": summary,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        )
                    
                    # Track numerical metrics with relevant tags
                    vectordb_tags = {
                        **common_tags,
                        "provider": metadata.get("provider", "unknown"),
                        "embedding_model": metadata.get("embedding_model", "unknown"),
                        "embedding_provider": metadata.get("embedding_provider", "unknown"),
                        "query_type": metadata.get("query_type", "semantic_search")
                    }
                    
                    # Track summary metrics
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_total_results",
                        value=float(summary.get("total_results", 0)),
                        tags=vectordb_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_avg_score",
                        value=float(summary.get("avg_score", 0.0)),
                        tags=vectordb_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track latency
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.HISTOGRAM,
                        name="vectordb_latency",
                        value=float(summary.get("latency", 0.0)),
                        tags=vectordb_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track cost
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_cost",
                        value=metadata.get("cost", 0.0),
                        tags=vectordb_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track cache hits
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.COUNTER,
                        name="vectordb_cache_hits",
                        value=1.0 if metadata.get("cache_hit", False) else 0.0,
                        tags=vectordb_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track index metrics
                    index_tags = {
                        **vectordb_tags,
                        "dimensions": index_stats.get("dimensions", 0),
                        "db_type": index_stats.get("db_type", "unknown"),
                        "use_gpu": str(index_stats.get("use_gpu", False))
                    }
                    
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_total_vectors",
                        value=float(index_stats.get("total_vectors", 0)),
                        tags=index_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track hardware metrics
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_gpu_memory",
                        value=float(index_stats.get("gpu_memory", 0.0)),
                        tags=index_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_cpu_memory",
                        value=float(index_stats.get("cpu_memory", 0.0)),
                        tags=index_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    await self.metrics_collector.record_metric(
                        metric_type=self.metric_type.GAUGE,
                        name="vectordb_threads",
                        value=float(index_stats.get("num_threads", 0)),
                        tags=index_tags,
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    # Track per-result metrics
                    for i, result_item in enumerate(result.get("results", [])):
                        result_tags = {
                            **vectordb_tags,
                            "result_index": str(i),
                            "document_index": str(result_item.get("index", "unknown"))
                        }
                        
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="vectordb_result_score",
                            value=float(result_item.get("score", 0.0)),
                            tags=result_tags,
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        # Track result metadata metrics if available
                        result_metadata = result_item.get("metadata", {})
                        search_metrics = result_metadata.get("search_metrics", {})
                        
                        if search_metrics:
                            await self.metrics_collector.record_metric(
                                metric_type=self.metric_type.GAUGE,
                                name="vectordb_result_search_time",
                                value=float(search_metrics.get("search_time", 0.0)),
                                tags=result_tags,
                                timestamp=datetime.now(timezone.utc)
                            )
                            
                            await self.metrics_collector.record_metric(
                                metric_type=self.metric_type.GAUGE,
                                name="vectordb_result_similarity",
                                value=float(search_metrics.get("similarity_score", 0.0)),
                                tags=result_tags,
                                timestamp=datetime.now(timezone.utc)
                            )
            else:
                # Handle custom task types through task manager
                result = await self.task_manager.execute_task(task_id, task_type, resolved_config)
            
            # Store task result for dependency resolution
            self.task_results[task_id] = result
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Track task completion
            if self.tracker:
                await self.tracker.track_task(
                    task_id=task_id,
                    workflow_id=self.workflow_id,
                    event_type=EventType.TASK.value,
                    event_name=f"{task_type.title()} Task",
                    event_status=EventStatus.COMPLETED,
                    source="reasonflow",
                    data={
                        "task_type": task_type,
                        "duration": duration,
                        "end_time": end_time.isoformat(),
                        "stages_completed": ["preparation", "execution", "post_processing"],
                        "stages_remaining": [],
                        "result": self._make_config_serializable(result),
                        "metrics": result.get("metrics", {})
                    }
                )
            
            # Track task metrics
            if self.metrics_collector and self.metrics_config and self.metrics_config.task:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.GAUGE,
                    name="task_duration",
                    value=duration,
                    tags=common_tags,
                    timestamp=end_time
                )
                
                # Track task success
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name="task_success",
                    value=1.0,
                    tags=common_tags,
                    timestamp=end_time
                )
            
            # Send WebSocket notification if client_id is set
            if self.client_id:
                logger.info(f"Sending WebSocket notification for task {task_id} to client {self.client_id}")
                # Get the next task(s) from the workflow graph
                next_tasks = list(self.workflow_graph.successors(task_id)) if task_id in self.workflow_graph else []
                
                # Prepare notification data
                notification_data = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "status": "completed",
                    "next_task": next_tasks[0] if next_tasks else None,
                    "result_summary": {
                        "success": True,
                        "execution_time": (datetime.now(timezone.utc) - start_time).total_seconds(),
                        "output_summary": str(result.get("output", ""))[:100] + "..." if len(str(result.get("output", ""))) > 100 else str(result.get("output", ""))
                    }
                }
                
                # Send notification
                try:
                    await notifier.notify_task_completion(self.client_id, notification_data)
                    logger.info(f"Successfully sent WebSocket notification for task {task_id}")
                except Exception as notif_error:
                    logger.error(f"Error sending WebSocket notification: {str(notif_error)}")
            else:
                logger.warning(f"No WebSocket notification sent for task {task_id} - client_id not set")
            
            return result
            
        except Exception as e:
            error_time = datetime.now(timezone.utc)
            error_duration = (error_time - start_time).total_seconds()
            
            logger.error(f"Error executing task {task_id}: {str(e)}")
            
            # Track task failure
            if self.tracker:
                await self.tracker.track_task(
                    task_id=task_id,
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.TASK.value,
                    event_name=f"{task_type.title()} Task",
                    event_status=self.event_status.FAILED,
                    source="reasonflow",
                    data={
                        "task_type": task_type,
                        "error": str(e),
                        "duration": error_duration,
                        "end_time": error_time.isoformat()
                    }
                )
            
            # Track failure metrics
            if self.metrics_collector and self.metrics_config and self.metrics_config.task:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name="task_failure",
                    value=1.0,
                    tags={**common_tags, "error": str(e)},
                    timestamp=error_time
                )
            
            # Send error notification if client_id is set
            if self.client_id:
                error_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                notification_data = {
                    "task_id": task_id,
                    "task_type": task_type,
                    "status": "error",
                    "error": str(e),
                    "result_summary": {
                        "success": False,
                        "execution_time": error_duration,
                        "error_message": str(e)
                    }
                }
                await notifier.notify_task_completion(self.client_id, notification_data)
            
            raise

    def _resolve_placeholders(self, task_id: str, config: Dict) -> Dict:
        """
        Resolve placeholders in task parameters using the outputs of preceding tasks.
        """
        try:
            params = config.get("params", {})
            for key, value in params.items():
                if not isinstance(value, str):
                    logger.debug(f"Skipping placeholder resolution for key '{key}': Value is not a string")
                    continue

                logger.debug(f"Processing key '{key}' with value: {value}")
                for match in re.finditer(r'\{\{([\w\-\.]+)\.([\w\-\.]+)\}\}', value):
                    ref_task_id, field = match.groups()
                    logger.debug(f"Found placeholder: ref_task_id={ref_task_id}, field={field}")
                    
                    if ref_task_id in self.task_results:
                        result = self.task_results[ref_task_id]
                        if isinstance(result, dict) and field in result:
                            field_value = result[field]
                            logger.debug(f"Resolving placeholder '{{{{{ref_task_id}.{field}}}}}' with value: {field_value}")
                            params[key] = value.replace(match.group(0), str(field_value))
                        else:
                            # If the field doesn't exist, try to use the entire result
                            logger.warning(f"Field '{field}' not found in results of task {ref_task_id}, using entire result")
                            params[key] = value.replace(match.group(0), str(result))
                    else:
                        logger.warning(f"Task ID '{ref_task_id}' not found in task results")
                        params[key] = value.replace(match.group(0), "[UNRESOLVED]")

            logger.debug(f"Params after resolution: {params}")
            config["params"] = params
            return config
            
        except Exception as e:
            logger.error(f"Error resolving placeholders: {str(e)}")
            return config


    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the workflow with tracking.
        
        Returns:
            Dict[str, Any]: Workflow execution results
        """
        if not self.workflow_id:
            raise ValueError("Workflow context not set")
            
        start_time = datetime.now(timezone.utc)
        results = {}
        completed_tasks = 0
        total_tasks = 0
        
        try:
            # Track workflow execution start
            if self.tracker:
                await self.tracker.track_workflow(
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.WORKFLOW.value,
                    event_name="Workflow Execution",
                    event_status=self.event_status.PROCESSING,
                    source="reasonflow",
                    data={
                        "start_time": start_time.isoformat(),
                        "total_tasks": len(self.workflow_graph.nodes),
                        "completed_tasks": 0,
                        "current_stage": "initialization"
                    }
                )
            
            # Track workflow metrics start
            if self.metrics_collector and self.metrics_config:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.GAUGE,
                    name="workflow_progress",
                    value=0.0,
                    tags={"workflow_id": self.workflow_id},
                    timestamp=start_time
                )
            
            # Get execution order
            try:
                execution_order = list(nx.topological_sort(self.workflow_graph))
                total_tasks = len(execution_order)
            except nx.NetworkXUnfeasible:
                raise ValueError("Workflow contains cycles")
            
            # Execute tasks in order
            for task_id in execution_order:
                task_data = self.workflow_graph.nodes[task_id]
                task_type = task_data["task_type"]
                task_config = task_data["config"]
                
                try:
                    results[task_id] = await self._execute_task(
                        task_id=task_id,
                        task_type=task_type,
                        config=task_config
                    )
                    
                    completed_tasks += 1
                    
                    # Update workflow progress
                    if self.metrics_collector and self.metrics_config:
                        progress = (completed_tasks / total_tasks) * 100
                        await self.metrics_collector.record_metric(
                            metric_type=self.metric_type.GAUGE,
                            name="workflow_progress",
                            value=progress,
                            tags={"workflow_id": self.workflow_id},
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                except Exception as task_error:
                    logger.error(f"Error executing task {task_id}: {str(task_error)}")
                    raise
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            # Track workflow completion
            if self.tracker:
                await self.tracker.track_workflow(
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.WORKFLOW.value,
                    event_name="Workflow Execution",
                    event_status=self.event_status.COMPLETED,
                    source="reasonflow",
                    data={
                        "duration": duration,
                        "end_time": end_time.isoformat(),
                        "completed_tasks": completed_tasks,
                        "total_tasks": total_tasks,
                        "success_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                    }
                )
            
            # Track final workflow metrics
            if self.metrics_collector and self.metrics_config:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.GAUGE,
                    name="workflow_duration",
                    value=duration,
                    tags={"workflow_id": self.workflow_id},
                    timestamp=end_time
                )
                
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name="workflow_success",
                    value=1.0,
                    tags={"workflow_id": self.workflow_id},
                    timestamp=end_time
                )
            
            # Send workflow completion notification via WebSocket
            if self.client_id:
                workflow_data = {
                    "workflow_id": self.workflow_id,
                    "status": "completed",
                    "summary": {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "success_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
                        "execution_time": duration,
                        "completed_at": end_time.isoformat()
                    }
                }
                await notifier.notify_workflow_completion(self.client_id, workflow_data)
            
            return results
            
        except Exception as e:
            error_time = datetime.now(timezone.utc)
            error_duration = (error_time - start_time).total_seconds()
            
            logger.error(f"Error executing workflow: {str(e)}")
            
            # Track workflow failure
            if self.tracker:
                await self.tracker.track_workflow(
                    workflow_id=self.workflow_id,
                    event_type=self.event_type.WORKFLOW.value,
                    event_name="Workflow Execution",
                    event_status=self.event_status.FAILED,
                    source="reasonflow",
                    data={
                        "error": str(e),
                        "duration": error_duration,
                        "end_time": error_time.isoformat(),
                        "completed_tasks": completed_tasks,
                        "total_tasks": total_tasks,
                        "success_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                    }
                )
            
            # Track failure metrics
            if self.metrics_collector and self.metrics_config:
                await self.metrics_collector.record_metric(
                    metric_type=self.metric_type.COUNTER,
                    name="workflow_failure",
                    value=1.0,
                    tags={"workflow_id": self.workflow_id, "error": str(e)},
                    timestamp=error_time
                )
            
            # Send workflow error notification via WebSocket
            if self.client_id:
                workflow_data = {
                    "workflow_id": self.workflow_id,
                    "status": "error",
                    "error": str(e),
                    "summary": {
                        "total_tasks": total_tasks,
                        "completed_tasks": completed_tasks,
                        "success_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
                        "execution_time": error_duration,
                        "failed_at": error_time.isoformat()
                    }
                }
                await notifier.notify_workflow_completion(self.client_id, workflow_data)
            
            raise

    async def get_metrics(self, 
                        names: List[str], 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get metrics from the metrics collector.
        
        Args:
            metric_names: List of metric names to retrieve
            start_time: Optional start time for the query range
            end_time: Optional end time for the query range
            tags: Optional tags to filter metrics
            
        Returns:
            Dict[str, Any]: Retrieved metrics
        """
        if not self.metrics_collector:
            return {}
            
        try:
            # Set default time range if not provided
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            if start_time is None:
                start_time = end_time - timedelta(hours=1)
            
            # Query metrics
            metrics = await self.metrics_collector.get_metrics(
                names=names,
                start_time=start_time,
                end_time=end_time,
                tags=tags or {}
            )
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return {}

    async def get_workflow_metrics(self, workflow_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive workflow metrics.
        
        Args:
            workflow_id: The workflow ID to get metrics for
            
        Returns:
            Dict[str, Any]: Workflow metrics
        """
        workflow_metrics = [
            "workflow_duration",
            "workflow_progress",
            "workflow_success",
            "workflow_failure",
            "task_completion_rate",
            "resource_utilization"
        ]
        
        return await self.get_metrics(
            names=workflow_metrics,
            start_time=start_time,
            end_time=end_time,
            tags={"workflow_id": workflow_id}
        )

    async def get_task_metrics(self, task_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive task metrics.
        
        Args:
            task_id: The task ID to get metrics for
            
        Returns:
            Dict[str, Any]: Task metrics
        """
        # Get task type from graph
        task_data = self.workflow_graph.nodes.get(task_id, {})
        task_type = task_data.get("task_type")
        
        # Define metrics based on task type
        if task_type == "llm":
            metric_names = [
                "llm_output_tokens",
                "llm_input_tokens",
                "llm_memory_used",
                "llm_cost",
                "llm_latency",
                "llm_cache_hits",
                "task_duration",
                "task_success",
                "task_failure"
            ]
        elif task_type == "data_retrieval":
            metric_names = [
                "vectordb_latency",
                "vectordb_cost",
                "vectordb_gpu_memory",
                "vectordb_cache_hits",
                "vectordb_index_size",
                "vectordb_query_time",
                "task_duration",
                "task_success",
                "task_failure"
            ]
        else:
            metric_names = [
                "task_duration",
                "task_success",
                "task_failure",
                "task_memory_used",
                "task_cpu_usage",
                "task_gpu_usage"
            ]
        
        return await self.get_metrics(
            names=metric_names,
            start_time=start_time,
            end_time=end_time,
            tags={"task_id": task_id, "workflow_id": self.workflow_id}
        )

    async def get_system_metrics(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get system-wide metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        system_metrics = [
            "system_memory_usage",
            "system_cpu_usage",
            "system_gpu_usage",
            "system_disk_usage",
            "system_network_usage",
            "active_workflows",
            "active_tasks",
            "error_rate",
            "total_cost"
        ]
        
        return await self.get_metrics(
            names=system_metrics,
            start_time=start_time,
            end_time=end_time
        )

    async def get_custom_metrics(self,
                               metric_names: List[str],
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get custom metrics with specific parameters.
        
        Args:
            metric_names: List of metric names to retrieve
            start_time: Optional start time for the query range
            end_time: Optional end time for the query range
            tags: Optional tags to filter metrics
            
        Returns:
            Dict[str, Any]: Retrieved metrics
        """
        return await self.get_metrics(
            names=metric_names,
            start_time=start_time,
            end_time=end_time,
            tags=tags
        )

    async def check_system_health(self) -> Dict[str, Any]:
        """Check health status of all components."""
        if not self.tracker:
            return {"status": "unknown"}
        health = await self.tracker.check_system_health()
        return await self._ensure_awaited(health)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        cleanup_errors = []
        
        for resource in self._resources:
            try:
                if hasattr(resource, 'cleanup') and callable(resource.cleanup):
                    await resource.cleanup()
                elif hasattr(resource, 'close') and callable(resource.close):
                    await resource.close()
                elif hasattr(resource, 'session') and resource.session:
                    await resource.session.close()
            except Exception as e:
                error_msg = f"Error cleaning up {resource.__class__.__name__}: {str(e)}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)
        
        if cleanup_errors:
            logger.error("Errors during cleanup:\n" + "\n".join(cleanup_errors))
        else:
            logger.info("Successfully cleaned up all resources")

    async def _ensure_awaited(self, data: Any) -> Any:
        """Ensure all coroutines in the data are awaited."""
        if isinstance(data, Dict):
            return {k: await self._ensure_awaited(v) for k, v in data.items()}
        elif isinstance(data, List):
            return [await self._ensure_awaited(item) for item in data]
        elif asyncio.iscoroutine(data):
            return await data
        return data
    def _serialize_value(self, value: Any) -> Any:
            """
            Helper method to serialize individual values.
            """
            import numpy as np
            try:
                if hasattr(value, '__dict__'):
                    # Convert objects with __dict__ attribute to their string representation
                    return str(value)
                elif isinstance(value, (int, float, str, bool, type(None))):
                    # Basic JSON-serializable types
                    return value
                elif isinstance(value, (np.ndarray, list, tuple, set)):
                    # Convert collections to lists
                    return list(value)
                elif isinstance(value, (np.floating, np.integer)):
                    # Convert numpy types to native Python types
                    return value.item()
                else:
                    # Fallback: convert to string
                    return str(value)
            except Exception as e:
                # Handle serialization errors gracefully
                return f"// Serialization Error: {str(e)}"
