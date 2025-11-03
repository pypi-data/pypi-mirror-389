from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import subprocess
import requests
import json
import os
import asyncio
from datetime import datetime
from reasonflow.integrations.llm_integrations import LLMIntegration
from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.integrations.web_browser_integration import WebBrowserIntegration
import logging

class BaseTask(ABC):
    """Base class for all task types"""
    
    @abstractmethod
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pass

class ShellTask(BaseTask):
    """Execute shell commands"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        command = config.get("command")
        cwd = config.get("cwd", os.getcwd())
        env = config.get("env", os.environ.copy())
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env
            )
            stdout, stderr = await process.communicate()
            
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "return_code": process.returncode
            }
        except Exception as e:
            return {"error": str(e)}

class HTTPTask(BaseTask):
    """Make HTTP requests"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        method = config.get("method", "GET")
        url = config.get("url")
        headers = config.get("headers", {})
        data = config.get("data")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=data if method == "GET" else None
            )
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.json() if response.headers.get("content-type") == "application/json" else response.text
            }
        except Exception as e:
            return {"error": str(e)}

class PythonTask(BaseTask):
    """Execute Python code"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        code = config.get("code")
        globals_dict = {}
        locals_dict = {}
        
        try:
            exec(code, globals_dict, locals_dict)
            return {
                "result": locals_dict.get("result"),
                "locals": {k: v for k, v in locals_dict.items() if not k.startswith("_")}
            }
        except Exception as e:
            return {"error": str(e)}

class FileSystemTask(BaseTask):
    """Perform file system operations"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        operation = config.get("operation")
        path = config.get("path")
        
        try:
            if operation == "read":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content}
            elif operation == "write":
                content = config.get("content", "")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True}
            elif operation == "delete":
                os.remove(path)
                return {"success": True}
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"error": str(e)}

class DatabaseTask(BaseTask):
    """Execute database operations"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        db_type = config.get("db_type")
        operation = config.get("operation")
        query = config.get("query")
        params = config.get("params", {})
        
        # This is a placeholder - in real implementation, you'd want to use proper
        # database connectors based on db_type
        try:
            return {
                "success": True,
                "operation": operation,
                "query": query,
                "params": params
            }
        except Exception as e:
            return {"error": str(e)}

class MessageQueueTask(BaseTask):
    """Interact with message queues"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        queue_type = config.get("queue_type")
        operation = config.get("operation")
        message = config.get("message")
        queue = config.get("queue")
        
        # This is a placeholder - in real implementation, you'd want to use proper
        # message queue clients based on queue_type
        try:
            return {
                "success": True,
                "operation": operation,
                "queue": queue,
                "message": message
            }
        except Exception as e:
            return {"error": str(e)}

class LLMTask(BaseTask):
    """Execute LLM tasks using various providers with updated ReasonChain integration"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            agent_config = config.get("agent_config", {})
            params = config.get("params", {})

            if "agent" in config and isinstance(config["agent"], LLMIntegration):
                agent = config["agent"]
            else:
                # Initialize LLM agent with new ReasonChain provider system
                provider = agent_config.get("provider", "openai")
                model = agent_config.get("model", "gpt-4o")
                api_key = agent_config.get("api_key")
                
                # Extract additional provider-specific parameters
                provider_params = {k: v for k, v in agent_config.items() 
                                if k not in ["provider", "model", "api_key"]}
                
                agent = LLMIntegration(
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    **provider_params
                )
            
            # Execute LLM task
            prompt = params.get("prompt", "")
            if not prompt:
                return {
                    "status": "error",
                    "message": "No prompt provided in params",
                    "metadata": {"task_type": "llm"}
                }
            
            # Remove prompt from params to pass other parameters
            other_params = {k: v for k, v in params.items() if k != "prompt"}
            
            # Use the new execute method which returns a standardized response
            result = agent.execute(prompt, **other_params)
            
            # Ensure consistent response format
            if not isinstance(result, dict):
                result = {"status": "success", "output": result}
            
            # Add task metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["task_type"] = "llm"
            
            return result
            
        except Exception as e:
            logging.error(f"Error in LLM task execution: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "metadata": {
                    "task_type": "llm",
                    "error": str(e)
                }
            }
class DataIngestionTask(BaseTask):
    """Execute data ingestion tasks using vector databases with updated RAG integration"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            agent_config = config.get("agent_config", {})
            params = config.get("params", {})
            
            # Check if we have a RAG integration instance or need to create one
            if "rag_integration" in config:
                rag_integration = config["rag_integration"]
            else:
                # Import RAGIntegration here to avoid circular imports
                from reasonflow.integrations.rag_integrations import RAGIntegration
                
                # Initialize RAG integration with new ReasonChain system
                db_path = agent_config.get("db_path", "vector_db.index")
                db_type = agent_config.get("db_type", "faiss")
                embedding_provider = agent_config.get("embedding_provider", "sentence_transformers")
                embedding_model = agent_config.get("embedding_model", "all-MiniLM-L6-v2")
                api_key = agent_config.get("api_key")
                
                # Extract additional parameters
                rag_params = {k: v for k, v in agent_config.items() 
                            if k not in ["db_path", "db_type", "embedding_provider", "embedding_model", "api_key"]}
                
                rag_integration = RAGIntegration(
                    db_path=db_path,
                    db_type=db_type,
                    embedding_provider=embedding_provider,
                    embedding_model=embedding_model,
                    api_key=api_key,
                    **rag_params
                )
            
            # Execute data ingestion task
            file_paths = params.get("file_paths", [])
            texts = params.get("texts", [])
            metadata = params.get("metadata", None)
            
            if file_paths:
                # Add documents from file paths
                result = rag_integration.add_documents(file_paths)
                return {
                    "status": "success" if result else "error",
                    "message": f"Added {len(file_paths)} documents" if result else "Failed to add documents",
                    "files_processed": file_paths,
                    "metadata": {"task_type": "data_ingestion"}
                }
            elif texts:
                # Add raw text data
                result = rag_integration.add_raw_data(texts, metadata)
                return {
                    "status": "success" if result else "error",
                    "message": f"Added {len(texts)} text documents" if result else "Failed to add text documents",
                    "texts_processed": len(texts),
                    "metadata": {"task_type": "data_ingestion"}
                }
            else:
                return {
                    "status": "error",
                    "message": "No file_paths or texts provided in params",
                    "metadata": {"task_type": "data_ingestion"}
                }
            
        except Exception as e:
            logging.error(f"Error in data ingestion task execution: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "metadata": {
                    "task_type": "data_ingestion",
                    "error": str(e)
                }
            }
        
        
class DataRetrievalTask(BaseTask):
    """Execute data retrieval tasks using vector databases with updated RAG integration"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            agent_config = config.get("agent_config", {})
            params = config.get("params", {})
            
            # Check if we have a RAG integration instance or need to create one
            if "rag_integration" in config:
                rag_integration = config["rag_integration"]
            else:
                # Import RAGIntegration here to avoid circular imports
                from reasonflow.integrations.rag_integrations import RAGIntegration
                
                # Initialize RAG integration with new ReasonChain system
                db_path = agent_config.get("db_path", "vector_db.index")
                db_type = agent_config.get("db_type", "faiss")
                embedding_provider = agent_config.get("embedding_provider", "sentence_transformers")
                embedding_model = agent_config.get("embedding_model", "all-MiniLM-L6-v2")
                api_key = agent_config.get("api_key")
                
                # Extract additional parameters
                rag_params = {k: v for k, v in agent_config.items() 
                            if k not in ["db_path", "db_type", "embedding_provider", "embedding_model", "api_key"]}
                
                rag_integration = RAGIntegration(
                    db_path=db_path,
                    db_type=db_type,
                    embedding_provider=embedding_provider,
                    embedding_model=embedding_model,
                    api_key=api_key,
                    **rag_params
                )
            
            # Execute data retrieval task
            query = params.get("query", "")
            top_k = params.get("top_k", 5)
            
            if not query:
                return {
                    "status": "error",
                    "message": "No query provided in params",
                    "metadata": {"task_type": "data_retrieval"}
                }
            
            # Use the new search method
            result = rag_integration.search(query, top_k=top_k)
            
            # Ensure consistent response format
            if not isinstance(result, dict):
                result = {"status": "success", "results": result}
            
            # Add task metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["task_type"] = "data_retrieval"
            
            return result
            
        except Exception as e:
            logging.error(f"Error in data retrieval task execution: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "metadata": {
                    "task_type": "data_retrieval",
                    "error": str(e)
                }
            }

class BrowserTask(BaseTask):
    """Execute browser automation tasks using WebBrowserIntegration"""
    async def execute(self, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Get the actions from the config
            actions = config.get("config", {}).get("actions", []) or config.get("actions", [])
            logging.info(f"Executing browser task with {len(actions)} actions")
            
            # Initialize browser integration
            browser = WebBrowserIntegration(
                headless=True,  # Always headless for now
                browser_type="chromium",
                timeout=30000,
                user_agent=None,
                proxy=None
            )
            
            async with browser:
                results = {}
                extracted_data = {}  # Store extracted data for use across actions
                
                for action in actions:
                    action_type = action.get("action")
                    logging.info(f"Executing browser action: {action_type}")
                    
                    if action_type == "navigate":
                        results["navigation"] = await browser.navigate(action.get("url"))
                        logging.info(f"Navigation completed to {action.get('url')}")
                    elif action_type == "screenshot":
                        success = await browser.screenshot(
                            path=action.get("path"),
                            full_page=action.get("full_page", True)
                        )
                        results["screenshot"] = {"success": success}
                    elif action_type == "extract_links":
                        links = await browser.extract_links(action.get("selector", "a"))
                        results["links"] = links
                    elif action_type == "fill_form":
                        form_result = await browser.fill_form(
                            form_data=action.get("form_data", {}),
                            submit_selector=action.get("submit_selector"),
                            wait_for_navigation=action.get("wait_for_navigation", True)
                        )
                        results["form"] = form_result
                    elif action_type == "extract_data":
                        selectors = action.get("selectors", {})
                        logging.info(f"Extracting data with selectors: {selectors}")
                        
                        # Get attributes to extract
                        extract_attributes = action.get("extract_attributes", {})
                        logging.info(f"Extracting attributes: {extract_attributes}")
                        
                        data = await browser.extract_structured_data(
                            selectors=selectors,
                            schema=action.get("schema"),
                            transform=action.get("transform"),
                            wait_for_selectors=action.get("wait_for_selectors", True),
                            extract_attributes=extract_attributes
                        )
                        #logging.info(f"Extracted data: {data}")
                        
                        results["extracted_data"] = data
                        extracted_data.update(data.get("data", {}))
                        
                        # Store result if specified
                        if action.get("store_result"):
                            results[action["store_result"]] = data
                            logging.info(f"Stored extracted data in {action['store_result']}")
                            
                    elif action_type == "validate":
                        config = action.get("config", {})
                        input_value = config.get("input")
                        logging.info(f"Validating input: {input_value}")
                        if isinstance(input_value, str) and input_value.startswith("${"):
                            # Handle variable references like ${extracted_data.data.q3_link.href}
                            parts = input_value[2:-1].split(".")  # Remove ${ and } and split
                            value = results
                            for part in parts:
                                value = value.get(part, {})
                                logging.info(f"Resolving part {part}, current value: {value}")
                            if not value:
                                raise ValueError(f"Failed to resolve value for {input_value}")
                            
                            # Store validated URL
                            results["validated_url"] = value
                            logging.info(f"Stored validated URL: {value}")
                            
                    elif action_type == "analyze":
                        analysis = await browser.analyze_content(
                            analysis_types=action.get("analysis_types", ["readability", "sentiment", "keywords"]),
                            options=action.get("options")
                        )
                        results["analysis"] = analysis
                    elif action_type == "download":
                        config = action.get("config", {})
                        url = config.get("url")
                        logging.info(f"Processing download with URL reference: {url}")
                        
                        if isinstance(url, str) and url.startswith("${"):
                            # Handle variable references
                            parts = url[2:-1].split(".")
                            value = results
                            for part in parts:
                                value = value.get(part, {})
                                logging.info(f"Resolving download URL part {part}, current value: {value}")
                            
                            if not value or not isinstance(value, str):
                                raise ValueError(f"Failed to resolve download URL from {url}")
                            url = value
                            
                        if not url:
                            raise ValueError("No download URL provided")
                            
                        logging.info(f"Attempting to download from URL: {url}")
                        download_path = config.get("download_path")
                        filename = config.get("filename")
                        logging.info(f"Download path: {download_path}, filename: {filename}")
                        
                        # Create download directory if it doesn't exist
                        if download_path:
                            os.makedirs(download_path, exist_ok=True)
                            logging.info(f"Created download directory: {download_path}")
                        
                        download = await browser.download_file(
                            url=url,
                            save_path=download_path,  # Use save_path as that's what WebBrowserIntegration expects
                            filename=filename
                        )
                        logging.info(f"Download result: {download['status']}")
                        results["download"] = download

                # logging.info(f"Browser task completed with results: {results}")
                return {
                    "status": "success",
                    "results": results
                }
                
        except Exception as e:
            error_msg = f"Browser task failed: {str(e)}"
            logging.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "metadata": {
                    "task_type": "browser",
                    "error": str(e)
                }
            }

# Register all available task types
TASK_TYPES = {
    "shell": ShellTask,
    "http": HTTPTask,
    "python": PythonTask,
    "filesystem": FileSystemTask,
    "database": DatabaseTask,
    "messagequeue": MessageQueueTask,
    "llm": LLMTask,
    "data_retrieval": DataRetrievalTask,
    "browser": BrowserTask,
    "data_ingestion": DataIngestionTask
} 
