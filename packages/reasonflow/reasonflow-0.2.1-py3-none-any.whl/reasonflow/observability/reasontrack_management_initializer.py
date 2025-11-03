"""Management examples initializer for ReasonTrack.

This module provides a centralized initialization for all management examples:
- Alert Management
- Archive Management
- Event Tracking
- Health Check
- State Management
- Time Series Management
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from reasontrack.integrations.prometheus_integration import PrometheusIntegration
from reasontrack.core.alert_manager import AlertManager, Alert, AlertSeverity, AlertStatus
from reasontrack.core.health_checker import HealthChecker, HealthStatus
from reasontrack.core.state_manager import StateManager
from reasontrack.core.event_manager import EventManager, EventType, EventStatus
from reasontrack.storage.alert_store import AlertStorage, AlertStorageConfig
from reasontrack.storage.archive_store import BaseArchiveStorage, ElasticsearchArchiveStorage, ArchiveStorageConfig
from reasontrack.storage.event_store import EventStorage, EventStorageConfig
from reasontrack.storage.state_store import StateStorage, StateStorageConfig
from reasontrack.storage.metrics_store import MetricStorage, MetricStorageConfig
from reasontrack.core.metrics_collector import MetricsCollector, MetricsConfig
from reasontrack.core.version_manager import VersionManager
from reasontrack.storage.version_store import VersionStorage, VersionStorageConfig
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
PROMETHEUS_PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY", "http://localhost:9091")
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RETENTION_DAYS = 30
BATCH_SIZE = 100


class ManagementInitializer:
    """Initializer for all management components."""

    def __init__(self, config: dict):
        """Initialize management components."""
        # Initialize Prometheus integration
        self.config = config
        self.prometheus = PrometheusIntegration(
            pushgateway_url=PROMETHEUS_PUSHGATEWAY
        )
        
        # Initialize storages
        self.alert_storage = self._init_alert_storage()
        self.archive_storage = self._init_archive_storage()
        self.event_storage = self._init_event_storage()
        self.state_storage = self._init_state_storage()
        self.metric_storage = self._init_metric_storage()
        self.metrics_collector = self._init_metrics_collector()
        self.version_storage = self._init_version_storage()
        # Initialize managers
        self.alert_manager = self._init_alert_manager()
        self.event_manager = self._init_event_manager()
        self.state_manager = self._init_state_manager()
        self.health_checker = self._init_health_checker()
        self.version_manager = self._init_version_manager()
        
        # Initialize metrics
        self._init_metrics()

    def _init_alert_storage(self) -> AlertStorage:
        """Initialize alert storage."""
        config = AlertStorageConfig(
            backend="prometheus",
            retention_days=RETENTION_DAYS,
            compression=True,
            batch_size=BATCH_SIZE,
            pushgateway_url=PROMETHEUS_PUSHGATEWAY
        )
        return AlertStorage(config=config)

    def _init_archive_storage(self) -> BaseArchiveStorage:
        """Initialize archive storage."""
        config = ArchiveStorageConfig(
            backend="elasticsearch",
            url=ELASTICSEARCH_URL,
            index_prefix="reasontrack_archive",
            retention_days=RETENTION_DAYS
        )
        return ElasticsearchArchiveStorage(config=config)

    def _init_event_storage(self) -> EventStorage:
        """Initialize event storage."""
        event_config = self.config.get("storage", {}).get("events", {})
        kafka_config = self.config.get("kafka", {})
        config = EventStorageConfig(
            backend=event_config.get("backend"),
            storage_path=event_config.get("path"),
            retention_days=RETENTION_DAYS,
            kafka_config=kafka_config
        )
        return EventStorage(config=config)

    def _init_state_storage(self) -> StateStorage:
        """Initialize state storage."""
        state_config = self.config.get("storage", {}).get("state", {})
        redis_config = self.config.get("redis", {})
        config = StateStorageConfig(
            backend=state_config.get("backend"),
            prefix='state',
            ttl=86400,
            redis_config=redis_config
        )
        return StateStorage(config=config)

    def _init_metric_storage(self) -> MetricStorage:
        """Initialize metric storage."""
        metric_config = self.config.get("storage", {}).get("metrics", {})
        print(metric_config)
        config = MetricStorageConfig(
            backend=metric_config.get("backend"),
            url=metric_config.get("url"),
            token=metric_config.get("token"),
            org=metric_config.get("org"),
            bucket=metric_config.get("bucket"),
            retention_days=RETENTION_DAYS,
            # pushgateway_url=PROMETHEUS_PUSHGATEWAY
        )
        print(config)
        return MetricStorage(config=config)
    
    def _init_metrics_collector(self) -> MetricsCollector:
        """Initialize metrics collector."""
        return MetricsCollector(
            config=MetricsConfig(),
            storage=self.metric_storage
        )
    
    def _init_version_storage(self) -> VersionStorage:
        """Initialize version storage."""
        return VersionStorage(
            config=VersionStorageConfig()
        )
    
    def _init_version_manager(self) -> VersionManager:
        """Initialize version manager."""
        return VersionManager(
            storage=self.version_storage
        )

    def _init_alert_manager(self) -> AlertManager:
        """Initialize alert manager."""
        return AlertManager(
            storage=self.alert_storage,
            retention_days=RETENTION_DAYS
        )

    def _init_event_manager(self) -> EventManager:
        """Initialize event manager."""
        return EventManager(
            storage=self.event_storage,
        )

    def _init_state_manager(self) -> StateManager:
        """Initialize state manager."""
        return StateManager(
            storage=self.state_storage
        )

    def _init_health_checker(self) -> HealthChecker:
        """Initialize health checker."""
        health_config = {
            "kafka": {
                "broker_url": self.config.get("kafka", {}).get("broker_url", "localhost:9092"),
                "topic_prefix": "reasontrack",
                "client_id": "reasontrack-health",
                "group_id": "reasontrack-health-group"
            },
            "elasticsearch": {
                "hosts": [self.config.get("storage", {}).get("archive", {}).get("url", "http://localhost:9200")],
                "index_prefix": "reasontrack",
                "verify_certs": False
            },
            "redis": {
                "url": self.config.get("redis", {}).get("url", "redis://localhost:6379/0"),
                "prefix": "reasontrack"
            },
            "prometheus": {
                "port": PROMETHEUS_PORT,
                "pushgateway": PROMETHEUS_PUSHGATEWAY,
                "job_name": "reasontrack_health"
            },
            "opentelemetry": {
                "endpoint": self.config.get("telemetry", {}).get("tracing", {}).get("endpoint", "http://localhost:4317")
            }
        }
        return HealthChecker(config=health_config)

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        # Counter for total events by type and status
        self.event_counter = self.prometheus.create_counter(
            name="reasontrack_events_total",
            description="Total number of events by type and status",
            labels=["event_type", "status"]
        )

        # Counter for total alerts by severity and status
        self.alert_counter = self.prometheus.create_counter(
            name="reasontrack_alerts_total",
            description="Total number of alerts by severity and status",
            labels=["severity", "status", "source", "category"]
        )

        # Gauge for active alerts by severity
        self.active_alerts = self.prometheus.create_gauge(
            name="reasontrack_active_alerts",
            description="Number of currently active alerts",
            labels=["severity", "source", "category"]
        )

        # Gauge for system metrics
        self.system_metrics = self.prometheus.create_gauge(
            name="reasontrack_system_metrics",
            description="System metrics for monitoring",
            labels=["metric_name", "resource_type"]
        )

        # Histogram for event processing times
        self.event_processing_time = self.prometheus.create_histogram(
            name="reasontrack_event_processing_seconds",
            description="Time taken to process events",
            labels=["event_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        # Histogram for alert resolution times
        self.alert_resolution_time = self.prometheus.create_histogram(
            name="reasontrack_alert_resolution_seconds",
            description="Time taken to resolve alerts",
            labels=["severity"],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800, 86400]
        )

    async def cleanup(self):
        """Cleanup all resources."""
        try:
            # Close storage connections
            await self.alert_storage.close()
            await self.archive_storage.close()
            await self.event_storage.close()
            await self.state_storage.close()
            await self.metric_storage.close()

            # Close Prometheus connection
            await self.prometheus.close()

            logger.info("Successfully cleaned up all resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

def get_reasontrack_config(config_path: str) -> dict:
        """Get ReasonTrack configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            dict: Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
        """
        config_path = os.path.expanduser(config_path)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.info(f"Loading config from: {config_path}")
        
        # Load and parse YAML config
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Process environment variables
        def process_env_vars(data):
            if isinstance(data, dict):
                return {k: process_env_vars(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [process_env_vars(item) for item in data]
            elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
                env_var = data[2:-1]
                value = os.getenv(env_var)
                if value is None:
                    logger.warning(f"Environment variable {env_var} not set")
                    return ''
                if ',' in value:  # Handle comma-separated lists
                    return value.split(',')
                return value
            return data
        
        return process_env_vars(config)

async def main():
    """Run a test of the management initializer."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "reasontrack.yaml")
    config = get_reasontrack_config(config_path)
    initializer = ManagementInitializer(config=config)

    
    
    await initializer.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 