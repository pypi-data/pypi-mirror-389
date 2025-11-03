import unittest
import os
import tempfile
from reasonflow.persistence.document_management import DocumentManager
from reasonflow.persistence.versioning import VersionManager

class TestDocumentManager(unittest.TestCase):
    def setUp(self):
        self.doc_manager = DocumentManager(storage_provider="minio")
        self.test_content = "This is a test document"
        
        # Create temporary test file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self.temp_file.write(self.test_content)
        self.temp_file.close()
        
    def tearDown(self):
        os.unlink(self.temp_file.name)
        
    def test_upload_document(self):
        doc_id = self.doc_manager.upload_document(
            self.temp_file.name,
            {"title": "Test Document"}
        )
        self.assertIsNotNone(doc_id)
        
    def test_search_documents(self):
        self.doc_manager.upload_document(
            self.temp_file.name,
            {"title": "Test Document"}
        )
        results = self.doc_manager.search_documents("test document")
        self.assertTrue(len(results) > 0)
        
class TestVersionManager(unittest.TestCase):
    def setUp(self):
        self.version_manager = VersionManager()
        self.test_data = {"name": "test", "value": 1}
        
    def test_create_version(self):
        version_id = self.version_manager.create_version(
            "test-entity",
            "workflow",
            self.test_data
        )
        self.assertIsNotNone(version_id)
        
    def test_get_latest_version(self):
        self.version_manager.create_version(
            "test-entity",
            "workflow",
            self.test_data
        )
        version = self.version_manager.get_latest_version(
            "test-entity",
            "workflow"
        )
        self.assertEqual(version["data"], self.test_data)
        
    def test_list_versions(self):
        self.version_manager.create_version(
            "test-entity",
            "workflow",
            self.test_data
        )
        versions = self.version_manager.list_versions(
            "test-entity",
            "workflow"
        )
        self.assertTrue(len(versions) > 0)

if __name__ == "__main__":
    unittest.main() 