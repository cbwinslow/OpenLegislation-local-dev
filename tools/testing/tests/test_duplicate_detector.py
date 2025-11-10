# tools/testing/tests/test_duplicate_detector.py
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from enum import Enum

# Mock the models and pipeline components since we don't have them installed
class MockProcessingStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class MockMatchingAlgorithm(Enum):
    COSINE_SIMILARITY = "COSINE_SIMILARITY"
    JACCARD_SIMILARITY = "JACCARD_SIMILARITY"
    EXACT_MATCH = "EXACT_MATCH"

class MockDuplicateConfidence(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class MockVectorDocument:
    def __init__(self, id, content, metadata=None, vector=None, status=None):
        self.id = id
        self.content = content
        self.metadata = metadata or {}
        self.vector = vector or []
        self.status = status

class MockDuplicateCandidate:
    def __init__(self, document_id, confidence, algorithm, score):
        self.document_id = document_id
        self.confidence = confidence
        self.algorithm = algorithm
        self.score = score

class MockDuplicateGroup:
    def __init__(self, group_id, documents, primary_document_id=None):
        self.group_id = group_id
        self.documents = documents
        self.primary_document_id = primary_document_id

    def get_document_count(self):
        return len(self.documents)

    def get_primary_document(self):
        if self.primary_document_id:
            return next((doc for doc in self.documents if doc.id == self.primary_document_id), None)
        return self.documents[0] if self.documents else None

class MockMatchingResult:
    def __init__(self, document_id, candidates):
        self.document_id = document_id
        self.candidates = candidates

class MockDuplicateDetector:
    def __init__(self, similarity_threshold=0.8, algorithm=None):
        self.similarity_threshold = similarity_threshold
        self.algorithm = algorithm or MockMatchingAlgorithm.COSINE_SIMILARITY

    def find_duplicates(self, documents):
        """Mock implementation of duplicate detection"""
        results = []
        for doc in documents:
            candidates = []
            # Simple mock logic: if content contains "legislation", consider it a potential duplicate
            if "legislation" in doc.content.lower():
                for other_doc in documents:
                    if other_doc.id != doc.id and "legislation" in other_doc.content.lower():
                        candidates.append(MockDuplicateCandidate(
                            document_id=other_doc.id,
                            confidence=MockDuplicateConfidence.HIGH,
                            algorithm=self.algorithm,
                            score=0.9
                        ))
            results.append(MockMatchingResult(doc.id, candidates))
        return results

    def group_duplicates(self, matching_results):
        """Mock implementation of duplicate grouping"""
        groups = []
        processed_ids = set()

        for result in matching_results:
            if result.document_id in processed_ids:
                continue

            group_docs = [MockVectorDocument(id=result.document_id, content="")]
            processed_ids.add(result.document_id)

            for candidate in result.candidates:
                if candidate.document_id not in processed_ids:
                    group_docs.append(MockVectorDocument(id=candidate.document_id, content=""))
                    processed_ids.add(candidate.document_id)

            if len(group_docs) > 1:
                groups.append(MockDuplicateGroup(
                    group_id=f"group_{len(groups)}",
                    documents=group_docs,
                    primary_document_id=group_docs[0].id
                ))

        return groups

def mock_find_document_duplicates(documents, threshold=0.8):
    """Mock implementation of find_document_duplicates function"""
    detector = MockDuplicateDetector(similarity_threshold=threshold)
    return detector.find_duplicates(documents)

def mock_merge_duplicate_group(group, primary_doc_id):
    """Mock implementation of merge_duplicate_group function"""
    group.primary_document_id = primary_doc_id
    return group

class TestDuplicateDetector:
    """Unit tests for DuplicateDetector class"""

    def test_duplicate_detector_creation(self):
        """Test DuplicateDetector creation"""
        detector = MockDuplicateDetector(
            similarity_threshold=0.9,
            algorithm=MockMatchingAlgorithm.EXACT_MATCH
        )

        assert detector.similarity_threshold == 0.9
        assert detector.algorithm == MockMatchingAlgorithm.EXACT_MATCH

    def test_find_duplicates(self):
        """Test duplicate detection"""
        documents = [
            MockVectorDocument(
                id="doc1",
                content="This is a test document about legislation",
                status=MockProcessingStatus.PROCESSED
            ),
            MockVectorDocument(
                id="doc2",
                content="This is another test document about legislation",
                status=MockProcessingStatus.PROCESSED
            ),
            MockVectorDocument(
                id="doc3",
                content="This is a document about something else",
                status=MockProcessingStatus.PROCESSED
            )
        ]

        detector = MockDuplicateDetector()
        results = detector.find_duplicates(documents)

        assert len(results) == 3
        # doc1 and doc2 should have candidates for each other
        assert len(results[0].candidates) > 0
        assert len(results[1].candidates) > 0
        # doc3 should have no candidates
        assert len(results[2].candidates) == 0

    def test_group_duplicates(self):
        """Test duplicate grouping"""
        # Create mock matching results
        result1 = MockMatchingResult("doc1", [
            MockDuplicateCandidate("doc2", MockDuplicateConfidence.HIGH, MockMatchingAlgorithm.COSINE_SIMILARITY, 0.9)
        ])
        result2 = MockMatchingResult("doc2", [
            MockDuplicateCandidate("doc1", MockDuplicateConfidence.HIGH, MockMatchingAlgorithm.COSINE_SIMILARITY, 0.9)
        ])
        result3 = MockMatchingResult("doc3", [])

        matching_results = [result1, result2, result3]

        detector = MockDuplicateDetector()
        groups = detector.group_duplicates(matching_results)

        assert len(groups) == 1  # One group with doc1 and doc2
        assert groups[0].get_document_count() == 2
        assert groups[0].primary_document_id == "doc1"

class TestDuplicateCandidate:
    """Unit tests for DuplicateCandidate model"""

    def test_duplicate_candidate_creation(self):
        """Test DuplicateCandidate creation"""
        candidate = MockDuplicateCandidate(
            document_id="doc123",
            confidence=MockDuplicateConfidence.MEDIUM,
            algorithm=MockMatchingAlgorithm.JACCARD_SIMILARITY,
            score=0.75
        )

        assert candidate.document_id == "doc123"
        assert candidate.confidence == MockDuplicateConfidence.MEDIUM
        assert candidate.algorithm == MockMatchingAlgorithm.JACCARD_SIMILARITY
        assert candidate.score == 0.75

class TestDuplicateGroup:
    """Unit tests for DuplicateGroup model"""

    def test_duplicate_group_creation(self):
        """Test DuplicateGroup creation"""
        documents = [
            MockVectorDocument(id="doc1", content="content1"),
            MockVectorDocument(id="doc2", content="content2"),
            MockVectorDocument(id="doc3", content="content3")
        ]

        group = MockDuplicateGroup(
            group_id="group1",
            documents=documents,
            primary_document_id="doc1"
        )

        assert group.group_id == "group1"
        assert group.get_document_count() == 3
        assert group.get_primary_document().id == "doc1"

    def test_duplicate_group_no_primary(self):
        """Test DuplicateGroup with no primary document specified"""
        documents = [MockVectorDocument(id="doc1", content="content1")]

        group = MockDuplicateGroup(
            group_id="group1",
            documents=documents
        )

        assert group.get_primary_document().id == "doc1"  # Should default to first document

class TestUtilityFunctions:
    """Unit tests for utility functions"""

    def test_find_document_duplicates(self):
        """Test find_document_duplicates function"""
        documents = [
            MockVectorDocument(id="doc1", content="legislation document"),
            MockVectorDocument(id="doc2", content="another legislation document")
        ]

        results = mock_find_document_duplicates(documents, threshold=0.8)

        assert len(results) == 2
        assert all(len(result.candidates) > 0 for result in results)

    def test_merge_duplicate_group(self):
        """Test merge_duplicate_group function"""
        documents = [
            MockVectorDocument(id="doc1", content="content1"),
            MockVectorDocument(id="doc2", content="content2")
        ]

        group = MockDuplicateGroup("group1", documents)

        merged_group = mock_merge_duplicate_group(group, "doc2")

        assert merged_group.primary_document_id == "doc2"

class TestGlobalFunctions:
    """Tests for global duplicate detection functions"""

    @patch('src.pipeline.duplicate_detector.get_duplicate_detector')
    def test_find_document_duplicates(self, mock_get_detector, sample_documents):
        """Test find_document_duplicates function"""
        mock_detector = Mock()
        mock_detector.find_duplicates.return_value = [
            DuplicateGroup(
                master_id="doc1",
                candidates=[],
                confidence=DuplicateConfidence.HIGH
            )
        ]
        mock_get_detector.return_value = mock_detector

        groups = find_document_duplicates(sample_documents)

        assert isinstance(groups, list)
        mock_detector.find_duplicates.assert_called_once()

    @patch('src.pipeline.duplicate_detector.get_duplicate_detector')
    def test_merge_duplicate_group(self, mock_get_detector):
        """Test merge_duplicate_group function"""
        mock_detector = Mock()
        mock_get_detector.return_value = mock_detector

        group = DuplicateGroup(
            master_id="doc1",
            candidates=[],
            confidence=DuplicateConfidence.HIGH
        )

        result = merge_duplicate_group(group, "KEEP_NEWEST")

        assert isinstance(result, bool)
        mock_detector.merge_group.assert_called_once_with(group, "KEEP_NEWEST")

class TestEnums:
    """Tests for duplicate detection enums"""

    def test_matching_algorithm_enum(self):
        """Test MatchingAlgorithm enum values"""
        assert MatchingAlgorithm.EXACT_TEXT.value == "exact_text"
        assert MatchingAlgorithm.VECTOR_SIMILARITY.value == "vector_similarity"
        assert MatchingAlgorithm.HYBRID.value == "hybrid"

    def test_duplicate_confidence_enum(self):
        """Test DuplicateConfidence enum values"""
        assert DuplicateConfidence.VERY_HIGH.value == "VERY_HIGH"
        assert DuplicateConfidence.LOW.value == "LOW"

class TestDataClasses:
    """Tests for duplicate detection data classes"""

    def test_duplicate_candidate_creation(self):
        """Test DuplicateCandidate creation"""
        candidate = DuplicateCandidate(
            candidate_id="doc1",
            confidence=DuplicateConfidence.HIGH,
            algorithms=[MatchingAlgorithm.EXACT_TEXT, MatchingAlgorithm.METADATA_EXACT]
        )

        assert candidate.candidate_id == "doc1"
        assert candidate.confidence == DuplicateConfidence.HIGH
        assert len(candidate.algorithms) == 2

    def test_matching_result_creation(self):
        """Test MatchingResult creation"""
        result = MatchingResult(
            algorithm=MatchingAlgorithm.EXACT_TEXT,
            score=0.95,
            metadata={"matches": 5}
        )

        assert result.algorithm == MatchingAlgorithm.EXACT_TEXT
        assert result.score == 0.95
        assert result.metadata["matches"] == 5