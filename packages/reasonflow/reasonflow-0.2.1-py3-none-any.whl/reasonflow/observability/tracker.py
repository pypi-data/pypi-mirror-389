from datetime import datetime
from typing import List, Dict, Optional


class TaskTracker:
    def __init__(self, shared_memory: None):
        self.task_logs: List[Dict] = []
        self.shared_memory = shared_memory


    def log(self, task_id: str, task_name: str, status: str):
        """Log a task with its ID, name, status, and timestamp."""
        log_entry = {
            "task_id": task_id,
            "task_name": task_name,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self.task_logs.append(log_entry)
        # Save log to shared memory
        if self.shared_memory:
            existing_logs = self.shared_memory.retrieve_entry("task_logs") or []
            existing_logs.append(log_entry)
            self.shared_memory.add_entry("task_logs", existing_logs)

        print(f"Task log updated: {log_entry}")

    def get_logs(self) -> List[Dict]:
        """Retrieve all task logs."""
        return self.task_logs

    def filter_logs(self, task_id: Optional[str] = None, task_name: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """
        Filter logs by task ID, name, or status.
        :param task_id: Filter logs by task ID.
        :param task_name: Filter logs by task name.
        :param status: Filter logs by status.
        :return: Filtered list of logs.
        """
        filtered_logs = self.task_logs
        if task_id:
            filtered_logs = [log for log in filtered_logs if log["task_id"] == task_id]
        if task_name:
            filtered_logs = [log for log in filtered_logs if log["task_name"] == task_name]
        if status:
            filtered_logs = [log for log in filtered_logs if log["status"] == status]
        return filtered_logs

    def save_logs(self, file_path: str):
        """Save logs to a file."""
        try:
            with open(file_path, "w") as file:
                import json
                json.dump(self.task_logs, file, indent=4)
            print(f"Logs saved to {file_path}")
        except Exception as e:
            print(f"Error saving logs: {str(e)}")

    def load_logs(self, file_path: str):
        """Load logs from a file."""
        try:
            with open(file_path, "r") as file:
                import json
                self.task_logs = json.load(file)
            print(f"Logs loaded from {file_path}")
        except Exception as e:
            print(f"Error loading logs: {str(e)}")


if __name__ == "__main__":
    task_tracker = TaskTracker()

    # Log some tasks
    task_tracker.log(task_id="1", task_name="Task1", status="pending")
    task_tracker.log(task_id="2", task_name="Task2", status="completed")
    task_tracker.log(task_id="3", task_name="Task3", status="failed")

    # Retrieve all logs
    print("\nAll Logs:")
    print(task_tracker.get_logs())

    # Filter logs
    print("\nFiltered Logs (status='completed'):")
    print(task_tracker.filter_logs(status="completed"))

    # Save logs to a file
    task_tracker.save_logs("task_logs.json")

    # Load logs from a file
    task_tracker.load_logs("task_logs.json")
