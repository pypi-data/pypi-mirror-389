from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import query_vector_db

from reasonflow.tasks.task import Task

# Initialize components
task_manager = TaskManager()
workflow_engine = WorkflowEngine(task_manager=task_manager)

# Add a PDF to the vector database
add_pdf_to_vector_db(
    file_path="pdfs/tsla-20240930-gen.pdf",
    db_path="vector_db_tesla.index",
    db_type="faiss",
    embedding_provider="sentence_transformers",
    embedding_model="all-mpnet-base-v2",
    use_llama=False
)

# Create and register agents
extractor_agent = CustomTaskAgent(function_path="tasks/extract_financials.py", task_manager=task_manager)
analyzer_agent = CustomTaskAgent(function_path="tasks/analyze_trends.py", task_manager=task_manager)
summarizer_agent = CustomTaskAgent(function_path="tasks/summarize_insights.py", task_manager=task_manager)

workflow_engine.register_agent("Extractor", extractor_agent)
workflow_engine.register_agent("Analyzer", analyzer_agent)
workflow_engine.register_agent("Summarizer", summarizer_agent)

# Define tasks
task1 = Task(name="Extract Financials", priority=5, metadata={"db_path": "vector_db_tesla.index"})
task2 = Task(name="Analyze Trends", priority=4, dependencies=["Extract Financials"])
task3 = Task(name="Summarize Insights", priority=3, dependencies=["Analyze Trends"])

# Add tasks to TaskManager
task_manager.add_task(task1)
task_manager.add_task(task2)
task_manager.add_task(task3)

# Execute workflow
workflow_engine.run_workflow()

# View task statuses
for task in task_manager.list_all_tasks():
    print(f"Task: {task.name}, Status: {task.status}")
