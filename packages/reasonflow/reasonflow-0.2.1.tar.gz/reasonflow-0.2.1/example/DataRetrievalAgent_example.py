from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.integrations.rag_integrations import RAGIntegration
import os

qdrant_db_config = {
    "mode": "cloud",
    "api_key": os.getenv("QDRANT_API_KEY"),
    "host": os.getenv("QDRANT_HOST"),
    "port": os.getenv("QDRANT_PORT"),
    "collection_name": os.getenv("QDRANT_COLLECTION_NAME")
}

# pinecone_db_config = {
#     "mode": "cloud",
#     "api_key": os.getenv("PINECONE_API_KEY"),
#     "index_name": "tesla-q11",
#     "environment": os.getenv("PINECONE_ENVIRONMENT", "us-east-1"),
#     "batch_size": 500
# }

# weaviate_db_config = {
#     "mode" : 'cloud',
#     "class_name" : "tesla_q11",
#     "api_key" : os.getenv("WEAVIATE_API_KEY"),
#     "WEAVIATE_CLUSTER_URL" : os.getenv("WEAVIATE_CLUSTER_URL")
# }

db_path = "vector_db_tesla.index"
db_type = "faiss"
embedding_provider = "sentence_transformers"
embedding_model = "all-MiniLM-L6-v2"
use_gpu = True

# rag = RAGIntegration(
#     db_path=db_path,
#     db_type=db_type,
#     db_config=None,
#     embedding_provider=embedding_provider,
#     embedding_model=embedding_model,
#     use_gpu=use_gpu,
# )
# add_result = rag.add_documents(file_path="tsla-20240930-gen.pdf")
# print(add_result)
# Initialize the Data Retrieval Agent
agent = DataRetrievalAgent(
    db_path=db_path,
    db_type=db_type,
    db_config=None,
    embedding_provider=embedding_provider,
    embedding_model=embedding_model,
    use_gpu=use_gpu,
)

#Index a document
add_result = agent.index_document(file_paths=["tsla-20240930-gen.pdf"])
print(add_result)

# Search the database
query = "What are Tesla's financial highlights?"
results = agent.execute(query=query, top_k=5)
print("Search Results:", results)
