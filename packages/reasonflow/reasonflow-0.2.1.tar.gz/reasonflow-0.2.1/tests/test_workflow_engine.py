import unittest
from reasonflow.orchestrator.workflow_engine import WorkflowEngine

class TestWorkflowEngine(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()
        
    def test_add_task(self):
        self.engine.add_task("task1", "llm", {"prompt": "test"})
        self.assertTrue("task1" in self.engine.workflow_graph.nodes)
        
    def test_add_dependency(self):
        self.engine.add_task("task1", "llm", {"prompt": "test"})
        self.engine.add_task("task2", "llm", {"prompt": "test2"})
        self.engine.add_dependency("task1", "task2")
        self.assertTrue(("task1", "task2") in self.engine.workflow_graph.edges)

if __name__ == "__main__":
    unittest.main() 