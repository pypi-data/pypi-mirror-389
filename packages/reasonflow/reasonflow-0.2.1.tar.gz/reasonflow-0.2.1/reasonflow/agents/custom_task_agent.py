from typing import Dict, Any, Callable, Optional
import importlib.util
from reasonflow.tasks.task_manager import TaskManager
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class CustomTaskAgent:
    def __init__(self, function_path: Optional[str] = None, task_manager: Optional[TaskManager] = None, shared_memory=None):
        """
        Initialize the CustomTaskAgent.
        :param function_path: Path to the custom function script.
        :param task_manager: Optional TaskManager instance.
        :param shared_memory: Optional shared memory for task results and logs.
        """
        self.function_path = function_path
        self.task_manager = task_manager  # Integrate with Task Manager
        self.shared_memory = shared_memory
        self.loaded_function: Optional[Callable] = None

    def load_function(self) -> None:
        """
        Dynamically load a function from the provided file path.
        """
        try:
            if not self.function_path or not self.function_path.endswith('.py'):
                raise ValueError("A valid Python function file path must be provided.")

            # Load Python function dynamically
            spec = importlib.util.spec_from_file_location("custom_module", self.function_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_function = getattr(module, "execute", None)
                if not self.loaded_function:
                    raise AttributeError("The custom function file does not define an 'execute' function.")
            else:
                raise ImportError("Failed to load the custom function module.")
        except Exception as e:
            error_message = f"Error loading custom function: {str(e)}"
            logging.error(error_message)
            if self.shared_memory:
                self.shared_memory.store("function_load_error", error_message)
            raise

    def execute(self, params: Dict[str, Any]) -> Dict:
        """
        Execute the custom function with provided parameters.
        :param params: Parameters for the function.
        :return: Execution status and result or error message.
        """
        try:
            if not self.loaded_function:
                logging.info("Loading the custom function before execution.")
                self.load_function()

            if not self.loaded_function:
                raise RuntimeError("Function not loaded. Unable to execute.")

            # Validate and update task status
            task_id = params.get("task_id")
            if self.task_manager and task_id:
                self.task_manager.update_task_status(task_id, "in_progress")

            # Execute the function
            logging.info(f"Executing custom task with parameters: {params}")
            result = self.loaded_function(**params)

            # Save results in shared memory
            if self.shared_memory:
                self.shared_memory.store("custom_task_result", {"task_id": task_id, "result": result})

            # Update task status to completed
            if self.task_manager and task_id:
                self.task_manager.update_task_status(task_id, "completed")

            logging.info(f"Task {task_id} executed successfully.")
            return {"status": "success", "result": result}

        except Exception as e:
            error_message = f"Error executing custom task: {str(e)}"
            logging.error(error_message)

            # Store error details in shared memory
            if self.shared_memory:
                self.shared_memory.store("custom_task_error", {"task_id": params.get("task_id"), "error": error_message})

            # Update task status to failed
            task_id = params.get("task_id")
            if self.task_manager and task_id:
                self.task_manager.update_task_status(task_id, "failed")

            return {"status": "error", "message": error_message}