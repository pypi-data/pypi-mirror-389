from typing import Dict, Any, Optional
import logging
import os
from reasonflow.observability.basic_tracker import BasicTracker
from reasonflow.observability.reasontrack_adapter import ReasonTrackAdapter
from reasonflow.observability.tracking_interface import TrackingInterface
from reasontrack.storage.state_store import StateStorage
from reasontrack import (
    EventManager,
    MetricsCollector, 

)
from reasontrack.core.metrics_config import (
    MetricsConfig,
    LLMConfig,
    VectorDBConfig,
    TaskConfig,
)
from reasontrack.core.config_validator import ConfigValidator, ReasonTrackConfig
from reasontrack.storage.event_store import EventStorage, EventStorageConfig
from reasontrack.storage.metrics_store import MetricStorage, MetricStorageConfig
from reasontrack.storage.alert_store import AlertStorage, AlertStorageConfig
from reasontrack.storage.state_store import StateStorageConfig

import yaml

logger = logging.getLogger(__name__)

# Define constants at the top
DEFAULT_RETENTION_DAYS = 30
DEFAULT_STORAGE_PATH = "./storage"
DEFAULT_BACKEND = "memory"
STORAGE_PATHS = {
    "events": f"{DEFAULT_STORAGE_PATH}/events",
    "states": f"{DEFAULT_STORAGE_PATH}/states"
}

class TrackerFactory:
    """Factory for creating and configuring trackers with enhanced functionality."""

    @staticmethod
    def validate_config(tracker_type: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Validate tracker configuration with comprehensive checks.

        Args:
            tracker_type: Type of tracker to validate config for
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        if tracker_type == "reasontrack":
            if not config:
                raise ValueError("ReasonTrack requires configuration")
            
            try:
                # Validate using ConfigValidator and Pydantic model
                ConfigValidator.validate_config(config)
                ReasonTrackConfig(**config)  # Additional validation through Pydantic
                logger.debug("ReasonTrack configuration validated successfully")
            except Exception as e:
                logger.error(f"Invalid ReasonTrack configuration: {str(e)}")
                raise ValueError(f"Invalid ReasonTrack configuration: {str(e)}")

    @staticmethod
    def _create_reasontrack_components(config: Dict[str, Any]):
        try:
            # Initialize event storage and manager
            event_config = EventStorageConfig(
                backend=config.get("event_manager", {}).get("backend", DEFAULT_BACKEND),
                retention_days=config.get("event_manager", {}).get("retention_days", DEFAULT_RETENTION_DAYS),
                kafka_config=config.get("event_manager", {}).get("kafka_config", {})
            )
            event_storage = EventStorage(config=event_config)
            event_manager = EventManager(storage=event_storage)
            logger.debug("Event manager initialized")

            # Initialize state storage with config values
            state_config = StateStorageConfig(
                backend=config.get("state_manager", {}).get("backend", DEFAULT_BACKEND),
                retention_days=config.get("state_manager", {}).get("retention_days", DEFAULT_RETENTION_DAYS),
                storage_path=config.get("state_manager", {}).get("storage_path", STORAGE_PATHS["states"]),
                prefix=config.get("state_manager", {}).get("prefix", "reasontrack_state_"),
                ttl=config.get("state_manager", {}).get("ttl", 3600),
                redis_config=config.get("state_manager", {}).get("redis_config", {})
            )
            state_storage = StateStorage(config=state_config)
            logger.debug("State storage initialized")

            # Initialize metrics configuration
            metrics_config = config.get("metrics_config")
            if not metrics_config:
                metrics_config = MetricsConfig(
                    llm=LLMConfig(**config.get("llm", {})),
                    vectordb=VectorDBConfig(**config.get("vectordb", {})),
                    task=TaskConfig(**config.get("task", {})),
                    enable_cost_alerts=config.get("enable_cost_alerts", True),
                    cost_threshold=config.get("cost_threshold", 1.0)
                )
            logger.debug("Metrics config initialized")

            return event_manager, state_storage, metrics_config
        except Exception as e:
            logger.error(f"Failed to create ReasonTrack components: {str(e)}")
            raise

    @staticmethod
    def create_tracker(
        tracker_type: str = "basic",
        config: Optional[Dict[str, Any]] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ) -> TrackingInterface:
        """Create a tracker instance based on type and configuration.
        
        Args:
            tracker_type: Type of tracker to create ("basic" or "reasontrack")
            config: Configuration for the tracker
            metrics_collector: Optional metrics collector to use
            
        Returns:
            TrackingInterface: The created tracker instance
        """
        logger.info(f"Creating tracker of type: {tracker_type}")
        
        try:
            if tracker_type.lower() == "reasontrack":
                logger.info("Initializing ReasonTrack tracker with enhanced functionality")
                
                if not config:
                    logger.error("Configuration required for ReasonTrack tracker")
                    raise ValueError("Configuration required for ReasonTrack")

                # Validate configuration
                TrackerFactory.validate_config(tracker_type, config)
                logger.debug("Configuration validated successfully")
    
                # Create components with proper configuration
                event_manager, state_storage, metrics_config = TrackerFactory._create_reasontrack_components(config)
                logger.debug("Components created successfully")
                
                tracker = ReasonTrackAdapter(
                    event_manager=event_manager,
                    state_manager=state_storage,
                    metrics_config=metrics_config,
                    config_path=config.get("config_path")
                )
                logger.info("Successfully created ReasonTrack tracker")
                return tracker
            
            elif tracker_type.lower() == "basic":
                logger.info("Creating basic tracker")
                return BasicTracker(metrics_collector=metrics_collector)
            
            else:
                logger.warning(f"Unknown tracker type: {tracker_type}, falling back to basic tracker")
                return BasicTracker(metrics_collector=metrics_collector)
                
        except Exception as e:
            logger.error(f"Error creating {tracker_type} tracker: {str(e)}")
            logger.warning("Falling back to basic tracker due to error")
            return BasicTracker(metrics_collector=metrics_collector)