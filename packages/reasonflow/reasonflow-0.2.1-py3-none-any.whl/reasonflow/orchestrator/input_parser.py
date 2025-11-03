from typing import Dict, Any
import yaml
import json
import os

class InputParser:
    @staticmethod
    def parse_workflow(workflow_path: str) -> Dict[str, Any]:
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                if workflow_path.endswith('.yaml') or workflow_path.endswith('.yml'):
                    return yaml.safe_load(f)
                elif workflow_path.endswith('.json'):
                    return json.load(f)
                else:
                    raise ValueError("Unsupported file format. Use .yaml, .yml, or .json")
        except Exception as e:
            print(f"Error parsing workflow file: {str(e)}")
            return {}
    
    @staticmethod
    def validate_workflow(workflow: Dict) -> bool:
        required_fields = ['tasks', 'dependencies']
        try:
            return all(field in workflow for field in required_fields)
        except Exception as e:
            print(f"Error validating workflow: {str(e)}")
            return False 