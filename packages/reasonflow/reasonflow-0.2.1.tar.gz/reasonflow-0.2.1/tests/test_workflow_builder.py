import unittest
from reasonflow.orchestrator.workflow_builder import WorkflowBuilder

class TestWorkflowBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = WorkflowBuilder()
        self.test_config = {
            'tasks': {
                'task1': {
                    'type': 'llm',
                    'config': {'prompt': 'test'}
                },
                'task2': {
                    'type': 'data_retrieval',
                    'config': {'query': 'test'}
                }
            },
            'dependencies': [
                {'from': 'task1', 'to': 'task2'}
            ]
        }
        
    def test_create_workflow(self):
        workflow_id = self.builder.create_workflow(self.test_config)
        self.assertIsInstance(workflow_id, str)
        self.assertTrue(len(workflow_id) > 0)
        
    def test_execute_workflow(self):
        workflow_id = self.builder.create_workflow(self.test_config)
        results = self.builder.execute_workflow(workflow_id)
        self.assertIsInstance(results, dict)
        
    def test_stop_workflow(self):
        workflow_id = self.builder.create_workflow(self.test_config)
        self.builder.execute_workflow(workflow_id)
        result = self.builder.stop_workflow(workflow_id)
        self.assertTrue(result)
        
    def test_delete_workflow(self):
        workflow_id = self.builder.create_workflow(self.test_config)
        result = self.builder.delete_workflow(workflow_id)
        self.assertTrue(result)
        
    def test_get_workflow_status(self):
        workflow_id = self.builder.create_workflow(self.test_config)
        status = self.builder.get_workflow_status(workflow_id)
        self.assertEqual(status['status'], 'created')

if __name__ == '__main__':
    unittest.main() 