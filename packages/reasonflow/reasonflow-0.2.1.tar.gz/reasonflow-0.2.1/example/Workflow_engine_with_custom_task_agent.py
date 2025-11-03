from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.memory import SharedMemory
from reasonflow.tasks.task import Task

# Initialize components
task_manager = TaskManager()
workflow_engine = WorkflowEngine(task_manager=task_manager)
shared_memory = SharedMemory()

# Step 1: Data Retrieval Agents
db_agent = DataRetrievalAgent(
    db_path="vector_db_financial.index",
    db_type="faiss",
    embedding_provider="sentence_transformers",
    embedding_model="all-MiniLM-L6-v2",
    use_gpu=True,
    shared_memory=shared_memory
)

api_agent = CustomTaskAgent(
    function_path="tasks/retrieve_api_data.py",
    task_manager=task_manager,
    shared_memory=shared_memory
)

# Step 2: Analysis and Processing Agents
extractor_agent = CustomTaskAgent(
    function_path="tasks/extract_insights.py",
    task_manager=task_manager,
    shared_memory=shared_memory
)
analyzer_agent = CustomTaskAgent(
    function_path="tasks/analyze_trends.py",
    task_manager=task_manager,
    shared_memory=shared_memory
)
summarizer_agent = CustomTaskAgent(
    function_path="tasks/summarize_report.py",
    task_manager=task_manager,
    shared_memory=shared_memory
)

# Step 3: Register Agents
workflow_engine.register_agent("Database Retrieval", db_agent)
workflow_engine.register_agent("API Retrieval", api_agent)
workflow_engine.register_agent("Insight Extractor", extractor_agent)
workflow_engine.register_agent("Trend Analyzer", analyzer_agent)
workflow_engine.register_agent("Summarizer", summarizer_agent)

# Step 4: Define Tasks
task1 = Task(name="Retrieve Database Data", priority=5, metadata={"query": "Retrieve Tesla financial data"})
task2 = Task(name="Retrieve API Data", priority=4)
task3 = Task(name="Extract Insights", priority=3, dependencies=["Retrieve Database Data", "Retrieve API Data"])
task4 = Task(name="Analyze Trends", priority=2, dependencies=["Extract Insights"])
task5 = Task(name="Summarize Insights", priority=1, dependencies=["Analyze Trends"])

# Add tasks to TaskManager
task_manager.add_task(task1)
task_manager.add_task(task2)
task_manager.add_task(task3)
task_manager.add_task(task4)
task_manager.add_task(task5)

# Step 5: Execute Workflow
print("Executing workflow...")
workflow_engine.run_workflow()

# Step 6: View Results
print("\n=== Task Results ===")
for task in task_manager.list_all_tasks():
    result = shared_memory.retrieve(task.name)
    print(f"Task: {task.name}, Status: {task.status}, Result: {result}")
