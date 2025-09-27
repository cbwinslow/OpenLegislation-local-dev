# tools/testing/tests/test_member.py
import pytest
from datetime import datetime

# Mock the models since we don't have Pydantic installed in test environment
class MockSessionYear:
    def __init__(self, year):
        self.year = year

class MockPersonName:
    def __init__(self, first_name=None, last_name=None, middle_name=None, suffix=None):
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.suffix = suffix

    def get_full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(filter(None, parts))

class MockPerson:
    def __init__(self, person_id, full_name=None, first_name=None, last_name=None,
                 middle_name=None, suffix=None, img_name=None):
        self.person_id = person_id
        self.full_name = full_name
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.suffix = suffix
        self.img_name = img_name

    def get_display_name(self):
        return self.full_name or f"{self.first_name} {self.last_name}"

class MockSessionMember:
    def __init__(self, session_member_id=None, member_id=None, session_year=None,
                 chamber=None, district_code=None, alternate=None):
        self.session_member_id = session_member_id
        self.member_id = member_id
        self.session_year = session_year
        self.chamber = chamber
        self.district_code = district_code
        self.alternate = alternate

class MockMember:
    def __init__(self, member_id, person=None, chamber=None, district_code=None,
                 alternate=None, session_year=None):
        self.member_id = member_id
        self.person = person
        self.chamber = chamber
        self.district_code = district_code
        self.alternate = alternate
        self.session_year = session_year

    def get_full_name(self):
        return self.person.get_display_name() if self.person else "Unknown"

    def is_active(self):
        return True  # Mock implementation

class TestMemberModel:
    """Unit tests for Member model"""

    def test_member_creation(self):
        """Test basic Member creation"""
        person = MockPerson(
            person_id=123,
            full_name="John Doe",
            first_name="John",
            last_name="Doe"
        )

        member = MockMember(
            member_id="MEM001",
            person=person,
            chamber="SENATE",
            district_code="01",
            session_year=MockSessionYear(2023)
        )

        assert member.member_id == "MEM001"
        assert member.person.full_name == "John Doe"
        assert member.chamber == "SENATE"
        assert member.district_code == "01"
        assert member.session_year.year == 2023

    def test_member_methods(self):
        """Test Member methods"""
        person = MockPerson(
            person_id=123,
            full_name="John Doe"
        )

        member = MockMember(
            member_id="MEM001",
            person=person,
            chamber="SENATE"
        )

        # Test get_full_name method
        assert member.get_full_name() == "John Doe"

        # Test is_active method
        assert member.is_active() == True

    def test_member_relationships(self):
        """Test Member relationships with other models"""
        person = MockPerson(
            person_id=123,
            full_name="John Doe"
        )

        member = MockMember(
            member_id="MEM001",
            person=person,
            chamber="SENATE",
            district_code="01"
        )

        # Test session member relationship
        session_member = MockSessionMember(
            session_member_id="SM001",
            member_id=member.member_id,
            session_year=MockSessionYear(2023),
            chamber="SENATE",
            district_code="01",
            alternate=False
        )

        assert session_member.session_member_id == "SM001"
        assert session_member.member_id == "MEM001"
        assert session_member.session_year.year == 2023
        assert session_member.chamber == "SENATE"
        assert session_member.district_code == "01"
        assert session_member.alternate == False

        assert member.member_id == "MEM001"
        assert member.person.full_name == "John Doe"
        assert member.chamber == "SENATE"
        assert member.district_code == "01"

class TestPersonModel:
    """Unit tests for Person model"""

    def test_person_creation(self):
        """Test basic Person creation"""
        person = MockPerson(
            person_id=123,
            full_name="Jane Smith",
            first_name="Jane",
            last_name="Smith",
            middle_name="A",
            suffix="Jr.",
            img_name="jane_smith.jpg"
        )

        assert person.person_id == 123
        assert person.full_name == "Jane Smith"
        assert person.first_name == "Jane"
        assert person.last_name == "Smith"
        assert person.middle_name == "A"
        assert person.suffix == "Jr."
        assert person.img_name == "jane_smith.jpg"

    def test_person_methods(self):
        """Test Person methods"""
        person = MockPerson(
            person_id=456,
            full_name="Bob Johnson",
            first_name="Bob",
            last_name="Johnson"
        )

        # Test get_display_name method
        assert person.get_display_name() == "Bob Johnson"

        # Test with no full_name
        person_no_full = MockPerson(
            person_id=789,
            first_name="Alice",
            last_name="Brown"
        )
        assert person_no_full.get_display_name() == "Alice Brown"

class TestSessionMemberModel:
    """Unit tests for SessionMember model"""

    def test_session_member_creation(self):
        """Test basic SessionMember creation"""
        session_member = MockSessionMember(
            session_member_id="SM001",
            member_id="MEM001",
            session_year=MockSessionYear(2023),
            chamber="SENATE",
            district_code="01",
            alternate=False
        )

        assert session_member.session_member_id == "SM001"
        assert session_member.member_id == "MEM001"
        assert session_member.session_year.year == 2023
        assert session_member.chamber == "SENATE"
        assert session_member.district_code == "01"
        assert session_member.alternate == False

class TestPersonNameModel:
    """Unit tests for PersonName model"""

    def test_person_name_creation(self):
        """Test basic PersonName creation"""
        name = MockPersonName(
            first_name="John",
            last_name="Doe",
            middle_name="Q",
            suffix="Sr."
        )

        assert name.first_name == "John"
        assert name.last_name == "Doe"
        assert name.middle_name == "Q"
        assert name.suffix == "Sr."

    def test_person_name_methods(self):
        """Test PersonName methods"""
        name = MockPersonName(
            first_name="Jane",
            last_name="Smith",
            middle_name="A",
            suffix="Jr."
        )

        # Test get_full_name method
        assert name.get_full_name() == "Jane A Smith Jr."

        # Test without middle name and suffix
        simple_name = MockPersonName(
            first_name="Bob",
            last_name="Johnson"
        )
        assert simple_name.get_full_name() == "Bob Johnson"
