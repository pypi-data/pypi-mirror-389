"""
Advanced RAG and LLM Integration Workflow Example

This example demonstrates a comprehensive workflow using the latest RAG and LLM integrations
with multiple providers including OpenAI, Groq, Anthropic, and local models.

Features demonstrated:
- Multi-provider LLM integration (OpenAI, Groq, Anthropic, local models)
- Advanced RAG with multiple vector databases (FAISS, Pinecone, Qdrant)
- Custom agents for document processing, analysis, and summarization
- Comprehensive observability and tracking
- Dynamic provider switching based on task requirements
- Error handling and fallback mechanisms
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# ReasonFlow imports
from reasonflow.orchestrator.workflow_engine import WorkflowEngine
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.tasks.task_manager import TaskManager
from reasonflow.tasks.task import Task
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.observability import TrackerFactory
from reasonchain.memory import SharedMemory

# Configuration constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Vector database configurations
VECTOR_DB_CONFIGS = {
    "faiss_local": {
        "db_path": "vector_db_advanced_example.index",
        "db_type": "faiss",
        "embedding_provider": "sentence_transformers",
        "embedding_model": "all-MiniLM-L6-v2"
    },
    "faiss_openai": {
        "db_path": "vector_db_openai_embeddings.index",
        "db_type": "faiss",
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-ada-002"
    }
}

# LLM provider configurations
LLM_CONFIGS = {
    "openai_gpt4": {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": OPENAI_API_KEY,
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "groq_llama": {
        "provider": "groq",
        "model": "llama-3.1-70b-versatile",
        "api_key": GROQ_API_KEY,
        "temperature": 0.5,
        "max_tokens": 1500
    },
    "anthropic_claude": {
        "provider": "anthropic",
        "model": "claude-3-sonnet-20240229",
        "api_key": ANTHROPIC_API_KEY,
        "temperature": 0.6,
        "max_tokens": 1800
    },
    "local_ollama": {
        "provider": "ollama",
        "model": "llama2:7b",
        "base_url": "http://localhost:11434"
    }
}


class AdvancedDocumentProcessor:
    """Advanced document processor with multi-provider RAG and LLM capabilities."""
    
    def __init__(self, shared_memory: SharedMemory):
        self.shared_memory = shared_memory
        self.rag_integrations = {}
        self.llm_integrations = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize RAG integrations
        self._initialize_rag_integrations()
        
        # Initialize LLM integrations
        self._initialize_llm_integrations()
    
    def _initialize_rag_integrations(self):
        """Initialize multiple RAG integrations with different providers."""
        try:
            for name, config in VECTOR_DB_CONFIGS.items():
                self.logger.info(f"Initializing RAG integration: {name}")
                
                # Skip if API key is missing for paid providers
                if config["embedding_provider"] == "openai" and not OPENAI_API_KEY:
                    self.logger.warning(f"Skipping {name} - OpenAI API key not found")
                    continue
                
                rag_integration = RAGIntegration(
                    db_path=config["db_path"],
                    db_type=config["db_type"],
                    embedding_provider=config["embedding_provider"],
                    embedding_model=config["embedding_model"],
                    api_key=config.get("api_key"),
                    shared_memory=self.shared_memory
                )
                
                self.rag_integrations[name] = rag_integration
                self.logger.info(f"Successfully initialized RAG integration: {name}")
                
        except Exception as e:
            self.logger.error(f"Error initializing RAG integrations: {str(e)}")
    
    def _initialize_llm_integrations(self):
        """Initialize multiple LLM integrations with different providers."""
        try:
            for name, config in LLM_CONFIGS.items():
                self.logger.info(f"Initializing LLM integration: {name}")
                
                # Skip if API key is missing for paid providers
                if config["provider"] == "openai" and not config.get("api_key"):
                    self.logger.warning(f"Skipping {name} - API key not found")
                    continue
                if config["provider"] == "groq" and not config.get("api_key"):
                    self.logger.warning(f"Skipping {name} - API key not found")
                    continue
                if config["provider"] == "anthropic" and not config.get("api_key"):
                    self.logger.warning(f"Skipping {name} - API key not found")
                    continue
                
                try:
                    llm_integration = LLMIntegration(
                        provider=config["provider"],
                        model=config["model"],
                        api_key=config.get("api_key"),
                        **{k: v for k, v in config.items() if k not in ["provider", "model", "api_key"]}
                    )
                    
                    self.llm_integrations[name] = llm_integration
                    self.logger.info(f"Successfully initialized LLM integration: {name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to initialize {name}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error initializing LLM integrations: {str(e)}")
    
    def add_documents_to_vector_db(self, file_paths: List[str], rag_name: str = "faiss_local") -> bool:
        """Add documents to the specified vector database."""
        try:
            if rag_name not in self.rag_integrations:
                self.logger.error(f"RAG integration '{rag_name}' not found")
                return False
            
            rag_integration = self.rag_integrations[rag_name]
            result = rag_integration.add_documents(file_paths)
            
            # Log to shared memory
            self.shared_memory.add_entry("documents_added", {
                "files": file_paths,
                "rag_provider": rag_name,
                "success": result,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}")
            return False
    
    def search_documents(self, query: str, rag_name: str = "faiss_local", top_k: int = 5) -> Dict:
        """Search documents using the specified RAG integration."""
        try:
            if rag_name not in self.rag_integrations:
                self.logger.error(f"RAG integration '{rag_name}' not found")
                return {"status": "error", "message": f"RAG integration '{rag_name}' not found"}
            
            rag_integration = self.rag_integrations[rag_name]
            results = rag_integration.search(query, top_k=top_k)
            
            # Log to shared memory
            self.shared_memory.add_entry("search_performed", {
                "query": query,
                "rag_provider": rag_name,
                "results_count": len(results.get("results", [])),
                "timestamp": datetime.now().isoformat()
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def generate_response(self, prompt: str, llm_name: str = "openai_gpt4", context: Optional[str] = None) -> Dict:
        """Generate response using the specified LLM integration."""
        try:
            if llm_name not in self.llm_integrations:
                # Fallback to first available LLM
                if self.llm_integrations:
                    llm_name = list(self.llm_integrations.keys())[0]
                    self.logger.warning(f"LLM '{llm_name}' not found, using fallback: {llm_name}")
                else:
                    return {"status": "error", "message": "No LLM integrations available"}
            
            llm_integration = self.llm_integrations[llm_name]
            
            # Enhance prompt with context if provided
            if context:
                enhanced_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nPlease provide a comprehensive answer based on the context provided."
            else:
                enhanced_prompt = prompt
            
            result = llm_integration.execute(enhanced_prompt)
            
            # Log to shared memory
            self.shared_memory.add_entry("llm_response_generated", {
                "llm_provider": llm_name,
                "prompt_length": len(prompt),
                "context_provided": context is not None,
                "success": result.get("status") == "success",
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def rag_enhanced_query(self, query: str, rag_name: str = "faiss_local", llm_name: str = "openai_gpt4", top_k: int = 3) -> Dict:
        """Perform RAG-enhanced query combining document search with LLM generation."""
        try:
            # Step 1: Search relevant documents
            search_results = self.search_documents(query, rag_name, top_k)
            
            if search_results.get("status") == "error":
                return search_results
            
            # Step 2: Extract context from search results
            context_parts = []
            for result in search_results.get("results", []):
                content = result.get("content", "")
                score = result.get("score", 0)
                context_parts.append(f"[Relevance: {score:.3f}] {content}")
            
            context = "\n\n".join(context_parts)
            
            # Step 3: Generate response with context
            llm_result = self.generate_response(query, llm_name, context)
            
            # Step 4: Combine results
            combined_result = {
                "status": "success",
                "query": query,
                "rag_provider": rag_name,
                "llm_provider": llm_name,
                "search_results": search_results,
                "llm_response": llm_result,
                "context_used": context,
                "metadata": {
                    "search_results_count": len(search_results.get("results", [])),
                    "context_length": len(context),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Log to shared memory
            self.shared_memory.add_entry("rag_enhanced_query", {
                "query": query,
                "rag_provider": rag_name,
                "llm_provider": llm_name,
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Error in RAG-enhanced query: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def get_provider_status(self) -> Dict:
        """Get status of all initialized providers."""
        return {
            "rag_providers": {
                name: {
                    "db_type": config.vector_db_type,
                    "embedding_provider": config.embedding_provider,
                    "embedding_model": config.embedding_model,
                    "index_stats": config.get_index_stats()
                }
                for name, config in self.rag_integrations.items()
            },
            "llm_providers": {
                name: config.get_provider_info()
                for name, config in self.llm_integrations.items()
            }
        }


class DocumentAnalysisAgent(CustomTaskAgent):
    """Custom agent for document analysis using RAG and LLM integrations."""
    
    def __init__(self, task_manager, document_processor: AdvancedDocumentProcessor):
        super().__init__(function_path=None, task_manager=task_manager)
        self.document_processor = document_processor
        self.logger = logging.getLogger(__name__)
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute document analysis task."""
        try:
            task_type = task.metadata.get("task_type", "analyze")
            
            if task_type == "add_documents":
                return await self._add_documents_task(task)
            elif task_type == "search":
                return await self._search_task(task)
            elif task_type == "analyze":
                return await self._analyze_task(task)
            elif task_type == "summarize":
                return await self._summarize_task(task)
            else:
                return {"status": "error", "message": f"Unknown task type: {task_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing task {task.name}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _add_documents_task(self, task: Task) -> Dict[str, Any]:
        """Add documents to vector database."""
        file_paths = task.metadata.get("file_paths", [])
        rag_name = task.metadata.get("rag_provider", "faiss_local")
        
        if not file_paths:
            return {"status": "error", "message": "No file paths provided"}
        
        result = self.document_processor.add_documents_to_vector_db(file_paths, rag_name)
        
        return {
            "status": "success" if result else "error",
            "message": f"Added {len(file_paths)} documents to {rag_name}" if result else "Failed to add documents",
            "files_processed": file_paths,
            "rag_provider": rag_name
        }
    
    async def _search_task(self, task: Task) -> Dict[str, Any]:
        """Search documents in vector database."""
        query = task.metadata.get("query", "")
        rag_name = task.metadata.get("rag_provider", "faiss_local")
        top_k = task.metadata.get("top_k", 5)
        
        if not query:
            return {"status": "error", "message": "No query provided"}
        
        results = self.document_processor.search_documents(query, rag_name, top_k)
        
        return {
            "status": results.get("status", "success"),
            "search_results": results,
            "query": query,
            "rag_provider": rag_name
        }
    
    async def _analyze_task(self, task: Task) -> Dict[str, Any]:
        """Analyze documents using RAG-enhanced queries."""
        query = task.metadata.get("query", "")
        rag_name = task.metadata.get("rag_provider", "faiss_local")
        llm_name = task.metadata.get("llm_provider", "openai_gpt4")
        
        if not query:
            return {"status": "error", "message": "No query provided"}
        
        results = self.document_processor.rag_enhanced_query(query, rag_name, llm_name)
        
        return {
            "status": results.get("status", "success"),
            "analysis_results": results,
            "query": query,
            "providers_used": {
                "rag": rag_name,
                "llm": llm_name
            }
        }
    
    async def _summarize_task(self, task: Task) -> Dict[str, Any]:
        """Summarize previous analysis results."""
        analysis_results = task.metadata.get("analysis_results", {})
        llm_name = task.metadata.get("llm_provider", "openai_gpt4")
        
        if not analysis_results:
            return {"status": "error", "message": "No analysis results provided"}
        
        # Create summary prompt
        summary_prompt = f"""
        Please provide a comprehensive summary of the following analysis results:
        
        Query: {analysis_results.get('query', 'N/A')}
        
        Analysis Results: {analysis_results.get('llm_response', {}).get('output', 'No analysis available')}
        
        Please create a concise but comprehensive summary highlighting:
        1. Key findings
        2. Important insights
        3. Actionable recommendations
        4. Any limitations or areas for further investigation
        """
        
        summary_result = self.document_processor.generate_response(summary_prompt, llm_name)
        
        return {
            "status": summary_result.get("status", "success"),
            "summary": summary_result,
            "original_query": analysis_results.get('query', 'N/A'),
            "llm_provider": llm_name
        }


async def main():
    """Main function demonstrating the advanced RAG and LLM workflow."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Advanced RAG and LLM Workflow Example")
    
    try:
        # Initialize shared memory for observability
        shared_memory = SharedMemory()
        
        # Initialize task manager and workflow engine
        task_manager = TaskManager()
        
        # Initialize tracker for observability
        tracker = TrackerFactory.create_tracker("basic")
        
        workflow_engine = WorkflowEngine(
            task_manager=task_manager,
            tracker=tracker,
            workflow_id="advanced_rag_llm_workflow"
        )
        
        # Initialize document processor with multi-provider support
        document_processor = AdvancedDocumentProcessor(shared_memory)
        
        # Display available providers
        provider_status = document_processor.get_provider_status()
        logger.info("Available RAG Providers:")
        for name, info in provider_status["rag_providers"].items():
            logger.info(f"  - {name}: {info['db_type']} with {info['embedding_provider']}")
        
        logger.info("Available LLM Providers:")
        for name, info in provider_status["llm_providers"].items():
            logger.info(f"  - {name}: {info['provider']} - {info['model']}")
        
        # Create document analysis agent
        analysis_agent = DocumentAnalysisAgent(task_manager, document_processor)
        
        # Define sample document path (using existing Tesla document)
        sample_documents = [
            "/home/sunny-bedi/practise/Reason/data/tesla_q3_2024.pdf"
        ]
        
        # Create workflow tasks using the WorkflowEngine's add_task method
        logger.info("Adding tasks to workflow...")
        
        # Task 1: Add documents to vector database
        await workflow_engine.add_task(
            task_id="add_documents",
            task_type="data_ingestion",
            config={
                "agent_config": {
                    "db_path": "vector_db_advanced_example.index",
                    "db_type": "faiss",
                    "embedding_provider": "sentence_transformers",
                    "embedding_model": "all-MiniLM-L6-v2"
                },
                "params": {
                    "file_paths": sample_documents
                }
            }
        )
        
        # Task 2: Search financial data
        await workflow_engine.add_task(
            task_id="search_financial_data",
            task_type="data_retrieval",
            config={
                "agent_config": {
                    "db_path": "vector_db_advanced_example.index",
                    "db_type": "faiss",
                    "embedding_provider": "sentence_transformers",
                    "embedding_model": "all-MiniLM-L6-v2"
                },
                "params": {
                    "query": "What are Tesla's key financial metrics for Q3 2024?",
                    "top_k": 5
                }
            }
        )
        
        # Create LLM agents for workflow tasks
        analysis_llm = None
        summary_llm = None
        
        # Try to get the best available LLM for analysis
        if "openai_gpt4" in document_processor.llm_integrations:
            analysis_llm = document_processor.llm_integrations["openai_gpt4"]
        elif "groq_llama" in document_processor.llm_integrations:
            analysis_llm = document_processor.llm_integrations["groq_llama"]
        elif "local_ollama" in document_processor.llm_integrations:
            analysis_llm = document_processor.llm_integrations["local_ollama"]
        
        # Try to get a different LLM for summary (for variety)
        if "groq_llama" in document_processor.llm_integrations:
            summary_llm = document_processor.llm_integrations["groq_llama"]
        elif "openai_gpt4" in document_processor.llm_integrations:
            summary_llm = document_processor.llm_integrations["openai_gpt4"]
        elif "local_ollama" in document_processor.llm_integrations:
            summary_llm = document_processor.llm_integrations["local_ollama"]
        
        if not analysis_llm or not summary_llm:
            logger.error("No LLM integrations available for workflow tasks")
            return
        
        logger.info(f"Using {analysis_llm.provider}:{analysis_llm.model} for analysis")
        logger.info(f"Using {summary_llm.provider}:{summary_llm.model} for summary")
        
        # Task 3: Analyze financial performance
        await workflow_engine.add_task(
            task_id="analyze_performance",
            task_type="llm",
            config={
                "agent": analysis_llm,
                "params": {
                    "prompt": "Analyze Tesla's financial performance and growth trends based on the provided Q3 2024 data. Focus on key metrics, revenue growth, profitability, and market position."
                }
            }
        )
        
        # Task 4: Generate executive summary
        await workflow_engine.add_task(
            task_id="generate_summary",
            task_type="llm",
            config={
                "agent": summary_llm,
                "params": {
                    "prompt": "Create a comprehensive executive summary of Tesla's Q3 2024 financial analysis. Include key findings, insights, and strategic recommendations."
                }
            }
        )
        
        # Add dependencies
        await workflow_engine.add_dependency("add_documents", "search_financial_data")
        await workflow_engine.add_dependency("search_financial_data", "analyze_performance")
        await workflow_engine.add_dependency("analyze_performance", "generate_summary")
        
        logger.info("Added workflow tasks and dependencies")
        
        # Execute workflow
        logger.info("Starting workflow execution...")
        results = await workflow_engine.execute_workflow()
        
        # Display results
        logger.info("\n" + "="*50)
        logger.info("WORKFLOW EXECUTION RESULTS")
        logger.info("="*50)
        
        if results:
            for task_id, result in results.items():
                logger.info(f"\nTask: {task_id}")
                logger.info(f"Result: {result}")
        else:
            logger.info("No results returned from workflow execution")
        
        # Display shared memory entries
        logger.info("\n" + "="*50)
        logger.info("OBSERVABILITY DATA")
        logger.info("="*50)
        
        memory_keys = shared_memory.list_keys()
        for key in memory_keys:
            value = shared_memory.retrieve_entry(key)
            logger.info(f"{key}: {value}")
        
        # Display provider statistics
        logger.info("\n" + "="*50)
        logger.info("PROVIDER STATISTICS")
        logger.info("="*50)
        
        final_status = document_processor.get_provider_status()
        for rag_name, rag_info in final_status["rag_providers"].items():
            logger.info(f"\nRAG Provider: {rag_name}")
            logger.info(f"  Index Stats: {rag_info['index_stats']}")
        
        logger.info("\nWorkflow completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup resources
        if 'workflow_engine' in locals():
            await workflow_engine.cleanup()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
