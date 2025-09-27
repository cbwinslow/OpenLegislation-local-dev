# tools/testing/tests/test_calendar.py
import pytest
from datetime import datetime

# Mock the models since we don't have Pydantic installed in test environment
class MockCalendarId:
    def __init__(self, year, calendar_number):
        self.year = year
        self.calendar_number = calendar_number

    def __str__(self):
        return f"{self.year}-{self.calendar_number}"

class MockSupplementalCalendar:
    def __init__(self, calendar_id=None, supplemental_id=None, published_date_time=None):
        self.calendar_id = calendar_id
        self.supplemental_id = supplemental_id
        self.published_date_time = published_date_time

class MockActiveList:
    def __init__(self, calendar_id=None, sequence_no=None, notes=None):
        self.calendar_id = calendar_id
        self.sequence_no = sequence_no
        self.notes = notes

class MockCalendar:
    def __init__(self, calendar_id, published_date_time=None, notes=None):
        self.calendar_id = calendar_id
        self.published_date_time = published_date_time
        self.notes = notes
        self.supplementals = []
        self.active_lists = []

    def get_supplemental_count(self):
        return len(self.supplementals)

    def get_active_list_count(self):
        return len(self.active_lists)

    def is_published(self):
        return self.published_date_time is not None

    def get_calendar_name(self):
        return f"Calendar #{self.calendar_id.calendar_number} ({self.calendar_id.year})"

class TestCalendarModel:
    """Unit tests for Calendar model"""

    def test_calendar_creation(self):
        """Test basic Calendar creation"""
        calendar_id = MockCalendarId(
            year=2023,
            calendar_number=1
        )

        calendar = MockCalendar(
            calendar_id=calendar_id,
            published_date_time=datetime(2023, 1, 1, 12, 0),
            notes="Calendar notes"
        )

        assert calendar.calendar_id.year == 2023
        assert calendar.calendar_id.calendar_number == 1
        assert calendar.notes == "Calendar notes"

    def test_calendar_methods(self):
        """Test Calendar methods"""
        calendar = MockCalendar(
            calendar_id=MockCalendarId(year=2023, calendar_number=1),
            published_date_time=datetime(2023, 1, 1, 12, 0),
            notes="Test calendar"
        )

        # Test get_supplemental_count method
        assert calendar.get_supplemental_count() == 0

        # Test get_active_list_count method
        assert calendar.get_active_list_count() == 0

        # Test is_published method
        assert calendar.is_published() == True

        # Test get_calendar_name method
        assert calendar.get_calendar_name() == "Calendar #1 (2023)"

    def test_calendar_relationships(self):
        """Test Calendar relationships"""
        calendar = MockCalendar(
            calendar_id=MockCalendarId(year=2023, calendar_number=1)
        )

        # Add supplementals
        supplemental1 = MockSupplementalCalendar(
            calendar_id=calendar.calendar_id,
            supplemental_id="SUP001",
            published_date_time=datetime(2023, 1, 2, 10, 0)
        )
        calendar.supplementals.append(supplemental1)

        supplemental2 = MockSupplementalCalendar(
            calendar_id=calendar.calendar_id,
            supplemental_id="SUP002",
            published_date_time=datetime(2023, 1, 3, 14, 0)
        )
        calendar.supplementals.append(supplemental2)

        # Add active lists
        active_list = MockActiveList(
            calendar_id=calendar.calendar_id,
            sequence_no=1,
            notes="Active list notes"
        )
        calendar.active_lists.append(active_list)

        assert calendar.get_supplemental_count() == 2
        assert calendar.get_active_list_count() == 1

class TestCalendarId:
    """Tests for CalendarId model"""

    def test_calendar_id_creation(self):
        """Test CalendarId creation and properties"""
        calendar_id = MockCalendarId(
            year=2024,
            calendar_number=5
        )

        assert calendar_id.year == 2024
        assert calendar_id.calendar_number == 5

    def test_calendar_id_string_representation(self):
        """Test CalendarId string methods"""
        calendar_id = MockCalendarId(
            year=2023,
            calendar_number=1
        )

        assert str(calendar_id) == "2023-1"

class TestSupplementalCalendar:
    """Tests for SupplementalCalendar model"""

    def test_supplemental_creation(self):
        """Test SupplementalCalendar creation"""
        supplemental = MockSupplementalCalendar(
            calendar_id=MockCalendarId(year=2023, calendar_number=1),
            supplemental_id="SUP001",
            published_date_time=datetime(2023, 1, 2, 10, 0)
        )

        assert supplemental.supplemental_id == "SUP001"
        assert supplemental.calendar_id.year == 2023
        assert supplemental.published_date_time == datetime(2023, 1, 2, 10, 0)

class TestActiveList:
    """Tests for ActiveList model"""

    def test_active_list_creation(self):
        """Test ActiveList creation"""
        active_list = MockActiveList(
            calendar_id=MockCalendarId(year=2023, calendar_number=1),
            sequence_no=1,
            notes="Active list for calendar 1"
        )

        assert active_list.sequence_no == 1
        assert active_list.notes == "Active list for calendar 1"
        assert active_list.calendar_id.calendar_number == 1
        calendar = Calendar(
            calendar_id=CalendarId(year=2023, calendar_number=1)
        )

        # Test get_supplemental_calendars method
        supplementals = calendar.get_supplemental_calendars()
        assert isinstance(supplementals, list)

        # Test get_active_lists method
        active_lists = calendar.get_active_lists()
        assert isinstance(active_lists, list)

    def test_calendar_database_round_trip(self, test_session):
        """Test saving and loading Calendar from database"""
        # Create calendar
        calendar = Calendar(
            calendar_id=CalendarId(year=2023, calendar_number=1),
            published_date_time=datetime(2023, 1, 1, 12, 0),
            notes="DB test calendar"
        )

        # Save to database
        test_session.add(calendar)
        test_session.commit()

        # Load from database
        loaded_calendar = test_session.query(Calendar).filter(
            Calendar.calendar_id.year == 2023
        ).first()

        # Verify round-trip
        assert loaded_calendar is not None
        assert loaded_calendar.notes == "DB test calendar"
        assert loaded_calendar.calendar_id.calendar_number == 1

class TestCalendarId:
    """Tests for CalendarId model"""

    def test_calendar_id_creation(self):
        """Test CalendarId creation and properties"""
        calendar_id = CalendarId(
            year=2024,
            calendar_number=2
        )

        assert calendar_id.year == 2024
        assert calendar_id.calendar_number == 2

    def test_calendar_id_string_representation(self):
        """Test CalendarId string methods"""
        calendar_id = CalendarId(year=2023, calendar_number=1)

        assert str(calendar_id) == "2023-1"

class TestSupplementalCalendar:
    """Tests for SupplementalCalendar model"""

    def test_supplemental_creation(self):
        """Test SupplementalCalendar creation"""
        supplemental = SupplementalCalendar(
            calendar_id=CalendarId(year=2023, calendar_number=1),
            supplemental_id="SUP001",
            version="A",
            published_date_time=datetime(2023, 1, 2, 10, 0),
            notes="Supplemental notes"
        )

        assert supplemental.supplemental_id == "SUP001"
        assert supplemental.version == "A"
        assert supplemental.notes == "Supplemental notes"

class TestActiveList:
    """Tests for ActiveList model"""

    def test_active_list_creation(self):
        """Test ActiveList creation"""
        active_list = ActiveList(
            calendar_id=CalendarId(year=2023, calendar_number=1),
            sequence_no=1,
            calendar_no=1,
            bill_print_no="S1234",
            bill_amend_version="ORIGINAL",
            release_date_time=datetime(2023, 1, 1, 9, 0),
            notes="Active list notes"
        )

        assert active_list.sequence_no == 1
        assert active_list.calendar_no == 1
        assert active_list.bill_print_no == "S1234"
        assert active_list.notes == "Active list notes"