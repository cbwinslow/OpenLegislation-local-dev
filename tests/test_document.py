import unittest
import datetime
from models.document import Document, DocumentModel

class TestDocument(unittest.TestCase):

    def test_document_creation(self):
        doc = Document(
            source="test_source",
            url="http://example.com",
            title="Test Title",
            description="Test Description",
            pub_date=datetime.datetime(2023, 1, 1),
            content="Test Content",
            doc_metadata={"key": "value"}
        )
        self.assertEqual(doc.source, "test_source")
        self.assertEqual(doc.url, "http://example.com")
        self.assertEqual(doc.title, "Test Title")
        self.assertEqual(doc.description, "Test Description")
        self.assertEqual(doc.pub_date, datetime.datetime(2023, 1, 1))
        self.assertEqual(doc.content, "Test Content")
        self.assertEqual(doc.doc_metadata, {"key": "value"})
        self.assertIsNotNone(doc.created_at)

    def test_pydantic_model(self):
        doc_data = {
            "source": "pydantic_source",
            "url": "http://pydantic.example.com",
            "title": "Pydantic Title",
            "description": "Pydantic Description",
            "pub_date": "2023-01-01T12:00:00",
            "content": "Pydantic Content",
            "doc_metadata": {"pydantic_key": "pydantic_value"}
        }
        doc_model = DocumentModel(**doc_data)
        self.assertEqual(doc_model.source, "pydantic_source")
        self.assertEqual(doc_model.url, "http://pydantic.example.com")
        self.assertEqual(doc_model.title, "Pydantic Title")
        self.assertEqual(doc_model.pub_date, datetime.datetime(2023, 1, 1, 12, 0, 0))

if __name__ == '__main__':
    unittest.main()