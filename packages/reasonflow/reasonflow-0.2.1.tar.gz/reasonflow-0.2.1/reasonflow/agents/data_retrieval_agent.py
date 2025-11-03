from typing import Dict, List, Optional
import os
import logging
import time

from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonchain.memory import SharedMemory
from reasonflow.models.data_retrieval_models import DataRetrievalResponse

logger = logging.getLogger(__name__)

class DataRetrievalAgent:
    def __init__(
        self,
        db_path: str,
        db_type: str = "faiss",
        embedding_provider: str = "sentence_transformers",
        embedding_model: str = "all-MiniLM-L6-v2",
        db_config: Optional[Dict] = None,
        use_gpu: bool = False,
        api_key: Optional[str] = None,
        shared_memory: Optional[SharedMemory] = None,
    ):
        self.vector_store_type = db_type
        # Create new SharedMemory instance if none provided or if it's a string
        if shared_memory is None or isinstance(shared_memory, str):
            shared_memory = SharedMemory()
        
        self.shared_memory = shared_memory
        self.rag = RAGIntegration(
            db_path=db_path,
            db_type=db_type,
            db_config=db_config,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            use_gpu=use_gpu,
            api_key=api_key,
            shared_memory=self.shared_memory
        )

    def index_document(self, file_paths: List[str]) -> Dict:
        """
        Index documents into the vector database.
        :param file_paths: List of file paths to index
        :return: Dictionary containing indexing results or error
        """
        try:
            logging.info(f"Indexing documents: {file_paths}")
            result = self.rag.add_documents(file_paths=file_paths)
            
            # Validate response using Pydantic model
            validated_response = DataRetrievalResponse(**result)
            return validated_response.dict()
            
        except Exception as e:
            error_msg = f"Error indexing documents: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "metadata": {
                    "error": str(e),
                    "file_paths": file_paths
                }
            }

    def execute(self, query: str = "", top_k: int = 5, **kwargs) -> Dict:
        """
        Execute a search query against the vector database.
        :param query: Search query string
        :param top_k: Number of results to return
        :return: Dictionary containing results or error
        """
        start_time = time.time()
        try:
            logging.info(f"Executing search query: {query}")
            rag_response = self.rag.search(query=query, top_k=top_k)
            execution_time = time.time() - start_time
            
            # If RAG returns empty or error response
            if not rag_response or rag_response.get("status") == "error":
                logging.warning(f"No results found for query: {query}")
                return {
                    "status": "success",
                    "summary": {
                        "total_results": 0,
                        "avg_score": 0.0,
                        "latency": execution_time,
                        "provider": self.vector_store_type
                    },
                    "output": "No relevant documents found for the given query.",
                    "results": [],
                    "metadata": {
                        "query": query,
                        "top_k": top_k,
                        "num_results": 0,
                        "provider": self.vector_store_type,
                        "embedding_model": self.rag.embedding_model,
                        "embedding_provider": self.rag.embedding_provider,
                        "timestamp": time.time(),
                        "query_type": "semantic_search",
                        "latency": execution_time,
                        "cost": 0.0,
                        "cache_hit": False,
                        "index_stats": {
                            "total_vectors": self.rag.get_index_size(),
                            "dimensions": self.rag.get_dimensions(),
                            "gpu_memory": self.rag.get_gpu_memory_used() if self.rag.use_gpu else 0.0,
                            "cpu_memory": self.rag.get_memory_used(),
                            "num_threads": self.rag.get_num_threads(),
                            "db_type": self.vector_store_type,
                            "embedding_model": self.rag.embedding_model,
                            "embedding_provider": self.rag.embedding_provider,
                            "use_gpu": self.rag.use_gpu
                        }
                    }
                }

            # Get results and metadata from RAG response
            results = rag_response.get("results", [])
            rag_metadata = rag_response.get("metadata", {})
            rag_summary = rag_response.get("summary", {})
            
            # Format results for output with better structure
            formatted_results = []
            formatted_output_parts = []
            
            for i, result in enumerate(results):
                # Clean and format the content
                content = result.get("content", "").strip()
                score = result.get("score", 0.0)
                
                # Format for human-readable output
                formatted_output_parts.append(
                    f"Document {i+1} (Score: {score:.4f}):\n{content}"
                )
                
                # Add to structured results
                formatted_results.append({
                    "content": content,
                    "score": score,
                    "index": result.get("index"),
                    "metadata": result.get("metadata", {})
                })
            
            formatted_output = "\n\n".join(formatted_output_parts)
            
            if self.shared_memory:
                self.shared_memory.add_entry("search_results", formatted_results)
                self.shared_memory.add_entry("search_metadata", rag_metadata)

            # Construct response with enhanced structure
            response = {
                "status": "success",
                "summary": {
                    "total_results": rag_summary.get("total_results", len(results)),
                    "avg_score": rag_summary.get("avg_score", sum(r.get("score", 0) for r in results) / len(results) if results else 0),
                    "latency": rag_summary.get("latency", execution_time),
                    "provider": self.vector_store_type
                },
                "output": formatted_output,  # Human-readable output
                "results": formatted_results,  # Structured results
                "metadata": {
                    "query": query,
                    "top_k": top_k,
                    "num_results": len(results),
                    "provider": self.vector_store_type,
                    "embedding_model": self.rag.embedding_model,
                    "embedding_provider": self.rag.embedding_provider,
                    "timestamp": rag_metadata.get("timestamp", time.time()),
                    "query_type": rag_metadata.get("query_type", "semantic_search"),
                    "latency": rag_metadata.get("total_time", execution_time),
                    "cost": rag_metadata.get("cost", 0.0),
                    "cache_hit": rag_metadata.get("cache_hit", False),
                    "index_stats": rag_metadata.get("index_stats", {
                        "total_vectors": self.rag.get_index_size(),
                        "dimensions": self.rag.get_dimensions(),
                        "gpu_memory": self.rag.get_gpu_memory_used() if self.rag.use_gpu else 0.0,
                        "cpu_memory": self.rag.get_memory_used(),
                        "num_threads": self.rag.get_num_threads(),
                        "db_type": self.vector_store_type,
                        "embedding_model": self.rag.embedding_model,
                        "embedding_provider": self.rag.embedding_provider,
                        "use_gpu": self.rag.use_gpu
                    })
                }
            }

            # Log summary statistics
            logging.info(f"Search completed: {response['summary']}")
            return response
            
        except Exception as e:
            error_msg = f"Error executing search: {str(e)}"
            execution_time = time.time() - start_time
            logging.error(error_msg)
            if self.shared_memory:
                self.shared_memory.add_entry("search_error", error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "summary": {
                    "total_results": 0,
                    "avg_score": 0.0,
                    "latency": execution_time,
                    "provider": self.vector_store_type
                },
                "output": f"Error during search: {str(e)}",  # Human-readable error
                "results": [],  # Empty results
                "metadata": {
                    "query": query,
                    "top_k": top_k,
                    "num_results": 0,
                    "provider": self.vector_store_type,
                    "embedding_model": self.rag.embedding_model,
                    "embedding_provider": self.rag.embedding_provider,
                    "timestamp": time.time(),
                    "query_type": "semantic_search",
                    "latency": execution_time,
                    "cost": 0.0,
                    "cache_hit": False,
                    "index_stats": {
                        "total_vectors": 0,
                        "dimensions": 0,
                        "gpu_memory": 0.0,
                        "cpu_memory": 0.0,
                        "num_threads": 0,
                        "db_type": self.vector_store_type,
                        "embedding_model": self.rag.embedding_model,
                        "embedding_provider": self.rag.embedding_provider,
                        "use_gpu": self.rag.use_gpu
                    },
                    "error": str(e)
                }
            }
