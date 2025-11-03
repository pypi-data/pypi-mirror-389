import os
from dotenv import load_dotenv
from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonchain.memory import SharedMemory

import json

# Load environment variables
load_dotenv()

def setup_agents():
    """Setup all required agents"""
    # Initialize RAG
    rag = RAGIntegration(
        db_path="vector_db_tesla.index",
        db_type="faiss",
        embedding_model="all-MiniLM-L6-v2"
    )
    
    # Initialize LLM
    llm = LLMIntegration(
        provider="openai",
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Initialize Data Retrieval Agent
    # data_agent = DataRetrievalAgent(
    #     rag_integration=rag,
    #     shared_memory=SharedMemory()
    # )
    
    return {
        "rag": rag,
        "llm": llm,
        # "data_agent": data_agent
    }

def get_reasontrack_config():
    """Get ReasonTrack configuration"""
    return {
        "event_backend": {
            "type": "kafka",
            "config": {
                "broker_url": "localhost:9092",
                "topic_prefix": "reasonflow_events_"
            }
        },
        "metrics_backend": {
            "type": "prometheus",
            "config": {
                "pushgateway_url": "localhost:9091",
                "job_name": "reasonflow_metrics"
            }
        },
        "alert_config": {
            "storage_path": "alerts",
            "retention_days": 30,
            "backends": {
                "slack": {
                    "webhook_url": os.getenv("SLACK_WEBHOOK_URL")
                },
                "email": {
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": os.getenv("ALERT_EMAIL"),
                    "password": os.getenv("ALERT_EMAIL_PASSWORD")
                }
            }
        },
        "state_config": {
            "storage_path": "workflow_states"
        }
    }

def run_workflow_with_tracking(tracker_type="basic", tracker_config=None, config_path=None):
    """Run a sample workflow with specified tracking configuration"""
    
    # Initialize workflow engine with tracking

    
    # Initialize workflow builder
    workflow_builder = WorkflowBuilder( tracker_type=tracker_type,
        tracker_config=tracker_config,
        config_path=config_path)
    
    # Setup agents
    agents = setup_agents()
    
    # Create workflow configuration
    workflow_config = {
        "tasks": {
            "data_retrieval": {
                "type": "data_retrieval",
                "config": {
                    "agent": agents["rag"],
                    "params": {
                        "query": "What was Tesla's revenue in 2023?",
                        "document_type": "financial_report"
                    }
                }
            },
            "analysis": {
                "type": "llm",
                "config": {
                    "agent": agents["llm"],
                    "params": {
                        "prompt": """
                        Analyze Tesla's performance based on:
                        Retrieved data: {{data_retrieval.output}}
                        """
                    }
                }
            },
            "summary": {
                "type": "llm",
                "config": {
                    "agent": agents["llm"],
                    "params": {
                        "prompt": "Create a concise summary of this analysis: {{analysis.response}}"
                    }
                }
            }
        },
        "dependencies": [
            ["ingest-document", "extract-highlights"],
            ["extract-highlights", "analyze-trends"],
            ["analyze-trends", "summarize-insights"]
        ]
    }
    
    try:
        # Create workflow
        workflow_id = await workflow_builder.create_workflow(workflow_config)
        print(f"\nWorkflow created with ID: {workflow_id}")
        
        # Execute workflow with tracking
        results = await workflow_builder.execute_workflow(workflow_id)
        
        # Get tracking information
        if tracker_type == "basic":
            # Get basic tracking info
            task_logs = await workflow_builder.task_manager.tracker.get_logs()
            print("\nBasic Tracking Logs:")
            for log in task_logs:
                print(f"Task: {log['task_name']}, Status: {log['status']}, Time: {log['timestamp']}")
                
        else:
            # Get advanced tracking metrics
            metrics = await workflow_builder.engine.tracker.get_workflow_status(workflow_id)
            print("\nAdvanced Tracking Metrics:")
            print(json.dumps(metrics, indent=2))
            
            # Get task-specific metrics
            for task_id in workflow_config["tasks"]:
                task_metrics = await workflow_builder.engine.tracker.get_task_metrics(task_id)
                print(f"\nMetrics for task {task_id}:")
                print(json.dumps(task_metrics, indent=2))
            
        return results
        
    except Exception as e:
        print(f"Error executing workflow: {str(e)}")
        return None

def main():
    # Example 1: Basic Tracking
    print("\n=== Running Workflow with Basic Tracking ===")
    config_path = os.path.join(os.path.dirname(__file__),"config", "reasontrack_config.yaml")
    #basic_results = run_workflow_with_tracking(tracker_type="basic", config_path=config_path)
    
    # Example 2: Advanced Tracking with ReasonTrack
    print("\n=== Running Workflow with Advanced Tracking ===")
    advanced_results = run_workflow_with_tracking(
        tracker_type="reasontrack",
        tracker_config=get_reasontrack_config(),
        config_path=config_path
    )
    
    # Compare results and tracking data
    print("\n=== Workflow Results Comparison ===")
    #print("\nBasic Tracking Results:")
    #print(json.dumps(basic_results, indent=2))
    print("\nAdvanced Tracking Results:")
    print(json.dumps(advanced_results, indent=2))

if __name__ == "__main__":
    main() 