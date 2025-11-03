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
# Load environment variables from .env file
load_dotenv()

# Initialize ReasonFlow components


def build_workflow(llm_extractor, llm_analyzer, llm_summarizer, shared_memory):
    workflow_config = {
        "tasks": {
            "ingest-document": {
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
                        "query": "Retrieve Tesla financial data",
                        "top_k": 20
                    }
                }
            },
            "extract-highlights": {
                "type": "llm",
                "config": {
                    "agent": llm_extractor,
                    "params": {
                        "prompt": """Extract key financial highlights from the following data: 
                        {{ingest-document.output}}
                        
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
            {"from": "ingest-document", "to": "extract-highlights"},
            {"from": "extract-highlights", "to": "analyze-trends"},
            {"from": "analyze-trends", "to": "summarize-insights"}
        ]
    }
    return workflow_config

def main():

    shared_memory = SharedMemory()
    task_manager = TaskManager(shared_memory=shared_memory)
    workflow_builder = WorkflowBuilder(task_manager=task_manager)
        
    # Add document to the vector database
    rag_integration = RAGIntegration(
            db_path="vector_db_tesla.index",
            db_type="faiss",
            embedding_provider="sentence_transformers",
            embedding_model="all-MiniLM-L6-v2",
            shared_memory=shared_memory
    )
    rag_integration.add_documents(file_path="tsla-20240930-gen.pdf")
    print("Document added to vector database.")
    # Create agents
    llm_extractor = LLMIntegration(provider="openai", model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    llm_analyzer = LLMIntegration(provider="ollama", model="llama3.1:latest", api_key=None)
    llm_summarizer = LLMIntegration(provider="groq", model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

    # Build workflow
    workflow_config = build_workflow(llm_extractor, llm_analyzer, llm_summarizer, shared_memory)
    print(json.dumps(workflow_config, indent=2, default=str))
    workflow_id = workflow_builder.create_workflow(workflow_config)
    print(f"Workflow created with ID: {workflow_id}")

    # Execute workflow
    results = workflow_builder.execute_workflow(workflow_id)
    print("\n=== Workflow Execution Results ===")
    for task_id, result in results.items():
        print(f"Task {task_id}: {result}")

if __name__ == "__main__":
    main()
