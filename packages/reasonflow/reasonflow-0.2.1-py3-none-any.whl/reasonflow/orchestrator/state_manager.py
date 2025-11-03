from typing import Dict, Any, Optional
import json
import os
from datetime import datetime
import numpy as np
import threading

class StateManager:
    def __init__(self, storage_path: str = "workflow_states"):
        self.storage_path = storage_path
        self.current_states: Dict[str, Any] = {}
        self.lock = threading.Lock()

        os.makedirs(storage_path, exist_ok=True)

    def _serialize_config(self, config: Any) -> Any:
        """
        Recursively convert a config dictionary or value to a JSON-serializable format.
        Handles datetime objects, numpy types, and other complex objects.
        """
        if isinstance(config, datetime):
            # Convert datetime to ISO format string
            return config.isoformat()
        elif isinstance(config, dict):
            # Recursively process dictionaries
            return {key: self._serialize_config(value) for key, value in config.items()}
        elif isinstance(config, list):
            # Recursively process lists
            return [self._serialize_config(item) for item in config]
        elif isinstance(config, tuple):
            # Convert tuples to lists
            return [self._serialize_config(item) for item in config]
        elif isinstance(config, np.ndarray):
            # Convert numpy arrays to lists
            return config.tolist()
        elif isinstance(config, (np.floating, float)):
            # Convert numpy floats to Python floats
            return float(config)
        elif isinstance(config, (np.integer, int)):
            # Convert numpy integers to Python integers
            return int(config)
        elif isinstance(config, (np.bool_, bool)):
            # Convert numpy booleans to Python booleans
            return bool(config)
        elif hasattr(config, "__dict__"):
            # Convert objects with __dict__ to their string representation
            return str(config)
        elif isinstance(config, (str, bool, type(None))):
            # Return basic JSON serializable types as-is
            return config
        else:
            # Fallback: Convert other types to strings
            return str(config)


    def save_state(self, workflow_id: str, state: Dict) -> bool:
        """Save workflow state to storage."""
        try:
            with self.lock:
                file_path = os.path.join(self.storage_path, f"{workflow_id}.json")
            
                # Add timestamp
                state["last_updated"] = datetime.now().isoformat()
                
                # Serialize the state
                serializable_state = self._serialize_config(state)
                
                # Update in-memory state
                self.current_states[workflow_id] = serializable_state
                
                # Save to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(serializable_state, f, indent=2)
                return True
        except Exception as e:
            print(f"Error saving state: {str(e)}")
            return False
    
    def load_state(self, workflow_id: str) -> Dict:
        """Load workflow state from storage."""
        try:
            # Try to get from in-memory cache first
            if workflow_id in self.current_states:
                return self.current_states[workflow_id]
            
            # If not in memory, try to load from file
            state_path = os.path.join(self.storage_path, f"{workflow_id}.json")
            if os.path.exists(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.current_states[workflow_id] = state  # Cache the loaded state
                    return state
            return {}
        except Exception as e:
            print(f"Error loading state: {str(e)}")
            return {}

    def delete_state(self, workflow_id: str) -> bool:
        """Delete workflow state."""
        try:
            # Remove from memory
            if workflow_id in self.current_states:
                del self.current_states[workflow_id]
            
            # Remove file
            state_path = os.path.join(self.storage_path, f"{workflow_id}.json")
            if os.path.exists(state_path):
                os.remove(state_path)
            return True
        except Exception as e:
            print(f"Error deleting state: {str(e)}")
            return False 