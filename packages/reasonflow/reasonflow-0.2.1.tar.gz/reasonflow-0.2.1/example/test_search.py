import os
from dotenv import load_dotenv
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonchain.memory import SharedMemory

def test_vector_search():
    # Initialize components
    shared_memory = SharedMemory()
    
    # Check file existence
    file_path = "tsla-20240930-gen.pdf"
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        print(f"Current working directory: {os.getcwd()}")
        return
        
    print(f"Found file: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    # Initialize RAG integration
    rag = RAGIntegration(
        db_path="vector_db_tesla.index",
        db_type="faiss",
        embedding_provider="sentence_transformers",
        embedding_model="all-MiniLM-L6-v2",
        shared_memory=shared_memory
    )
    
    # First, add the document
    print("\nAdding document to vector database...")
    success = rag.add_documents(file_path)
    
    # Verify index creation
    if os.path.exists("vector_db_tesla.index"):
        print("\nVector database file details:")
        print(f"Size: {os.path.getsize('vector_db_tesla.index')} bytes")
        print(f"Created: {os.path.getctime('vector_db_tesla.index')}")
        print(f"Modified: {os.path.getmtime('vector_db_tesla.index')}")
        
        # Try to load the index
        try:
            import faiss
            index = faiss.read_index("vector_db_tesla.index")
            print(f"Successfully loaded index with {index.ntotal} vectors")
            print(f"Index dimension: {index.d}")
        except Exception as e:
            print(f"Error loading index: {e}")
    
    if not success:
        print("Failed to add document")
        return
    
    # Test search with different queries
    test_queries = [
        "What is Tesla's revenue?",
        "Describe Tesla's financial performance",
        "What are the key financial metrics?",
        "Retrieve Tesla financial data"
    ]
    
    print("\nTesting search functionality...")
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = rag.search(query=query, top_k=5)
        print(f"Number of results: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Content: {result.get('content', 'No content')[:200]}...")
            print(f"Score: {result.get('score', 'No score')}")
            if result.get('metadata'):
                print(f"Metadata: {result['metadata']}")

if __name__ == "__main__":
    load_dotenv()
    test_vector_search() 