from typing import Dict, List, Optional, Any
from reasonchain.memory import SharedMemory
from reasonchain.rag.rag_main import query_vector_db
from reasonchain.rag.vector.add_to_vector_db import add_data_to_vector_db
from reasonchain.rag.vector.VectorDB import VectorDB
from reasonchain.llm_models.provider_registry import EmbeddingProviderRegistry
from reasonflow.config.DBConfigLoader import DBConfigLoader
import os


class RAGIntegration:
    def __init__(
        self,
        db_path: str,
        db_type: str = "faiss",
        embedding_provider: str = "sentence_transformers",
        embedding_model: str = "all-MiniLM-L6-v2",
        config_file: str = "db_config.yaml",
        db_config: Optional[Dict] = None,
        use_gpu: bool = False,
        api_key: Optional[str] = None,
        shared_memory: Optional[SharedMemory] = None,
        **kwargs
    ):
        """
        Initialize RAGIntegration with flexible provider support using ReasonChain's system.
        
        :param db_path: Path to the vector database.
        :param db_type: Type of vector database (faiss, milvus, pinecone, qdrant, weaviate).
        :param embedding_provider: Provider for embedding generation.
        :param embedding_model: Model name for embedding generation.
        :param db_config: Optional configuration for the database.
        :param use_gpu: Whether to use GPU for embedding generation.
        :param api_key: API key for embedding services if required.
        :param shared_memory: Shared memory instance for observability.
        :param kwargs: Additional provider-specific parameters.
        """
        self.shared_memory = shared_memory or SharedMemory()
        self.vector_db_path = db_path
        self.vector_db_type = db_type
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.use_gpu = use_gpu
        self.api_key = api_key
        self.kwargs = kwargs
        
        # Load database configuration
        if db_config is None:
            config_loader = DBConfigLoader(config_file)
            self.db_config = config_loader.get_config(db_type)
        else:
            self.db_config = db_config
        
        # Initialize VectorDB using ReasonChain's system
        try:
            self.vector_db = VectorDB(
                db_path=db_path,
                db_type=db_type,
                embedding_provider=embedding_provider,
                embedding_model=embedding_model,
                use_gpu=use_gpu,
                api_key=api_key,
                db_config=self.db_config,
                **kwargs
            )
        except Exception as e:
            # Fallback to available providers
            available_providers = EmbeddingProviderRegistry.list_providers()
            raise ValueError(
                f"Failed to initialize vector database with provider '{embedding_provider}'. "
                f"Available embedding providers: {available_providers}. Error: {str(e)}"
            )
    
    @classmethod
    def register_embedding_provider(cls, provider_name: str, provider_class: type) -> None:
        """
        Register a custom embedding provider.
        
        Args:
            provider_name: Name of the provider
            provider_class: Provider class that inherits from BaseEmbeddingProvider
        """
        EmbeddingProviderRegistry.register(provider_name, provider_class)
        print(f"Registered custom embedding provider: {provider_name}")
    
    @classmethod
    def list_available_embedding_providers(cls) -> list:
        """Get list of all available embedding providers."""
        return EmbeddingProviderRegistry.list_providers()
    
    @classmethod
    def list_supported_vector_databases(cls) -> list:
        """Get list of supported vector database types."""
        return ["faiss", "milvus", "pinecone", "qdrant", "weaviate"]

    def add_documents(self, file_paths: List[str]) -> bool:
        """
        Add documents to the vector database using ReasonChain's system.
        :param file_paths: List of paths to the files to add.
        :return: True if successful, False otherwise.
        """
        try:
            print(f"\nAttempting to add documents: {file_paths}")
            print(f"Vector DB Path: {self.vector_db_path}")
            print(f"Vector DB Type: {self.vector_db_type}")
            print(f"Embedding Provider: {self.embedding_provider}")
            print(f"Embedding Model: {self.embedding_model}")

            # Log documents to shared memory
            if self.shared_memory:
                self.shared_memory.add_entry("file_paths", file_paths)

            # Use ReasonChain's add_data_to_vector_db function
            result = add_data_to_vector_db(
                file_paths=file_paths,
                db_path=self.vector_db_path,
                db_type=self.vector_db_type,
                embedding_provider=self.embedding_provider,
                embedding_model=self.embedding_model,
                use_gpu=self.use_gpu,
                db_config=self.db_config,
                **self.kwargs
            )

            # Check if index was created successfully
            if os.path.exists(self.vector_db_path):
                print(f"Vector database file exists at: {self.vector_db_path}")
                print(f"File size: {os.path.getsize(self.vector_db_path)} bytes")
                print(f"Result from add_documents: {result}")
                return result
            else:
                print(f"Vector database file not found at: {self.vector_db_path}")
                print(f"Result from add_documents: {result}")
                return result

        except Exception as e:
            print(f"Error adding document: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.shared_memory:
                self.shared_memory.add_entry("add_documents_error", str(e))
            return False
    
    def add_raw_data(self, texts: List[str], metadata: Optional[List[Dict]] = None) -> bool:
        """
        Add raw text data to the vector database.
        
        Args:
            texts: List of text strings to add
            metadata: Optional list of metadata dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nAdding {len(texts)} text documents to vector database")
            
            # Log to shared memory
            if self.shared_memory:
                self.shared_memory.add_entry("raw_texts_count", len(texts))
            
            # Use VectorDB to add embeddings
            self.vector_db.add_embeddings(texts, metadata=metadata)
            self.vector_db.save_index(self.vector_db_path)
            
            print(f"Successfully added {len(texts)} text documents")
            return True
            
        except Exception as e:
            print(f"Error adding raw data: {str(e)}")
            if self.shared_memory:
                self.shared_memory.add_entry("add_raw_data_error", str(e))
            return False

    def search(self, query: str, top_k: int = 5) -> Dict:
        """Search the vector database using ReasonChain's system."""
        try:
            print(f"\nSearching vector database...")
            print(f"Path: {self.vector_db_path}")
            print(f"Type: {self.vector_db_type}")
            print(f"Query: {query}")
            print(f"Top K: {top_k}")

            # Use ReasonChain's query_vector_db function
            results = query_vector_db(
                db_path=self.vector_db_path,
                db_type=self.vector_db_type,
                db_config=self.db_config,
                query=query,
                top_k=top_k,
                embedding_provider=self.embedding_provider,
                embedding_model=self.embedding_model,
                use_gpu=self.use_gpu
            )
            
            print(f"\nRaw results from vector DB:")
            print(results)

            # Format results
            formatted_results = []
            for entry in results["results"]:
                # Clean and format the text content
                text = entry.get("text", "").replace("\t", " ").strip()
                
                # Extract and format metadata
                metadata = entry.get("metadata", {})
                search_metrics = metadata.get("search_metrics", {})
                resource_metrics = metadata.get("resource_metrics", {})
                index_metrics = metadata.get("index_metrics", {})
                score_stats = metadata.get("score_stats", {})
                
                formatted_result = {
                    "content": text,
                    "score": entry.get("score"),
                    "index": entry.get("index"),
                    "metadata": {
                        "search_metrics": {
                            "search_time": search_metrics.get("search_time"),
                            "query_time": search_metrics.get("query_time"),
                            "similarity_score": search_metrics.get("similarity_score"),
                            "rank": search_metrics.get("rank"),
                            "total_results": search_metrics.get("total_results")
                        },
                        "resource_metrics": {
                            "gpu_memory": resource_metrics.get("gpu_memory_used"),
                            "cpu_memory": resource_metrics.get("cpu_memory_used"),
                            "device_type": resource_metrics.get("device_type")
                        },
                        "index_metrics": {
                            "total_vectors": index_metrics.get("total_vectors"),
                            "dimension": index_metrics.get("dimension"),
                            "index_fullness": index_metrics.get("index_fullness", 0)
                        },
                        "score_stats": {
                            "max_score": score_stats.get("max_score"),
                            "min_score": score_stats.get("min_score"),
                            "mean_score": score_stats.get("mean_score"),
                            "total_chunks": score_stats.get("total_chunks")
                        }
                    }
                }
                
                # Add provider-specific metrics
                if self.vector_db_type == "weaviate":
                    queue_metrics = metadata.get("queue_metrics", {})
                    formatted_result["metadata"]["queue_metrics"] = {
                        "size": queue_metrics.get("size"),
                        "push_duration_ms": queue_metrics.get("push_duration_ms"),
                        "search_duration_ms": queue_metrics.get("search_duration_ms")
                    }
                elif self.vector_db_type == "pinecone":
                    cloud_metrics = metadata.get("cloud_metrics", {})
                    formatted_result["metadata"]["cloud_metrics"] = {
                        "provider": cloud_metrics.get("provider"),
                        "region": cloud_metrics.get("region"),
                        "replicas": cloud_metrics.get("replicas")
                    }
                elif self.vector_db_type == "qdrant":
                    performance = metadata.get("performance", {})
                    formatted_result["metadata"]["performance"] = {
                        "grpc_responses": performance.get("grpc_responses_total"),
                        "rest_responses": performance.get("rest_responses_total"),
                        "error_count": performance.get("error_count")
                    }
                elif self.vector_db_type == "faiss":
                    performance = metadata.get("performance", {})
                    formatted_result["metadata"]["performance"] = {
                        "search_qps": performance.get("search_qps"),
                        "error_count": performance.get("error_count"),
                        "last_operation_time": performance.get("last_operation_time")
                    }
                
                formatted_results.append(formatted_result)

            # Combine overall metadata
            response_metadata = {
                "query": query,
                "top_k": top_k,
                "num_results": len(formatted_results),
                "provider": self.vector_db_type,
                "embedding_model": self.embedding_model,
                "embedding_provider": self.embedding_provider,
                "latency": results.get("metadata", {}).get("total_time"),
                "cost": results.get("metadata", {}).get("cost", 0.0),
                "cache_hit": results.get("metadata", {}).get("cache_hit", False),
                "timestamp": results.get("metadata", {}).get("timestamp"),
                "query_type": results.get("metadata", {}).get("query_type", "semantic_search")
            }

            # Add index stats to response metadata
            index_stats = self.get_index_stats()
            response_metadata["index_stats"] = index_stats

            # Construct final response with summary
            response = {
                "status": "success",
                "summary": {
                    "total_results": len(formatted_results),
                    "avg_score": sum(r["score"] for r in formatted_results) / len(formatted_results) if formatted_results else 0,
                    "latency": response_metadata["latency"],
                    "provider": self.vector_db_type
                },
                "results": formatted_results,
                "metadata": response_metadata
            }

            print(f"\nFormatted results summary:")
            print(f"Total results: {response['summary']['total_results']}")
            print(f"Average score: {response['summary']['avg_score']:.4f}")
            print(f"Latency: {response['summary']['latency']:.4f}s")
            print(f"Provider: {response['summary']['provider']}")

            return response
        except Exception as e:
            print(f"Error in search: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "results": [],
                "metadata": {
                    "query": query,
                    "top_k": top_k,
                    "provider": self.vector_db_type
                }
            }

    def configure_vector_db(self, db_path: str, db_type: str = "faiss"):
        """
        Configure the vector database path and type.
        :param db_path: Path to the vector database.
        :param db_type: Type of vector database (e.g., "faiss").
        """
        self.vector_db_path = db_path
        self.vector_db_type = db_type

    def get_index_size(self) -> int:
        """Get the number of vectors in the index."""
        try:
            if hasattr(self, 'index') and self.index:
                if self.vector_db_type == "faiss":
                    return self.index.ntotal
                elif self.vector_db_type == "milvus":
                    return self.index.count()
                elif self.vector_db_type == "pinecone":
                    stats = self.index.describe_index_stats()
                    return stats.get("total_vector_count", 0)
            return 0
        except Exception as e:
            print(f"Error getting index size: {str(e)}")
            return 0

    def get_dimensions(self) -> int:
        """Get the dimensionality of the vectors."""
        try:
            if hasattr(self, 'index') and self.index:
                if self.vector_db_type == "faiss":
                    return self.index.d
                elif self.vector_db_type == "milvus":
                    return self.index.dimension
                elif self.vector_db_type == "pinecone":
                    return self.index.describe_index_stats().get("dimension", 0)
            return 0
        except Exception as e:
            print(f"Error getting dimensions: {str(e)}")
            return 0

    def get_gpu_memory_used(self) -> float:
        """Get GPU memory usage in MB if GPU is being used."""
        try:
            if not self.use_gpu:
                return 0.0
            
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / 1024 / 1024  # Convert to MB
            return 0.0
        except Exception as e:
            print(f"Error getting GPU memory usage: {str(e)}")
            return 0.0

    def get_memory_used(self) -> float:
        """Get CPU memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            print(f"Error getting memory usage: {str(e)}")
            return 0.0

    def get_num_threads(self) -> int:
        """Get number of threads being used."""
        try:
            import psutil
            process = psutil.Process()
            return process.num_threads()
        except Exception as e:
            print(f"Error getting thread count: {str(e)}")
            return 0

    def calculate_query_cost(self, query: str) -> float:
        """Calculate the cost of a query based on the embedding model and provider."""
        try:
            # Cost calculation based on provider and model
            if self.embedding_provider == "openai":
                # OpenAI's ada embedding cost
                return len(query.split()) * 0.0001  # $0.0001 per token
            elif self.embedding_provider == "cohere":
                # Cohere's embedding cost
                return len(query.split()) * 0.00001  # $0.00001 per token
            elif self.embedding_provider == "sentence_transformers":
                # Local models have no direct cost
                return 0.0
            return 0.0
        except Exception as e:
            print(f"Error calculating query cost: {str(e)}")
            return 0.0

    def is_cache_hit(self) -> bool:
        """Check if the last query was served from cache."""
        try:
            if hasattr(self, 'cache') and self.cache:
                return self.cache.get('last_query_cached', False)
            return False
        except Exception as e:
            print(f"Error checking cache status: {str(e)}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get comprehensive index statistics."""
        try:
            return {
                "index_size": self.get_index_size(),
                "dimensions": self.get_dimensions(),
                "gpu_memory": self.get_gpu_memory_used() if self.use_gpu else 0.0,
                "cpu_memory": self.get_memory_used(),
                "num_threads": self.get_num_threads(),
                "db_type": self.vector_db_type,
                "embedding_model": self.embedding_model,
                "embedding_provider": self.embedding_provider,
                "use_gpu": self.use_gpu,
                "db_path": self.vector_db_path
            }
        except Exception as e:
            print(f"Error getting index stats: {str(e)}")
            return {}
