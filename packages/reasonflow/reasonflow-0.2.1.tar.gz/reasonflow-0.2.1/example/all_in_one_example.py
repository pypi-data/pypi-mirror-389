from reasonflow.orchestrator.workflow_builder import WorkflowBuilder
from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.memory import SharedMemory

# Initialize ReasonFlow components
task_manager = TaskManager()
workflow_builder = WorkflowBuilder(task_manager=task_manager)
workflow_engine = WorkflowEngine(task_manager=task_manager)
shared_memory = SharedMemory()

# Step 1: Configure RAGIntegration and Add Document
rag_integration = RAGIntegration(
    db_path="vector_db_tesla.index",
    db_type="faiss",
    embedding_provider="sentence_transformers",
    embedding_model="all-MiniLM-L6-v2",
    shared_memory=shared_memory
)
pdf_path = "tesla_q10_report.pdf"
metadata = {"title": "Tesla Q10 Financial Report", "description": "Tesla's financial disclosures", "tags": ["Tesla", "Finance"]}
with open(pdf_path, "r") as file:
    document_content = file.read()
documents = [{"content": document_content, **metadata}]
rag_integration.add_documents(documents)

# Step 2: Define Agents
llm_extractor = LLMIntegration(provider="openai", model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
llm_analyzer = LLMIntegration(provider="ollama", model="ollama-latest", api_key=os.getenv("OLLAMA_API_KEY"))
llm_summarizer = LLMIntegration(provider="groq", model="groq-model-v1", api_key=os.getenv("GROQ_API_KEY"))

db_agent = DataRetrievalAgent(
    db_path="vector_db_tesla.index",
    db_type="faiss",
    embedding_provider="sentence_transformers",
    embedding_model="all-MiniLM-L6-v2",
    use_gpu=True,
    shared_memory=shared_memory
)

# Step 3: Build Workflow Using WorkflowBuilder
workflow_config = {
    "tasks": {
        "ingest_document": {"type": "data_retrieval", "config": {"query": "Retrieve Tesla financial data", "top_k": 20}},
        "extract_highlights": {"type": "llm", "config": {"agent": llm_extractor, "params": {"prompt": "Extract financial highlights"}}},
        "analyze_trends": {"type": "llm", "config": {"agent": llm_analyzer, "params": {"prompt": "Analyze trends in highlights"}}},
        "summarize_insights": {"type": "llm", "config": {"agent": llm_summarizer, "params": {"prompt": "Summarize key insights"}}}
    },
    "dependencies": [
        {"from": "ingest_document", "to": "extract_highlights"},
        {"from": "extract_highlights", "to": "analyze_trends"},
        {"from": "analyze_trends", "to": "summarize_insights"}
    ]
}
workflow_id = workflow_builder.create_workflow(workflow_config)
print(f"Workflow created with ID: {workflow_id}")

# Step 4: Add Custom Task Using WorkflowEngine
custom_task = Task(name="Custom Analysis", priority=2, dependencies=["summarize_insights"])
task_manager.add_task(custom_task)

# Step 5: Execute Workflow
workflow_engine.run_workflow()

# Step 6: Display Results
for task in task_manager.list_all_tasks():
    result = shared_memory.retrieve(task.name)
    print(f"Task: {task.name}, Status: {task.status}, Result: {result}")
