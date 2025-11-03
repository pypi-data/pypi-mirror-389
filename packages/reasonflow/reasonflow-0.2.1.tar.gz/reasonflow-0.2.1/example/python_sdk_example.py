# Initialize SDK
from reasonflow.sdk.python_sdk import ReasonFlowSDK

sdk = ReasonFlowSDK(api_key="your_api_key")

# Create an LLM Agent
agent_config = {
    "model_name": "gpt-4",
    "api_key": "your_openai_key"
}
agent_id = sdk.create_agent(agent_type="llm", config=agent_config)
print(f"Agent created with ID: {agent_id}")

# Upload a document
doc_id = sdk.upload_document("path/to/document.pdf", metadata={"title": "Tesla Report", "tags": ["finance", "report"]})
print(f"Document uploaded with ID: {doc_id}")

# Search for documents
results = sdk.search_documents(query="Tesla financial report", limit=5)
print("Search Results:", results)
