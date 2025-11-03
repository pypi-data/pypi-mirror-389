from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasonchain.memory import SharedMemory
import os

# Initialize ReasonFlow components
task_manager = TaskManager()
workflow_builder = WorkflowBuilder(task_manager=task_manager)
shared_memory = SharedMemory()

# Step 1: Configure Vector Database and Add Document
rag_integration = RAGIntegration(
    db_path="vector_db_tesla.index",
    db_type="faiss",
    embedding_provider="sentence_transformers",
    embedding_model="all-MiniLM-L6-v2",
    shared_memory=shared_memory
)

pdf_path = "/home/sunny-bedi/practise/Reason/tsla-20240930-gen.pdf"
metadata = {
    "title": "Tesla Q10 Financial Report",
    "description": "Tesla's financial disclosures for the quarter ending 2024-09-30",
    "tags": ["Tesla", "Finance", "Q10"]
}

print("Adding document to the vector database...")
with open(pdf_path, "r") as file:
    document_content = file.read()

documents = [{"content": document_content, **metadata}]
rag_integration.add_documents(documents)

# Step 2: Define LLM Agents for Workflow
llm_extractor = LLMIntegration(provider="openai", model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
llm_analyzer = LLMIntegration(provider="ollama", model="ollama-latest", api_key=os.getenv("OLLAMA_API_KEY"))
llm_summarizer = LLMIntegration(provider="groq", model="groq-model-v1", api_key=os.getenv("GROQ_API_KEY"))

# Step 3: Build Workflow with TaskManager
workflow_config = {
    "tasks": {
        "ingest_document": {
            "type": "data_retrieval",
            "config": {
                "query": f"Find document with metadata: {metadata}",
                "top_k": 20
            }
        },
        "extract_highlights": {
            "type": "llm",
            "config": {
                "agent": llm_extractor,
                "params": {
                    "prompt": "Extract financial highlights from Tesla's Q10 report."
                }
            }
        },
        "analyze_trends": {
            "type": "llm",
            "config": {
                "agent": llm_analyzer,
                "params": {
                    "prompt": "Analyze the trends in the extracted financial highlights."
                }
            }
        },
        "summarize_insights": {
            "type": "llm",
            "config": {
                "agent": llm_summarizer,
                "params": {
                    "prompt": "Summarize the analysis into key insights for Tesla's Q10 report."
                }
            }
        }
    },
    "dependencies": [
        {"from": "ingest_document", "to": "extract_highlights"},
        {"from": "extract_highlights", "to": "analyze_trends"},
        {"from": "analyze_trends", "to": "summarize_insights"}
    ]
}

workflow_id = workflow_builder.create_workflow(workflow_config)
print(f"Workflow created with ID: {workflow_id}")

# Step 4: Execute Workflow
print("Executing workflow...")
results = workflow_builder.execute_workflow(workflow_id)

# Step 5: Track Task Progress and Display Results
print("\n=== Workflow Execution Results ===")
for task_id, result in results.items():
    task_status = task_manager.get_task_status(task_id)
    print(f"Task {task_id} ({task_status['status']}): {result}")
