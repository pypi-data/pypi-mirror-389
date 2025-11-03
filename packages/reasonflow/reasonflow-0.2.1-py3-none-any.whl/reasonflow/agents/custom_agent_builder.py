from typing import Dict, Any, Type, Optional
from reasonflow.agents.llm_agent import LLMAgent
from reasonflow.agents.data_retrieval_agent import DataRetrievalAgent
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.agents.api_connector_agent import APIConnectorAgent

class CustomAgentBuilder:
    AGENT_TYPES = {
        "llm": LLMAgent,
        "data_retrieval": DataRetrievalAgent,
        "custom_task": CustomTaskAgent,
        "api_connector": APIConnectorAgent
    }
    
    def __init__(self):
        self.custom_agents: Dict[str, Type] = {}
        
    def register_agent_type(self, agent_type: str, agent_class: Type) -> None:
        """Register a new agent type"""
        try:
            if agent_type in self.AGENT_TYPES:
                raise ValueError(f"Agent type {agent_type} already exists")
                
            self.custom_agents[agent_type] = agent_class
            
        except Exception as e:
            print(f"Error registering agent type: {str(e)}")
            
    def create_agent(self, agent_type: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create an agent instance based on type and configuration"""
        try:
            # Extract agent configuration
            agent_config = config.get("agent_config", {})

            # For LLM agents, extract the agent instance from config
            if agent_type == "llm" and "agent" in config:
                return config["agent"]
            
            # Handle shared_memory specially - use the global instance if available
            if "shared_memory" in agent_config and isinstance(agent_config["shared_memory"], str):
                from reasonchain.memory import SharedMemory
                agent_config["shared_memory"] = SharedMemory()

            # For other agent types, create new instance with agent_config
            if agent_type in self.AGENT_TYPES:
                if not agent_config:
                    raise ValueError(f"Missing agent_config for {agent_type}")
                return self.AGENT_TYPES[agent_type](**agent_config)
            elif agent_type in self.custom_agents:
                return self.custom_agents[agent_type](**agent_config)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
                
        except Exception as e:
            print(f"Error creating agent: {str(e)}")
            return None
            
    def get_agent_types(self) -> Dict[str, Type]:
        """Get all available agent types"""
        return {**self.AGENT_TYPES, **self.custom_agents} 