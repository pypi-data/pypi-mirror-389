from typing import Dict, Any, List, Optional
import uuid
import time
import logging
import networkx as nx
from datetime import datetime, timedelta, timezone
import asyncio
import numpy as np
from reasontrack import (
    LLMConfig,
    MetricsConfig,
    VectorDBConfig,
    TaskConfig,
    RuntimeMode,
    HardwareType
)

from reasontrack.storage.event_store import EventType, EventStatus
from reasonflow.observability.reasontrack_management_initializer import get_reasontrack_config
from reasonflow.observability.reasontrack_adapter import ReasonTrackAdapter
from reasonflow.observability.tracker_factory import TrackerFactory
from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonchain.memory import SharedMemory
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.observability.basic_tracker import BasicMetricsCollector, BasicTaskConfig, BasicWorkflowConfig, BasicLLMConfig, BasicVectorDBConfig, BasicMetricsConfig

logger = logging.getLogger(__name__)

class WorkflowBuilder:
    """Workflow builder with comprehensive tracking support."""

    def __init__(self, task_manager=None, tracker_type="reasontrack", tracker_config=None, metrics_config=None, config_path=None, client_id: Optional[str] = None):
        """Initialize WorkflowBuilder with optional task manager and tracking"""
        self._resources = []  # Track resources that need cleanup
        
        # Initialize task manager
        self.task_manager = task_manager or TaskManager(shared_memory=SharedMemory())
        self._resources.append(self.task_manager)
        self._client_id = client_id  # Store client_id privately
        self.tracker_type = tracker_type
        self.config = {}
        
        if tracker_type == "reasontrack":
            try:
                # Initialize ReasonTrack components using ManagementInitializer
                if config_path:
                    self.config = get_reasontrack_config(config_path)
                else:
                    self.config = tracker_config or {}
                
                # Get initialized components
                self.tracker = ReasonTrackAdapter(self.config)
                self.state_storage = self.tracker.state_storage
                self.metrics_storage = self.tracker.metric_storage
                self.metrics_collector = self.tracker.metrics_collector
                self.alert_manager = self.tracker.alert_manager
                self.state_manager = self.tracker.state_manager
                self.version_manager = self.tracker.version_manager
                
                # Add resources for cleanup
                self._resources.extend([
                    self.state_storage,
                    self.metrics_storage,
                    self.metrics_collector,
                    self.tracker,
                    self.alert_manager,
                    self.state_manager,
                    self.version_manager
                ])
                
                # Store metrics config for later use
                self.metrics_config = metrics_config or self.config.get("metrics_config") or self.config.metrics_config
                
                logger.info(f"Initialized {self.tracker_type} components successfully")
                
            except Exception as e:
                logger.error(f"Error initializing ReasonTrack components: {str(e)}")
                logger.warning("Falling back to basic tracker")
                self._init_basic_tracker()

        elif tracker_type == "basic":
            self._init_basic_tracker()

        # Initialize workflow engine with our components
        self.engine = WorkflowEngine(
            task_manager=self.task_manager,
            tracker_type=tracker_type,
            tracker=self.tracker,
            metrics_collector=self.metrics_collector,
            metrics_config=self.metrics_config,
            state_storage=self.state_storage,
            metrics_storage=self.metrics_storage,
            alert_manager=self.alert_manager,
            client_id=self._client_id
        )
        self._resources.append(self.engine)
        
        self.logger = logging.getLogger(__name__)

    def _init_basic_tracker(self):
        """Initialize basic tracker and its components."""
        try:
            # Create metrics collector first
            self.metrics_collector = BasicMetricsCollector()
            
            # Create basic tracker with the metrics collector
            self.tracker = TrackerFactory.create_tracker(
                tracker_type="basic",
                metrics_collector=self.metrics_collector
            )
            
            # Get components from basic tracker
            self.state_manager = self.tracker.state_manager
            
            # Set None for components not available in basic tracker
            self.state_storage = None  # Basic tracker doesn't need external storage
            self.metrics_storage = None  # Basic tracker doesn't need external storage
            self.alert_manager = None  # Basic tracker doesn't have alert management
            self.version_manager = None  # Basic tracker doesn't have version management
            
            # Add resources for cleanup
            self._resources.extend([
                self.metrics_collector,
                self.tracker,
                self.state_manager
            ])
            
            # Set basic metrics config using Pydantic models
            self.metrics_config = BasicMetricsConfig(
                task=BasicTaskConfig(
                    enabled=True,
                    collection_interval=60,
                    retention_days=7,
                    track_memory=True,
                    track_cpu=True,
                    track_gpu=False,
                    hardware_type=HardwareType.CPU,
                    runtime_mode=RuntimeMode.ASYNC
                ),
                workflow=BasicWorkflowConfig(
                    enabled=True,
                    collection_interval=300,
                    retention_days=30
                ),
                llm=BasicLLMConfig(
                    track_tokens=True,
                    track_latency=True,
                    track_cost=True,
                    track_cache=True,
                    track_memory=True
                ),
                vectordb=BasicVectorDBConfig(
                    track_latency=True,
                    track_throughput=True,
                    track_cache=True,
                    track_memory=True
                )
            )
            
            logger.info("Initialized basic tracker components successfully")
            
        except Exception as e:
            logger.error(f"Error initializing basic tracker: {str(e)}")
            # Set minimal configuration in case of error
            self.metrics_collector = BasicMetricsCollector()
            self.tracker = TrackerFactory.create_tracker("basic", metrics_collector=self.metrics_collector)
            self.state_manager = self.tracker.state_manager
            self._resources.extend([self.metrics_collector, self.tracker, self.state_manager])
            # Create minimal metrics config with Pydantic models
            self.metrics_config = BasicMetricsConfig(
                task=BasicTaskConfig(enabled=True),
                workflow=BasicWorkflowConfig(enabled=True)
            )

    @property
    def client_id(self) -> Optional[str]:
        """Get the client ID."""
        return self._client_id

    @client_id.setter
    def client_id(self, value: Optional[str]):
        """Set the client ID and propagate to engine."""
        self._client_id = value
        if hasattr(self, 'engine'):
            self.engine.client_id = value

    def _generate_version_info(self, workflow_config: Dict[str, Any], workflow_id: str) -> Dict[str, Any]:
        """Generate version information for a workflow.
        
        Args:
            workflow_config: The workflow configuration
            workflow_id: The workflow ID
            
        Returns:
            Dict containing version information
        """
        version = workflow_config.get("version", "1.0.0")
        
        # Generate version hash based on critical workflow components
        tasks_hash = hash(str(sorted(workflow_config.get("tasks", {}).items())))
        deps_hash = hash(str(sorted(workflow_config.get("dependencies", []))))
        config_hash = hash(f"{tasks_hash}:{deps_hash}")
        
        version_info = {
            "version": version,
            "config_hash": str(config_hash),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workflow_id": workflow_id,
            "task_count": len(workflow_config.get("tasks", {})),
            "dependency_count": len(workflow_config.get("dependencies", [])),
            "task_types": list(set(task.get("type") for task in workflow_config.get("tasks", {}).values())),
            "metadata": {
                "type": workflow_config.get("type", "standard"),
                "owner": workflow_config.get("owner", "system"),
                "priority": workflow_config.get("priority", "medium"),
                "tags": workflow_config.get("tags", []),
                "description": workflow_config.get("description", ""),
                "parent_version": workflow_config.get("parent_version", None)
            }
        }
        
        return version_info

    async def _track_workflow_version(self, workflow_id: str, workflow_config: Dict[str, Any], version_info: Dict[str, Any]) -> None:
        """Track workflow version using ReasonTrack's VersionManager.
        
        Args:
            workflow_id: The workflow ID
            workflow_config: The workflow configuration
            version_info: Version information to track
        """
        if not self.version_manager:
            logger.warning("Version manager not available, skipping version tracking")
            return
            
        try:
            # Create version with full data and metadata
            await self.version_manager.create_version(
                entity_id=workflow_id,
                data={
                    "config": workflow_config,
                    "version_info": version_info
                },
                metadata={
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "version": version_info["version"],
                    "config_hash": version_info["config_hash"],
                    "task_count": version_info["task_count"],
                    "dependency_count": version_info["dependency_count"],
                    "task_types": version_info["task_types"],
                    "type": version_info["metadata"]["type"],
                    "owner": version_info["metadata"]["owner"],
                    "priority": version_info["metadata"]["priority"],
                    "tags": version_info["metadata"]["tags"],
                    "description": version_info["metadata"]["description"],
                    "parent_version": version_info["metadata"]["parent_version"]
                }
            )
            logger.info(f"Created version for workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error creating workflow version: {str(e)}")

    async def get_workflow_version_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get version history for a workflow using ReasonTrack's VersionManager.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of version information dictionaries
        """
        try:
            if not self.version_manager:
                logger.warning("Version manager not available")
                return []
                
            history = await self.version_manager.get_version_history(workflow_id)
            return history
            
        except Exception as e:
            logger.error(f"Error getting workflow version history: {str(e)}")
            return []

    async def compare_workflow_versions(self, workflow_id: str, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """Compare two workflow versions.
        
        Args:
            workflow_id: The workflow ID
            version_id1: First version ID to compare
            version_id2: Second version ID to compare
            
        Returns:
            Dict containing version differences
        """
        try:
            if not self.version_manager:
                logger.warning("Version manager not available")
                return {}
                
            differences = await self.version_manager.compare_versions(
                entity_id=workflow_id,
                version_id1=version_id1,
                version_id2=version_id2
            )
            return differences
            
        except Exception as e:
            logger.error(f"Error comparing workflow versions: {str(e)}")
            return {}

    async def rollback_workflow_version(self, workflow_id: str, version_id: str) -> Optional[Dict[str, Any]]:
        """Rollback workflow to a previous version.
        
        Args:
            workflow_id: The workflow ID
            version_id: Version ID to rollback to
            
        Returns:
            Optional[Dict[str, Any]]: New version information if rollback successful
        """
        try:
            if not self.version_manager:
                logger.warning("Version manager not available")
                return None
                
            rollback = await self.version_manager.rollback_version(
                entity_id=workflow_id,
                version_id=version_id
            )
            if rollback:
                logger.info(f"Rolled back workflow {workflow_id} to version {version_id}")
                return rollback.to_dict()
                
            return None
            
        except Exception as e:
            logger.error(f"Error rolling back workflow version: {str(e)}")
            return None

    async def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Create a workflow from configuration with tracking.

        Args:
            workflow_config: Workflow configuration dictionary

        Returns:
            str: Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        
        try:
            # Debug log the incoming configuration
            logger.debug(f"Creating workflow with config: {workflow_config}")
            
            # Validate workflow configuration
            if not isinstance(workflow_config, dict):
                logger.error(f"Workflow configuration must be a dictionary, got {type(workflow_config)}")
                raise ValueError("Workflow configuration must be a dictionary")
                
            if not workflow_config:
                logger.error("Workflow configuration is empty")
                raise ValueError("Workflow configuration is empty")
                
            if "tasks" not in workflow_config:
                logger.error(f"Missing tasks key in config. Keys present: {list(workflow_config.keys())}")
                raise ValueError("Invalid workflow configuration - missing tasks")
                
            if not isinstance(workflow_config["tasks"], dict):
                logger.error(f"Tasks must be a dictionary, got {type(workflow_config['tasks'])}")
                raise ValueError("Tasks configuration must be a dictionary")
                
            if not workflow_config["tasks"]:
                logger.error("No tasks defined in workflow configuration")
                raise ValueError("No tasks defined in workflow configuration")
                
            # Generate version information
            # version_info = self._generate_version_info(workflow_config, workflow_id)
            
            # Track version using ReasonTrack's VersionManager
            # await self._track_workflow_version(workflow_id, workflow_config, version_info)
                
            # Make config serializable
            serializable_config = self._make_config_serializable(workflow_config)
            
            # Create engine instance if not exists
            if not self.engine:
                self.engine = WorkflowEngine(
                    task_manager=self.task_manager,
                    tracker_type=self.tracker_type,
                    tracker=self.tracker,
                    metrics_collector=self.metrics_collector,
                    metrics_config=self.metrics_config,
                    state_storage=self.state_storage,
                    metrics_storage=self.metrics_storage,
                    alert_manager=self.alert_manager,
                    workflow_id=workflow_id,
                    client_id=self.client_id
                )
                self._resources.append(self.engine)
            
            # Set workflow context
            self.engine.set_workflow_context(workflow_id, serializable_config)
            
            # Track workflow creation
            if self.engine.tracker:
                try:
                    await self.engine.tracker.track_workflow(
                        workflow_id=workflow_id,
                        event_type=EventType.WORKFLOW.value,
                        event_name="Workflow Creation",
                        event_status=EventStatus.PROCESSING,
                        source="reasonflow",
                        data={
                            "config": serializable_config,
                            "start_time": start_time.isoformat(),
                            "version_info": "v1",
                            "metadata": {
                                "version": workflow_config.get("version", "1.0.0"),
                                "total_tasks": len(workflow_config["tasks"]),
                                "type": workflow_config.get("type", "standard"),
                                "owner": workflow_config.get("owner", "system"),
                                "priority": workflow_config.get("priority", "medium"),
                                "tags": workflow_config.get("tags", [])
                            }
                        }
                    )
                except Exception as track_error:
                    logger.error(f"Error tracking workflow creation: {str(track_error)}")

            # Initialize workflow graph
            try:
                for task_id, task_config in workflow_config["tasks"].items():
                    if not isinstance(task_config, dict):
                        raise ValueError(f"Invalid task configuration for task {task_id}")
                    
                    if "type" not in task_config:
                        raise ValueError(f"Task {task_id} missing type")
                        
                    if "config" not in task_config:
                        raise ValueError(f"Task {task_id} missing config")
                        
                    # Special handling for browser tasks
                    if task_config["type"] == "browser":
                        if "actions" not in task_config["config"]:
                            task_config["config"]["actions"] = []
                        if "agent_config" not in task_config["config"]:
                            task_config["config"]["agent_config"] = {
                                "headless": True,
                                "browser_type": "chromium",
                                "timeout": 30000
                            }
                        
                    await self.engine.add_task(
                        task_id,
                        task_config["type"],
                        task_config["config"]
                    )
            except Exception as task_error:
                logger.error(f"Error adding tasks to workflow: {str(task_error)}")
                raise

            # Add dependencies
            try:
                for dep in workflow_config.get("dependencies", []):
                    if not isinstance(dep, dict):
                        raise ValueError(f"Invalid dependency configuration: {dep}")
                        
                    if "from" not in dep or "to" not in dep:
                        raise ValueError(f"Dependency missing from/to fields: {dep}")
                        
                    await self.engine.add_dependency(dep["from"], dep["to"])
            except Exception as dep_error:
                logger.error(f"Error adding dependencies to workflow: {str(dep_error)}")
                raise

            # Track workflow creation completion with version info
            if self.engine.tracker:
                try:
                    await self.engine.tracker.track_workflow(
                        workflow_id=workflow_id,
                        event_type=EventType.WORKFLOW.value,
                        event_name="Workflow Creation",
                        event_status=EventStatus.COMPLETED,
                        source="reasonflow",
                        data={
                            "duration": (datetime.now(timezone.utc) - start_time).total_seconds(),
                            "end_time": datetime.now(timezone.utc).isoformat(),
                            "tasks_added": len(workflow_config["tasks"]),
                            "dependencies_added": len(workflow_config.get("dependencies", [])),
                            "version_info": "v1",
                            "metadata": {
                                "version": workflow_config.get("version", "1.0.0"),
                                "total_tasks": len(workflow_config["tasks"]),
                                "type": workflow_config.get("type", "standard"),
                                "owner": workflow_config.get("owner", "system"),
                                "priority": workflow_config.get("priority", "medium"),
                                "tags": workflow_config.get("tags", [])
                            }
                        }
                    )
                except Exception as track_error:
                    logger.error(f"Error tracking workflow creation completion: {str(track_error)}")
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            if self.engine and self.engine.tracker:
                try:
                    await self.engine.tracker.track_workflow(
                        workflow_id=workflow_id,
                        event_type=EventType.WORKFLOW.value,
                        event_name="Workflow Creation",
                        event_status=EventStatus.FAILED,
                        source="reasonflow",
                        data={
                            "error": str(e),
                            "duration": (datetime.now(timezone.utc) - start_time).total_seconds(),
                            "end_time": datetime.now(timezone.utc).isoformat(),
                            "version_info": "v1" if 'version_info' in locals() else None
                        }
                    )
                except Exception as track_error:
                    logger.error(f"Error tracking workflow creation failure: {str(track_error)}")
            raise
    def _validate_workflow_config(self, config: Dict[str, Any]) -> bool:
        """Validate the workflow configuration."""
        try:
            # Check if tasks exist and is a dictionary
            if "tasks" not in config:
                logger.error("No tasks found in workflow configuration")
                return False
                
            if not isinstance(config["tasks"], dict):
                logger.error("Tasks must be a dictionary")
                return False

            # Validate metrics configuration if present
            if "metrics_config" in config:
                metrics_config = config["metrics_config"]
                if not isinstance(metrics_config, dict):
                    logger.error("Metrics configuration must be a dictionary")
                    return False
                
                # Validate LLM metrics config
                if "llm" in metrics_config:
                    llm_config = metrics_config["llm"]
                    if not isinstance(llm_config, dict):
                        logger.error("LLM metrics configuration must be a dictionary")
                        return False
                    if not all(isinstance(v, bool) for v in llm_config.values()):
                        logger.error("LLM metrics configuration values must be boolean")
                        return False
                
                # Validate VectorDB metrics config
                if "vectordb" in metrics_config:
                    vdb_config = metrics_config["vectordb"]
                    if not isinstance(vdb_config, dict):
                        logger.error("VectorDB metrics configuration must be a dictionary")
                        return False
                    if not all(isinstance(v, bool) for v in vdb_config.values()):
                        logger.error("VectorDB metrics configuration values must be boolean")
                        return False
                
                # Validate task metrics config
                if "task" in metrics_config:
                    task_config = metrics_config["task"]
                    if not isinstance(task_config, dict):
                        logger.error("Task metrics configuration must be a dictionary")
                        return False
                    required_fields = ["track_memory", "track_cpu", "track_gpu", "hardware_type", "runtime_mode"]
                    if not all(field in task_config for field in required_fields):
                        logger.error(f"Task metrics configuration missing required fields: {required_fields}")
                        return False

            # Validate each task
            for task_id, task_config in config["tasks"].items():
                if not isinstance(task_config, dict):
                    logger.error(f"Task {task_id} configuration must be a dictionary")
                    return False
                    
                if "type" not in task_config:
                    logger.error(f"Task {task_id} missing 'type' field")
                    return False
                    
                # Validate LLM task configuration
                if task_config["type"] == "llm":
                    if "config" not in task_config:
                        logger.error(f"Task {task_id} missing 'config' field")
                        return False
                    if "agent" not in task_config["config"]:
                        logger.error(f"LLM task {task_id} missing 'agent' in config")
                        return False
                    if "params" not in task_config["config"]:
                        logger.error(f"LLM task {task_id} missing 'params' in config")
                        return False
                    if "prompt" not in task_config["config"]["params"]:
                        logger.error(f"LLM task {task_id} missing 'prompt' in params")
                        return False
                        
                # Validate data retrieval task configuration
                elif task_config["type"] == "data_retrieval":
                    if "config" not in task_config:
                        logger.error(f"Task {task_id} missing 'config' field")
                        return False
                    if "agent_config" not in task_config["config"]:
                        logger.error(f"Data retrieval task {task_id} missing 'agent_config'")
                        return False
                    if "params" not in task_config["config"]:
                        logger.error(f"Data retrieval task {task_id} missing 'params'")
                        return False

            # Validate dependencies if they exist
            if "dependencies" in config:
                if not isinstance(config["dependencies"], list):
                    logger.error("Dependencies must be a list")
                    return False
                    
                task_ids = set(config["tasks"].keys())
                for dep in config["dependencies"]:
                    if not isinstance(dep, dict):
                        logger.error("Each dependency must be a dictionary")
                        return False
                        
                    if "from" not in dep or "to" not in dep:
                        logger.error("Dependencies must have 'from' and 'to' fields")
                        return False
                        
                    if dep["from"] not in task_ids or dep["to"] not in task_ids:
                        logger.error(f"Invalid task reference in dependency: {dep}")
                        return False

            return True

        except Exception as e:
            logger.error(f"Error validating workflow configuration: {str(e)}")
            return False

    def _make_config_serializable(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert config to a JSON-serializable format while preserving critical data."""
        try:
            if not isinstance(config, dict):
                return str(config)
                
            serializable = {}
            for key, value in config.items():
                if isinstance(value, dict):
                    serializable[key] = self._make_config_serializable(value)
                elif isinstance(value, list):
                    serializable[key] = [
                        self._make_config_serializable(item) if isinstance(item, dict)
                        else str(item) if hasattr(item, '__dict__')
                        else item
                        for item in value
                    ]
                elif hasattr(value, '__dict__'):
                    # Handle objects by converting to string representation
                    serializable[key] = str(value)
                else:
                    # Handle basic types directly
                    serializable[key] = value
            return serializable
        except Exception as e:
            logger.error(f"Error making config serializable: {str(e)}")
            raise

    async def execute_workflow(self, workflow_config: Dict[str, Any], workflow_id: str = None) -> Dict[str, Any]:
        """Create and execute a workflow with comprehensive tracking.

        Args:
            workflow_config: Workflow configuration dictionary

        Returns:
            Dict containing workflow execution results
        """
        try:
            # Log the incoming configuration type and content
            logger.info(f"Executing workflow with config type: {type(workflow_config)}")
            if isinstance(workflow_config, dict):
                logger.info(f"Config keys: {list(workflow_config.keys())}")
                if "tasks" in workflow_config:
                    logger.info(f"Tasks: {list(workflow_config['tasks'].keys())}")
            else:
                logger.error(f"Invalid config type: {type(workflow_config)}, value: {workflow_config}")
                
            # Create workflow first
            # workflow_id = await self.create_workflow(workflow_config)
            # logger.info(f"Created workflow with ID: {workflow_id}")
            
            # Ensure workflow is properly initialized
            if not workflow_id:
                logger.error("Failed to create workflow - no workflow ID returned")
                raise ValueError("Failed to create workflow - no workflow ID returned")
                
            if not self.engine.workflow_id:
                logger.warning(f"Engine workflow ID not set, setting to {workflow_id}")
                self.engine.workflow_id = workflow_id
                
            # Validate workflow graph
            if not self.engine.workflow_graph or not self.engine.workflow_graph.nodes:
                logger.error("Workflow graph is empty - no tasks added")
                raise ValueError("Workflow graph is empty - no tasks added")
                
            try:
                # Check for cycles in workflow graph
                cycles = list(nx.simple_cycles(self.engine.workflow_graph))
                if cycles:
                    logger.error(f"Workflow contains cycles: {cycles}")
                    raise ValueError(f"Workflow contains cycles: {cycles}")
            except Exception as graph_error:
                logger.error(f"Error validating workflow graph: {str(graph_error)}")
                raise
            
            # Execute workflow
            try:
                logger.info("Starting workflow execution")
                results = await self.engine.execute_workflow()
                logger.info("Workflow execution completed successfully")
                return await self._ensure_awaited(results)
            except Exception as exec_error:
                logger.error(f"Error executing workflow: {str(exec_error)}")
                raise
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            raise

    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get comprehensive workflow status.
        
        Returns:
            Dict[str, Any]: Workflow status
        """
        try:
            return await self.engine.get_workflow_status()
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {}

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed task status.
        
        Args:
            task_id: The task ID to get status for
            
        Returns:
            Dict[str, Any]: Task status
        """
        try:
            return await self.engine.get_task_status(task_id)
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return {}

    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow metrics.
        
        Args:
            workflow_id: The workflow ID to get metrics for
            
        Returns:
            Dict[str, Any]: Workflow metrics
        """
        try:
            return await self.engine.get_workflow_metrics(workflow_id)
        except Exception as e:
            logger.error(f"Error getting workflow metrics: {str(e)}")
            return {}

    async def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get comprehensive task metrics.
        
        Args:
            task_id: The task ID to get metrics for
            
        Returns:
            Dict[str, Any]: Task metrics
        """
        try:
            return await self.engine.get_task_metrics(task_id)
        except Exception as e:
            logger.error(f"Error getting task metrics for {task_id}: {str(e)}")
            return {}

    async def check_system_health(self) -> Dict[str, Any]:
        """Check health status of all components.

        Returns:
            Dict containing health status
        """
        return await self.engine.check_system_health()

    async def cleanup(self) -> None:
        """Cleanup resources used by the workflow builder."""
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
        """Ensure all coroutines in the data structure are awaited."""
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
