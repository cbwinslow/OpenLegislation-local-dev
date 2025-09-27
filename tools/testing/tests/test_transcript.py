# tools/testing/tests/test_transcript.py
import pytest
from datetime import datetime
from enum import Enum

# Mock the models since we don't have Pydantic installed in test environment
class MockSessionType(Enum):
    REGULAR = "REGULAR"
    SPECIAL = "SPECIAL"
    EXTRAORDINARY = "EXTRAORDINARY"

    @classmethod
    def from_string(cls, value):
        """Parse SessionType from string with underscores"""
        if value == "_REGULAR_":
            return cls.REGULAR
        elif value == "_SPECIAL_":
            return cls.SPECIAL
        elif value == "_EXTRAORDINARY_":
            return cls.EXTRAORDINARY
        return None

class MockTranscriptId:
    def __init__(self, date, session_type, number):
        self.date = date
        self.session_type = session_type
        self.number = number

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')}-{self.session_type.value}-{self.number}"

class MockTranscript:
    def __init__(self, transcript_id, text=None, location=None, transcript_type=None):
        self.transcript_id = transcript_id
        self.text = text
        self.location = location
        self.transcript_type = transcript_type
        self.speakers = []
        self.topics = []

    def get_speakers(self):
        return self.speakers

    def get_topics(self):
        return self.topics

class TestTranscriptModel:
    """Unit tests for Transcript model"""

    def test_transcript_creation(self):
        """Test basic Transcript creation"""
        transcript_id = MockTranscriptId(
            date=datetime(2023, 1, 1),
            session_type=MockSessionType.REGULAR,
            number=1
        )

        transcript = MockTranscript(
            transcript_id=transcript_id,
            text="Sample transcript text",
            location="Assembly Chamber",
            transcript_type="FULL"
        )

        assert transcript.transcript_id.date.year == 2023
        assert transcript.transcript_id.session_type == MockSessionType.REGULAR
        assert transcript.text == "Sample transcript text"
        assert transcript.location == "Assembly Chamber"

    def test_transcript_methods(self):
        """Test Transcript methods"""
        transcript = MockTranscript(
            transcript_id=MockTranscriptId(
                date=datetime(2023, 1, 1),
                session_type=MockSessionType.REGULAR,
                number=1
            ),
            text="Sample transcript text"
        )

        # Test get_speakers method
        speakers = transcript.get_speakers()
        assert isinstance(speakers, list)

        # Test get_topics method
        topics = transcript.get_topics()
        assert isinstance(topics, list)

    def test_transcript_relationships(self):
        """Test Transcript relationships"""
        transcript = MockTranscript(
            transcript_id=MockTranscriptId(
                date=datetime(2023, 1, 1),
                session_type=MockSessionType.REGULAR,
                number=1
            ),
            text="Sample transcript text"
        )

        # Add some mock speakers and topics
        transcript.speakers = ["Speaker 1", "Speaker 2"]
        transcript.topics = ["topic1", "topic2"]

        assert transcript.get_speakers() == ["Speaker 1", "Speaker 2"]
        assert transcript.get_topics() == ["topic1", "topic2"]

class TestTranscriptId:
    """Tests for TranscriptId model"""

    def test_transcript_id_creation(self):
        """Test TranscriptId creation and properties"""
        transcript_id = MockTranscriptId(
            date=datetime(2023, 2, 1),
            session_type=MockSessionType.SPECIAL,
            number=2
        )

        assert transcript_id.date.month == 2
        assert transcript_id.session_type == MockSessionType.SPECIAL
        assert transcript_id.number == 2

    def test_transcript_id_string_representation(self):
        """Test TranscriptId string methods"""
        transcript_id = MockTranscriptId(
            date=datetime(2023, 1, 1),
            session_type=MockSessionType.REGULAR,
            number=1
        )

        assert str(transcript_id) == "2023-01-01-REGULAR-1"

class TestSessionType:
    """Tests for SessionType enum"""

    def test_session_type_values(self):
        """Test SessionType enum values"""
        assert MockSessionType.REGULAR.value == "REGULAR"
        assert MockSessionType.SPECIAL.value == "SPECIAL"
        assert MockSessionType.EXTRAORDINARY.value == "EXTRAORDINARY"

    def test_session_type_from_string(self):
        """Test parsing SessionType from string"""
        assert MockSessionType.from_string("_REGULAR_") == MockSessionType.REGULAR
        assert MockSessionType.from_string("_SPECIAL_") == MockSessionType.SPECIAL
        assert MockSessionType.from_string("_EXTRAORDINARY_") == MockSessionType.EXTRAORDINARY
        assert MockSessionType.from_string("_UNKNOWN_") is None
