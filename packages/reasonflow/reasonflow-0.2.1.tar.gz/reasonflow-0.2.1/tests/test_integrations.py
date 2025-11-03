import unittest
import os
import tempfile
from reasonflow.integrations.rag_integrations import RAGIntegration
from reasonflow.integrations.api_key_manager import APIKeyManager

class TestRAGIntegration(unittest.TestCase):
    def setUp(self):
        self.rag = RAGIntegration()
        self.test_docs = [
            {"content": "This is a test document"},
            {"content": "Another test document"}
        ]
        
    def test_add_documents(self):
        result = self.rag.add_documents(self.test_docs)
        self.assertTrue(result)
        
    def test_search(self):
        self.rag.add_documents(self.test_docs)
        results = self.rag.search("test document")
        self.assertTrue(len(results) > 0)
        
    def test_save_load_index(self):
        self.rag.add_documents(self.test_docs)
        with tempfile.NamedTemporaryFile() as tmp:
            save_result = self.rag.save_index(tmp.name)
            self.assertTrue(save_result)
            
            new_rag = RAGIntegration()
            load_result = new_rag.load_index(tmp.name)
            self.assertTrue(load_result)
            
class TestAPIKeyManager(unittest.TestCase):
    def setUp(self):
        self.manager = APIKeyManager("test_service")
        
    def test_set_get_api_key(self):
        self.manager.set_api_key("test", "test_key", persist=False)
        key = self.manager.get_api_key("test")
        self.assertEqual(key, "test_key")
        
    def test_delete_api_key(self):
        self.manager.set_api_key("test", "test_key", persist=False)
        result = self.manager.delete_api_key("test")
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_api_key("test"))
        
    def test_list_providers(self):
        self.manager.set_api_key("test1", "key1", persist=False)
        self.manager.set_api_key("test2", "key2", persist=False)
        providers = self.manager.list_providers()
        self.assertIn("test1", providers)
        self.assertIn("test2", providers)

if __name__ == "__main__":
    unittest.main() 