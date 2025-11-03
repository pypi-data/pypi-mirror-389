import unittest
from reasonflow.agents.custom_task_agent import CustomTaskAgent
from reasonflow.agents.api_connector_agent import APIConnectorAgent
from reasonflow.agents.custom_agent_builder import CustomAgentBuilder

class TestCustomTaskAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CustomTaskAgent()
        
    def test_execute_missing_function(self):
        result = self.agent.execute({})
        self.assertEqual(result["status"], "error")
        
class TestAPIConnectorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = APIConnectorAgent("https://api.example.com")
        
    def test_build_url(self):
        result = self.agent.request("GET", "/test")
        self.assertEqual(result["status"], "error")  # Will fail as no real API
        
class TestCustomAgentBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = CustomAgentBuilder()
        
    def test_register_agent_type(self):
        class TestAgent:
            pass
            
        self.builder.register_agent_type("test", TestAgent)
        self.assertIn("test", self.builder.get_agent_types())
        
    def test_create_known_agent(self):
        agent = self.builder.create_agent("llm", {"model": "test"})
        self.assertIsNotNone(agent)

if __name__ == "__main__":
    unittest.main() 