import os
from dotenv import load_dotenv
import asyncio
from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasontrack import (
    RuntimeMode,
    HardwareType,
    MetricsConfig,
    LLMConfig,
    VectorDBConfig,
    TaskConfig,
)
from reasonchain.memory import SharedMemory
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta
import logging
from fastapi import WebSocket
from reasonflow.integrations.websocket_integration import notifier

# Mock WebSocket for testing
class MockWebSocket:
    async def accept(self):
        print("WebSocket connection accepted")
        
    async def send_json(self, data: dict):
        print("\n🔔 WebSocket Message Sent:")
        print(json.dumps(data, indent=2))
        
    async def close(self):
        print("WebSocket connection closed")

# Add WebSocket debugging
class WebSocketDebugger:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.task_notifications = []
        self.workflow_notifications = []
        self.mock_websocket = MockWebSocket()
        
    async def setup_connection(self):
        """Setup WebSocket connection"""
        try:
            await notifier.connect(self.mock_websocket, self.client_id)
            print(f"\n🔌 WebSocket connection established for client: {self.client_id}")
        except Exception as e:
            print(f"Error setting up WebSocket connection: {str(e)}")
            
    async def cleanup_connection(self):
        """Cleanup WebSocket connection"""
        try:
            notifier.disconnect(self.client_id)
            await self.mock_websocket.close()
            print(f"\n🔌 WebSocket connection closed for client: {self.client_id}")
        except Exception as e:
            print(f"Error cleaning up WebSocket connection: {str(e)}")
        
    def log_notification(self, notification_type: str, data: dict):
        timestamp = datetime.now(timezone.utc).isoformat()
        formatted_data = {
            "timestamp": timestamp,
            "client_id": self.client_id,
            "type": notification_type,
            "data": data
        }
        
        if notification_type == "task_completion":
            self.task_notifications.append(formatted_data)
            print("\n🔔 Task Notification:")
            print(json.dumps(formatted_data, indent=2))
        elif notification_type == "workflow_completion":
            self.workflow_notifications.append(formatted_data)
            print("\n🔔 Workflow Notification:")
            print(json.dumps(formatted_data, indent=2))
            
    def print_summary(self):
        print("\n📊 WebSocket Notification Summary:")
        print(f"Total Task Notifications: {len(self.task_notifications)}")
        print(f"Total Workflow Notifications: {len(self.workflow_notifications)}")
        
        if self.task_notifications:
            print("\nTask Notification Timeline:")
            for notif in self.task_notifications:
                status = notif["data"]["status"]
                task_id = notif["data"]["task_id"]
                emoji = "✅" if status == "completed" else "❌"
                print(f"{emoji} [{notif['timestamp']}] Task {task_id}: {status}")
                
        if self.workflow_notifications:
            print("\nWorkflow Notification Timeline:")
            for notif in self.workflow_notifications:
                status = notif["data"]["status"]
                workflow_id = notif["data"]["workflow_id"]
                emoji = "✅" if status == "completed" else "❌"
                print(f"{emoji} [{notif['timestamp']}] Workflow {workflow_id}: {status}")

# Monkey patch the WebSocket notifier to add debugging
from reasonflow.integrations.websocket_integration import notifier

original_notify_task = notifier.notify_task_completion
original_notify_workflow = notifier.notify_workflow_completion

websocket_debugger = None

async def debug_notify_task(client_id: str, task_data: dict):
    if websocket_debugger:
        websocket_debugger.log_notification("task_completion", task_data)
    await original_notify_task(client_id, task_data)

async def debug_notify_workflow(client_id: str, workflow_data: dict):
    if websocket_debugger:
        websocket_debugger.log_notification("workflow_completion", workflow_data)
    await original_notify_workflow(client_id, workflow_data)

notifier.notify_task_completion = debug_notify_task
notifier.notify_workflow_completion = debug_notify_workflow

logger = logging.getLogger(__name__)
# Load environment variables from .env file
load_dotenv()


# Initialize ReasonFlow components
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

def build_workflow(llm_extractor, llm_analyzer, llm_summarizer, shared_memory):
    """Build workflow configuration with enhanced metrics tracking"""
    workflow_config = {
        
        "tasks": {
            "download-document": {
                "type": "browser",
                "config": {
                    "url": "https://ir.tesla.com/financial-information/quarterly-results",
                    "actions": [
                        {
                            "action": "navigate",
                            "url": "https://ir.tesla.com/financial-information/quarterly-results"
                        },
                        {
                            "action": "extract_data",
                            "selectors": {
                                "q3_link": "a.tds-link[href*='TSLA-Q3-2024-Update.pdf']"
                                },
                                "extract_attributes": {
                                    "q3_link": ["href"]
                                }
                            
                        },
                        {
                            "action": "validate",
                            "config": {
                                "input": "${extracted_data.data.q3_link.href}",
                                "validation_type": "url",
                                "pattern": ".*\\.pdf$"
                            }
                        },
                        {
                            "action": "download",
                            "config": {
                                "url": "${validated_url}",
                                "download_path": "./data",
                                "filename": "tesla_q3_2024.pdf"
                            }
                        }
                    ]
                }
            },
            "ingest-document": {
                "type": "data_ingestion",
                "config": {
                    "agent_config": {
                        "db_path": "vector_db_tesla.index",
                        "db_type": "faiss",
                        "embedding_provider": "sentence_transformers",
                        "embedding_model": "all-MiniLM-L6-v2",
                        "shared_memory": shared_memory
                    },
                    "params": {
                        "file_paths": ["./data/tesla_q3_2024.pdf"]
                    }
                }
            },
            "retrieve-document": {
                "type": "data_retrieval",
                "config": {
                    "agent_config": {
                        "db_path": "vector_db_tesla.index",
                        "db_type": "faiss",
                        "embedding_provider": "sentence_transformers",
                        "embedding_model": "all-MiniLM-L6-v2",
                        "use_gpu": True,
                        "shared_memory": shared_memory
                    },
                    "params": {
                        "query": "Retrieve Tesla Q3 2024 financial data",
                        "top_k": 5
                    }
                }
            },
            "extract-highlights": {
                "type": "llm",
                "config": {
                    "agent": llm_extractor,
                    "params": {
                        "prompt": """Extract key financial highlights from the following data: 
                        {{retrieve-document.output}}
                        
                        Format your response as a bulleted list of the most important financial metrics and findings."""
                    }
                }
            },
            "analyze-trends": {
                "type": "llm",
                "config": {
                    "agent": llm_analyzer,
                    "params": {
                        "prompt": """Analyze the financial trends from these highlights:
                        {{extract-highlights.output}}
                        
                        Focus on:
                        - Revenue growth trends
                        - Profitability metrics
                        - Cash flow patterns
                        - Key business segments performance"""
                    }
                }
            },
            "summarize-insights": {
                "type": "llm",
                "config": {
                    "agent": llm_summarizer,
                    "params": {
                        "prompt": """Provide a concise executive summary of these financial trends:
                        {{analyze-trends.output}}
                        
                        Include:
                        1. Overall financial health
                        2. Key growth indicators
                        3. Risk factors
                        4. Future outlook"""
                    }
                }
            }
        
        },
        "dependencies": [
            {"from": "download-document", "to": "ingest-document"},
            {"from": "ingest-document", "to": "retrieve-document"},
            {"from": "retrieve-document", "to": "extract-highlights"},
            {"from": "extract-highlights", "to": "analyze-trends"},
            {"from": "analyze-trends", "to": "summarize-insights"}
        ]
    }
    return workflow_config

async def print_task_status(engine, task_id, start_time, end_time):
    """Print task status with proper async handling."""
    try:
        status = await engine.get_task_status(task_id, start_time, end_time)
        print(f"\n{task_id}:")
        print(json.dumps(status, indent=2))
    except Exception as e:
        print(f"\n{task_id}:")
        print(f"Error getting task status: {str(e)}")

async def print_workflow_status(engine, workflow_id, start_time, end_time):
    """Print workflow status with proper async handling."""
    try:
        status = await engine.get_workflow_status(workflow_id, start_time, end_time)
        print("\nWorkflow Metrics:")
        print(json.dumps(status, indent=2))
    except Exception as e:
        print("\nWorkflow Metrics:")
        print(f"Error getting workflow status: {str(e)}")
def serialize_metrics(metrics):
    """Convert datetime objects in metrics to ISO 8601 strings."""
    if isinstance(metrics, dict):
        return {k: serialize_metrics(v) for k, v in metrics.items()}
    elif isinstance(metrics, list):
        return [serialize_metrics(v) for v in metrics]
    elif isinstance(metrics, datetime):
        return metrics.isoformat()  # Convert datetime to string
    return metrics
async def print_task_metrics(engine, task_id, start_time, end_time):
    """Print task metrics with proper async handling."""
    try:
        metrics = await engine.get_task_metrics(task_id, start_time, end_time)
        print(f"\nTask Metrics for {task_id}:")

        print(json.dumps(metrics, indent=2, default=serialize_metrics))
    except Exception as e:
        print(f"\nError getting task metrics for {task_id}: {str(e)}")

async def print_workflow_metrics(engine, workflow_id, start_time, end_time):
    """Print workflow metrics with proper async handling."""
    try:
        metrics = await engine.get_workflow_metrics(workflow_id, start_time, end_time)
        print("\nWorkflow Metrics:")
        print(json.dumps(metrics, indent=2, default=serialize_metrics))
    except Exception as e:
        print(f"\nError getting workflow metrics: {str(e)}")

async def main():
    print("Starting Advanced Tracking Example...")
    
    # Initialize components
    config_path = os.path.join(os.path.dirname(__file__), "config", "reasontrack.yaml")
    print(f"Loading config from: {config_path}")
    
    config = get_reasontrack_config(config_path)
    shared_memory = SharedMemory()
    task_manager = TaskManager(shared_memory=shared_memory)

    # Initialize metrics configuration
    metrics_config = MetricsConfig(
        task=TaskConfig(
            track_duration=True,
            track_memory=True,
            track_cpu=True,
            track_gpu=True,
            hardware_type=HardwareType.GPU
        ),
        llm=LLMConfig(
            track_tokens=True,
            track_cost=True,
            track_latency=True,
            track_hardware=True
        ),
        vectordb=VectorDBConfig(
            track_query_time=True,
            track_latency=True,
            track_embedding_time=True,
            runtime_mode=RuntimeMode.LOCAL
        ),
        enable_real_time=True,
        enable_cost_alerts=True,
        cost_threshold=1.0,
        sampling_interval=1.0
    )

    # Initialize WebSocket debugger
    global websocket_debugger
    client_id = "debug-client-1234"
    websocket_debugger = WebSocketDebugger(client_id)
    
    # Setup WebSocket connection
    await websocket_debugger.setup_connection()
    print(f"\n🔌 WebSocket Debugging Enabled for client: {client_id}")
    tracker = 'basic' #'reasontrack'
    workflow_builder = WorkflowBuilder(
        task_manager=task_manager, 
        tracker_type=tracker, 
        tracker_config=config,
        metrics_config=metrics_config,
        config_path=config_path,
        client_id=None  # Initially no WebSocket notifications
    )

    # Add document to the vector database
    # rag_integration = RAGIntegration(
    #         db_path="vector_db_tesla.index",
    #         db_type="faiss",
    #         embedding_provider="sentence_transformers",
    #         embedding_model="all-MiniLM-L6-v2",
    #         shared_memory=shared_memory
    # )
    # rag_integration.add_documents(file_paths=["tsla-20240930-gen.pdf"])
    # print("Document added to vector database.")
    
    # Create agents
    llm_extractor = LLMIntegration(provider="openai", model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    llm_analyzer = LLMIntegration(provider="ollama", model="llama3.1:latest", api_key=None)
    llm_summarizer = LLMIntegration(provider="groq", model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

    # Build workflow
    workflow_config = build_workflow(llm_extractor, llm_analyzer, llm_summarizer, shared_memory)
   
    # Create workflow
    try:
        # Create workflow
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        print(json.dumps(workflow_config, indent=2, default=str))
        
        # Enable WebSocket notifications before workflow creation/execution
        workflow_builder.client_id = client_id
        workflow_id = await workflow_builder.create_workflow(workflow_config)
        print(f"Workflow created with ID: {workflow_id}")
        
        results = await workflow_builder.execute_workflow(workflow_config, workflow_id=workflow_id)
        

        print("\n=== Workflow Execution Results ===")
        for task_id, result in results.items():
            print(f"\nTask {task_id}:")
            print(json.dumps(result, indent=2, default=serialize_metrics))
            await print_task_metrics(workflow_builder.engine, task_id, start_time, end_time)

        await print_workflow_metrics(workflow_builder.engine, workflow_id, start_time, end_time)

        # Print performance analysis
        print("\n=== Performance Analysis ===")
        # bottlenecks = workflow_builder.engine.metrics_collector.analyze_bottlenecks(workflow_id)
        # if bottlenecks:
        #     print("\nBottlenecks Detected:")
        #     print(json.dumps(bottlenecks, indent=2))

        # cost_analysis = workflow_builder.engine.metrics_collector.analyze_costs(workflow_id)
        # print("\nCost Analysis:")
        # print(json.dumps(cost_analysis, indent=2))

        # Print WebSocket notification summary at the end
        print("\n=== WebSocket Notification Summary ===")
        websocket_debugger.print_summary()

    except Exception as e:
        print(f"Error executing workflow: {str(e)}")
        # Still print WebSocket summary even if there's an error
        print("\n=== WebSocket Notification Summary (After Error) ===")
        websocket_debugger.print_summary()
        raise
    
    finally:
        # Cleanup WebSocket connection
        await websocket_debugger.cleanup_connection()
        # Cleanup resources
        await workflow_builder.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
