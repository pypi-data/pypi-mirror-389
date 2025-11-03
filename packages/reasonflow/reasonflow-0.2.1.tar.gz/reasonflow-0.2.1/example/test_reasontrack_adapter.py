"""Example to test ReasonTrack adapter functionality."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from zoneinfo import ZoneInfo

from reasonflow.observability import ReasonTrackAdapter
from reasonflow.observability.reasontrack_management_initializer import get_reasontrack_config
from reasontrack.core.alert_manager import AlertSeverity
from reasontrack.core.event_manager import EventStatus, EventType
from reasontrack.core.alert_manager import Alert
from reasontrack.core.metrics_collector import MetricType

import yaml
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use UTC timezone
UTC = ZoneInfo("UTC")

async def simulate_llm_task(tracker: ReasonTrackAdapter, task_id: str, workflow_id: str) -> str:
    """Simulate an LLM task with metrics.
    
    Args:
        tracker: ReasonTrack adapter instance
        task_id: Task ID (if None, will be auto-generated)
        workflow_id: Parent workflow ID
        
    Returns:
        str: The task ID (either provided or auto-generated)
    """
    start_time = datetime.now(UTC).timestamp()
    
    # Track task start
    task_id = await tracker.track_task(
        task_id=task_id,
        workflow_id=workflow_id,
        event_type=EventType.TASK.value,
        event_name="LLM Task",
        event_status=EventStatus.PROCESSING,
        source="reasonflow",
        data={
            "name": "llm_inference",
            "task_type": "llm",
            "start_time": datetime.now(UTC).isoformat(),
            "current_stage": "initialization",
            "stages_completed": [],
            "stages_remaining": ["tokenization", "inference", "post_processing"]
        }
    )
    
    # Simulate task execution time
    await asyncio.sleep(1)
    
    # Simulate LLM result data
    result = {
        "text": "This is a simulated LLM response",
        "metadata": {
            "provider": "OpenAI",
            "model": "gpt-4",
            "input_tokens": 150,
            "output_tokens": 50,
            "cost": 0.05,
            "memory_used": 1024,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "temperature": 0.7,
            "cache_hit": False
        }
    }
    
    duration = datetime.now(UTC).timestamp() - start_time
    
    # Track task completion with metrics
    await tracker.track_task(
        task_id=task_id,
        workflow_id=workflow_id,
        event_type=EventType.TASK.value,
        event_name="LLM Task",
        event_status=EventStatus.COMPLETED,
        source="reasonflow",
        data={
            "name": "llm_inference",
            "duration": duration,
            "end_time": datetime.now(UTC).isoformat(),
            "stages_completed": ["tokenization", "inference", "post_processing"],
            "stages_remaining": [],
            "progress": 100,
            "result": result,
            "metrics": {
                "llm": {
                    "provider": result["metadata"]["provider"],
                    "model": result["metadata"]["model"],
                    "input_tokens": result["metadata"]["input_tokens"],
                    "output_tokens": result["metadata"]["output_tokens"],
                    "cost": result["metadata"]["cost"],
                    "memory_used": result["metadata"]["memory_used"],
                    "prompt_tokens": result["metadata"]["prompt_tokens"],
                    "completion_tokens": result["metadata"]["completion_tokens"],
                    "temperature": result["metadata"]["temperature"],
                    "cache_hit": int(result["metadata"]["cache_hit"])
                }
            }
        }
    )
    
    return task_id, result

async def simulate_rag_task(tracker: ReasonTrackAdapter, task_id: str, workflow_id: str) -> str:
    """Simulate a RAG task with metrics.
    
    Args:
        tracker: ReasonTrack adapter instance
        task_id: Task ID (if None, will be auto-generated)
        workflow_id: Parent workflow ID
        
    Returns:
        str: The task ID (either provided or auto-generated)
    """
    start_time = datetime.now(UTC).timestamp()
    
    # Track task start
    task_id = await tracker.track_task(
        task_id=task_id,
        workflow_id=workflow_id,
        event_type=EventType.TASK.value,
        event_name="RAG Task",
        event_status=EventStatus.PROCESSING,
        source="reasonflow",
        data={
            "name": "rag_retrieval",
            "task_type": "rag",
            "start_time": datetime.now(UTC).isoformat(),
            "current_stage": "initialization",
            "stages_completed": [],
            "stages_remaining": ["embedding", "search", "reranking"]
        }
    )
    
    # Simulate task execution time
    await asyncio.sleep(0.5)
    
    # Simulate RAG result data
    result = {
        "documents": ["doc1", "doc2", "doc3"],
        "metadata": {
            "provider": "Weaviate",
            "embedding_model": "text-embedding-3-small",
            "embedding_provider": "OpenAI",
            "operation": "query",
            "latency": 0.15,
            "cost": 0.001,
            "cache_hit": False,
            "index_size": 10000,
            "num_dimensions": 1536,
            "num_results": 3,
            "hardware_info": {
                "gpu_memory_used": 512,
                "cpu_memory_used": 256,
                "num_threads": 4
            }
        }
    }
    
    duration = datetime.now(UTC).timestamp() - start_time
    
    # Track task completion with metrics
    await tracker.track_task(
        task_id=task_id,
        workflow_id=workflow_id,
        event_type=EventType.TASK.value,
        event_name="RAG Task",
        event_status=EventStatus.COMPLETED,
        source="reasonflow",
        data={
            "name": "rag_retrieval",
            "duration": duration,
            "end_time": datetime.now(UTC).isoformat(),
            "stages_completed": ["embedding", "search", "reranking"],
            "stages_remaining": [],
            "progress": 100,
            "result": result,
            "metrics": {
                "vectordb": {
                    "provider": result["metadata"]["provider"],
                    "embedding_model": result["metadata"]["embedding_model"],
                    "embedding_provider": result["metadata"]["embedding_provider"],
                    "operation": result["metadata"]["operation"],
                    "latency": result["metadata"]["latency"],
                    "cost": result["metadata"]["cost"],
                    "cache_hit": int(result["metadata"]["cache_hit"]),
                    "index_size": result["metadata"]["index_size"],
                    "num_dimensions": result["metadata"]["num_dimensions"],
                    "num_results": result["metadata"]["num_results"]
                },
                "hardware": result["metadata"]["hardware_info"]
            }
        }
    )
    
    return task_id, result

class TestReasonTrackAdapter:
    """Test class demonstrating ReasonTrack adapter capabilities."""

    def __init__(self):
        """Initialize the test adapter."""
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "config", "reasontrack.yaml")
        self.config = get_reasontrack_config(config_path)
        
        # Initialize tracker
        self.tracker = ReasonTrackAdapter(self.config)
    
  
    async def demonstrate_alert_management(self):
        """Demonstrate alert management capabilities."""
        logger.info("Demonstrating alert management...")
        
        try:
            # Create critical alert
            alert_id = str(uuid.uuid4())
            alert_data = Alert(
                alert_id=alert_id,
                alert_name="Critical System Issue",
                alert_message="Database connection lost",
                alert_source="system_monitor",
                severity=AlertSeverity.CRITICAL.value,
                metadata={
                    "component": "database",
                    "impact": "high"
                },
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            await self.tracker.alert_manager.trigger_alert(alert_data)
            logger.info(f"Created alert: {alert_id}")

        except Exception as e:
            logger.error(f"Error in alert management: {str(e)}")
            raise

    async def demonstrate_event_tracking(self):
        """Demonstrate event tracking capabilities."""
        logger.info("Demonstrating event tracking...")
        
        try:
            # Create and track an event
            event_id = await self.tracker.track_system_event(
                event_name="User Login",
                metadata={
                    "user_id": "test_user",
                    "ip_address": "127.0.0.1"
                }
            )
            logger.info(f"Created event: {event_id}")

        except Exception as e:
            logger.error(f"Error in event tracking: {str(e)}")
            raise

    async def demonstrate_workflow_tracking(self):
        """Demonstrate workflow tracking capabilities."""
        logger.info("Demonstrating workflow tracking...")
        
        try:
            start_time = datetime.now(UTC)
            
            # Start workflow
            workflow_id = await self.tracker.track_workflow(
                workflow_id=None,  # Auto-generate ID
                event_type=EventType.WORKFLOW.value,
                event_name='Workflow1',
                event_status=EventStatus.PROCESSING,
                source="reasonflow",
                data={
                    "version": "1.0.0",
                    "total_tasks": 2,  # LLM and RAG tasks
                    "metadata": {
                        "type": "test_workflow",
                        "owner": "system",
                        "priority": "medium",
                        "tags": ["test", "llm", "rag"]
                    },
                    "start_time": start_time.isoformat()
                }
            )
            logger.info(f"Created workflow with ID: {workflow_id}")
            
            # Write initial workflow metrics
            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="workflow_progress",
                value=0.0,
                tags={
                    "workflow_id": workflow_id,
                    "status": EventStatus.PROCESSING.value,
                    "type": "test_workflow"
                },
                timestamp=start_time
            )
            
            # Simulate LLM task
            logger.info("\nSimulating LLM task...")
            llm_task_id, llm_result = await simulate_llm_task(self.tracker, None, workflow_id)
            logger.info(f"Completed LLM task with ID: {llm_task_id}")
            logger.info(f"LLM result: {llm_result}")
            
            # Write LLM task completion metrics
            # await self.tracker.metrics_collector.record_metric(
            #     metric_type=MetricType.GAUGE,
            #     name="workflow_progress",
            #     value=50.0,  # 1 of 2 tasks completed
            #     tags={
            #         "workflow_id": workflow_id,
            #         "status": EventStatus.PROCESSING.value,
            #         "type": "test_workflow"
            #     },
            #     timestamp=datetime.now(UTC)
            # )
            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.COUNTER,
                name="llm_output_tokens",
                value=llm_result["metadata"]["output_tokens"],
                tags={"task_id": llm_task_id, "model": llm_result["metadata"]["model"]},
                timestamp=datetime.now(UTC)
            )

            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="llm_memory_used",
                value=llm_result["metadata"]["memory_used"],
                tags={"task_id": llm_task_id},
                timestamp=datetime.now(UTC)
            )

            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="llm_cost",
                value=llm_result["metadata"]["cost"],
                tags={"task_id": llm_task_id},
                timestamp=datetime.now(UTC)
            )
            # Simulate RAG task
            logger.info("\nSimulating RAG task...")
            rag_task_id, rag_result = await simulate_rag_task(self.tracker, None, workflow_id)
            logger.info(f"Completed RAG task with ID: {rag_task_id}")
            logger.info(f"RAG result: {rag_result}")
            # Write RAG task completion metrics
            # await self.tracker.metrics_collector.record_metric(
            #     metric_type=MetricType.GAUGE,
            #     name="workflow_progress",
            #     value=100.0,  # 2 of 2 tasks completed
            #     tags={
            #         "workflow_id": workflow_id,
            #         "status": EventStatus.PROCESSING.value,
            #         "type": "test_workflow"
            #     },
            #     timestamp=datetime.now(UTC)
            # )
            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.HISTOGRAM,
                name="rag_latency",
                value=rag_result["metadata"]["latency"],
                tags={"task_id": rag_task_id, "provider": rag_result["metadata"]["provider"]},
                timestamp=datetime.now(UTC)
            )

            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="rag_cost",
                value=rag_result["metadata"]["cost"],
                tags={"task_id": rag_task_id},
                timestamp=datetime.now(UTC)
            )

            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="rag_gpu_memory",
                value=rag_result["metadata"]["hardware_info"]["gpu_memory_used"],
                tags={"task_id": rag_task_id},
                timestamp=datetime.now(UTC)
            )
            
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()
            
            # Complete workflow
            await self.tracker.track_workflow(
                workflow_id=workflow_id,
                event_type=EventType.WORKFLOW.value,
                event_name='Workflow1',
                event_status=EventStatus.COMPLETED,
                source="reasonflow",
                data={
                    "completed_tasks": 2,
                    "duration": duration,
                    "metadata": {
                        "task_ids": [llm_task_id, rag_task_id],
                        "end_time": end_time.isoformat()
                    }
                }
            )
            logger.info("Successfully completed workflow")
            
            # Write final workflow metrics
            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="workflow_duration",
                value=duration,
                tags={
                    "workflow_id": workflow_id,
                    "status": EventStatus.COMPLETED.value,
                },
                timestamp=end_time
            )
            
            # Write task success rate
            await self.tracker.metrics_collector.record_metric(
                metric_type=MetricType.GAUGE,
                name="workflow_success_rate",
                value=100.0,  # Both tasks completed successfully
                tags={
                    "workflow_id": workflow_id,
                    "status": EventStatus.COMPLETED.value,
                },
                timestamp=end_time
            )
            
            # Get metrics with proper time range
            logger.info("\nRetrieving metrics from InfluxDB...")
            
            # Query workflow metrics
            workflow_metrics = await self.tracker.metrics_collector.get_metrics(
                names=["workflow_duration", "workflow_success_rate", "workflow_progress"],
                start_time=start_time,
                end_time=end_time,
                tags={"workflow_id": workflow_id}
            )
            
            # Query LLM metrics
            llm_metrics = await self.tracker.metrics_collector.get_metrics(
                names=["llm_output_tokens", "llm_memory_used", "llm_cost"],
                start_time=start_time,
                end_time=end_time,
                tags={"task_id": llm_task_id}
            )
            
            # Query RAG metrics
            rag_metrics = await self.tracker.metrics_collector.get_metrics(
                names=["rag_latency", "rag_cost", "rag_gpu_memory"],
                start_time=start_time,
                end_time=end_time,
                tags={"task_id": rag_task_id}
            )
            
            logger.info("\nWorkflow Metrics:")
            for name, values in workflow_metrics.items():
                logger.info(f"{name}: {values}")
                
            logger.info("\nLLM Task Metrics:")
            for name, values in llm_metrics.items():
                logger.info(f"{name}: {values}")
                
            logger.info("\nRAG Task Metrics:")
            for name, values in rag_metrics.items():
                logger.info(f"{name}: {values}")

        except Exception as e:
            logger.error(f"Error in workflow tracking: {str(e)}")
            raise

    async def check_system_health(self):
        """Check system health status."""
        logger.info("Checking system health...")
        
        try:
            health_status = await self.tracker.check_system_health()
            logger.info(f"System health status: {health_status}")
            
            # Print detailed component status
            components = health_status.get("components", {})
            for component, status in components.items():
                status_str = status.get("status", "unknown")
                symbol = "✓" if status_str == "healthy" else "✗"
                logger.info(f"{component}: {symbol} - {status_str}")
                if status.get("error"):
                    logger.info(f"  Error: {status['error']}")

        except Exception as e:
            logger.error(f"Error checking system health: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup all resources."""
        logger.info("Cleaning up resources...")
        try:
            await self.tracker.cleanup()
            logger.info("Successfully cleaned up all resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

async def main():
    """Run the test adapter example."""
    example = TestReasonTrackAdapter()
    
    try:
        # Test Alert Management
        print("\n=== Testing Alert Management ===")
        await example.demonstrate_alert_management()
        
        # Test Event Tracking
        print("\n=== Testing Event Tracking ===")
        await example.demonstrate_event_tracking()
        
        # Test Workflow Tracking
        print("\n=== Testing Workflow Tracking ===")
        await example.demonstrate_workflow_tracking()
        
        # Test System Health
        print("\n=== Testing System Health ===")
        #await example.check_system_health()
        
    except Exception as e:
        logger.error(f"Error running test example: {str(e)}")
        raise
    finally:
        await example.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 