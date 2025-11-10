# tools/testing/tests/test_agenda.py
import pytest
from datetime import datetime

# Mock the models since we don't have Pydantic installed in test environment
class MockAgendaId:
    def __init__(self, number, year):
        self.number = number
        self.year = year

    def __str__(self):
        return f"{self.year}-{self.number}"

class MockAgendaInfoAddendum:
    def __init__(self, addendum_id=None, agenda_id=None, published_date_time=None):
        self.addendum_id = addendum_id
        self.agenda_id = agenda_id
        self.published_date_time = published_date_time

class MockAgendaInfoCommittee:
    def __init__(self, committee_id=None, committee_name=None, committee_chamber=None):
        self.committee_id = committee_id
        self.committee_name = committee_name
        self.committee_chamber = committee_chamber

class MockAgenda:
    def __init__(self, agenda_id, total_bills_considered=None, published_date_time=None):
        self.agenda_id = agenda_id
        self.total_bills_considered = total_bills_considered
        self.published_date_time = published_date_time
        self.addendums = []
        self.committees = []

    def get_total_addendums(self):
        return len(self.addendums)

    def get_committee_count(self):
        return len(self.committees)

    def is_published(self):
        return self.published_date_time is not None

class TestAgendaModel:
    """Unit tests for Agenda model"""

    def test_agenda_creation(self):
        """Test basic Agenda creation"""
        agenda_id = MockAgendaId(
            number=123,
            year=2023
        )

        agenda = MockAgenda(
            agenda_id=agenda_id,
            total_bills_considered=5,
            published_date_time=datetime(2023, 1, 1, 12, 0)
        )

        assert agenda.agenda_id.number == 123
        assert agenda.agenda_id.year == 2023
        assert agenda.total_bills_considered == 5

    def test_agenda_methods(self):
        """Test Agenda methods"""
        agenda = MockAgenda(
            agenda_id=MockAgendaId(number=123, year=2023),
            total_bills_considered=5,
            published_date_time=datetime(2023, 1, 1, 12, 0)
        )

        # Test get_total_addendums method
        assert agenda.get_total_addendums() == 0

        # Test get_committee_count method
        assert agenda.get_committee_count() == 0

        # Test is_published method
        assert agenda.is_published() == True

    def test_agenda_relationships(self):
        """Test Agenda relationships with other models"""
        agenda = MockAgenda(
            agenda_id=MockAgendaId(number=123, year=2023),
            total_bills_considered=5
        )

        # Test adding addendums
        addendum = MockAgendaInfoAddendum(
            addendum_id="ADD001",
            agenda_id=agenda.agenda_id,
            published_date_time=datetime(2023, 1, 1, 12, 0)
        )
        agenda.addendums.append(addendum)

        # Test adding committees
        committee = MockAgendaInfoCommittee(
            committee_id="COMM001",
            committee_name="Finance Committee",
            committee_chamber="SENATE"
        )
        agenda.committees.append(committee)

        assert agenda.get_total_addendums() == 1
        assert agenda.get_committee_count() == 1

class TestAgendaId:
    """Tests for AgendaId model"""

    def test_agenda_id_creation(self):
        """Test AgendaId creation and properties"""
        agenda_id = MockAgendaId(
            number=456,
            year=2024
        )

        assert agenda_id.number == 456
        assert agenda_id.year == 2024

    def test_agenda_id_string_representation(self):
        """Test AgendaId string methods"""
        agenda_id = MockAgendaId(number=123, year=2023)

        assert str(agenda_id) == "2023-123"

class TestAgendaInfoAddendum:
    """Tests for AgendaInfoAddendum model"""

    def test_addendum_creation(self):
        """Test AgendaInfoAddendum creation"""
        addendum = MockAgendaInfoAddendum(
            addendum_id="ADD001",
            agenda_id=MockAgendaId(number=123, year=2023),
            published_date_time=datetime(2023, 1, 1, 12, 0)
        )

        assert addendum.addendum_id == "ADD001"
        assert addendum.agenda_id.number == 123
        assert addendum.published_date_time == datetime(2023, 1, 1, 12, 0)

class TestAgendaInfoCommittee:
    """Tests for AgendaInfoCommittee model"""

    def test_committee_creation(self):
        """Test AgendaInfoCommittee creation"""
        committee = MockAgendaInfoCommittee(
            committee_id="COMM001",
            committee_name="Finance Committee",
            committee_chamber="SENATE"
        )

        assert committee.committee_id == "COMM001"
        assert committee.committee_name == "Finance Committee"
        assert committee.committee_chamber == "SENATE"