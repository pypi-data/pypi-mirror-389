from typing import Dict, Any, Optional, List
import logging
import asyncio
from reasonchain.memory import SharedMemory
from reasonflow.integrations.web_browser_integration import WebBrowserIntegration
from reasonflow.observability.tracker import TaskTracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebBrowserAgent:
    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        timeout: int = 30000,
        user_agent: Optional[str] = None,
        proxy: Optional[Dict[str, str]] = None,
        shared_memory: Optional[SharedMemory] = None,
        task_tracker: Optional[TaskTracker] = None
    ):
        """Initialize web browser agent.
        
        Args:
            headless: Whether to run browser in headless mode
            browser_type: Type of browser to use
            timeout: Page timeout in milliseconds
            user_agent: Custom user agent string
            proxy: Proxy configuration
            shared_memory: Optional shared memory instance
            task_tracker: Optional task tracker instance
        """
        self.config = {
            "headless": headless,
            "browser_type": browser_type,
            "timeout": timeout,
            "user_agent": user_agent,
            "proxy": proxy
        }
        self.shared_memory = shared_memory or SharedMemory()
        self.task_tracker = task_tracker or TaskTracker()
        self.browser: Optional[WebBrowserIntegration] = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self.browser:
            self.browser = WebBrowserIntegration(**self.config)
            await self.browser.start()

    async def execute(self, action: str, params: Dict[str, Any], task_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a web browser action.
        
        Args:
            action: Action to perform (navigate, extract_links, screenshot, execute_script, download_file)
            params: Parameters for the action
            task_id: Optional task ID for tracking
            
        Returns:
            Dictionary containing action results
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Initialize browser if needed
            await self._ensure_browser()
            
            # Track task start
            if task_id:
                self.task_tracker.log(task_id, action, "started")
            
            # Execute requested action
            if action == "navigate":
                result = await self.browser.navigate(params["url"])
                
                # Store results in shared memory
                if self.shared_memory:
                    self.shared_memory.store(f"page_content_{task_id}", {
                        "url": params["url"],
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {})
                    })
                    
            elif action == "extract_links":
                result = await self.browser.extract_links(
                    params.get("selector", "a")
                )
                
            elif action == "screenshot":
                success = await self.browser.screenshot(
                    params["path"],
                    params.get("full_page", True)
                )
                result = {"status": "success" if success else "error"}
                
            elif action == "execute_script":
                script_result = await self.browser.execute_script(params["script"])
                result = {
                    "status": "success",
                    "result": script_result
                }

            elif action == "download_file":
                result = await self.browser.download_file(
                    url=params["url"],
                    download_path=params["download_path"],
                    filename=params.get("filename"),
                    timeout=params.get("timeout", 30000),
                    check_mime_types=params.get("check_mime_types", True),
                    allowed_mime_types=params.get("allowed_mime_types")
                )
                
                # Store download result in shared memory
                if self.shared_memory and result["status"] == "success":
                    self.shared_memory.store(f"download_result_{task_id}", {
                        "file_path": result["file_path"],
                        "filename": result["filename"],
                        "metadata": result["metadata"]
                    })
                
            else:
                raise ValueError(f"Unknown action: {action}")
            
            # Calculate execution time
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Add execution metadata
            result["metadata"] = {
                **(result.get("metadata", {})),
                "execution_time": execution_time,
                "action": action,
                "task_id": task_id
            }
            
            # Track task completion
            if task_id:
                self.task_tracker.log(task_id, action, "completed")
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing {action}: {str(e)}"
            logger.error(error_msg)
            
            # Track task failure
            if task_id:
                self.task_tracker.log(task_id, action, "failed", error=str(e))
            
            # Store error in shared memory
            if self.shared_memory:
                self.shared_memory.store(f"browser_error_{task_id}", {
                    "action": action,
                    "error": str(e),
                    "params": params
                })
            
            return {
                "status": "error",
                "message": error_msg,
                "metadata": {
                    "execution_time": asyncio.get_event_loop().time() - start_time,
                    "action": action,
                    "task_id": task_id,
                    "error": str(e)
                }
            }

    async def cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None 