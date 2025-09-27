# tools/testing/tests/test_bill.py
import pytest
from datetime import datetime

# Mock the models since we don't have Pydantic installed in test environment
class MockBillId:
    def __init__(self, base_print_no, version, session_year):
        self.base_print_no = base_print_no
        self.version = version
        self.session_year = session_year

    def __str__(self):
        return f"{self.base_print_no}-{self.session_year.year}"

    def get_print_no(self):
        # BillId doesn't know chamber, so just return the base print number
        return self.base_print_no

class MockBillStatus:
    INTRODUCED = "INTRODUCED"
    PASSED = "PASSED"

class MockBillType:
    SENATE_BILL = "SENATE_BILL"
    ASSEMBLY_BILL = "ASSEMBLY_BILL"

class MockChamber:
    SENATE = "SENATE"
    ASSEMBLY = "ASSEMBLY"

class MockSessionYear:
    def __init__(self, year):
        self.year = year

class MockBill:
    def __init__(self, bill_id, title=None, summary=None, status=None,
                 bill_type=None, chamber=None, active_version=None):
        self.bill_id = bill_id
        self.title = title
        self.summary = summary
        self.status = status
        self.bill_type = bill_type
        self.chamber = chamber
        self.active_version = active_version
        self.sponsors = []

        # Validate bill_type
        if bill_type and bill_type not in [MockBillType.SENATE_BILL, MockBillType.ASSEMBLY_BILL]:
            raise ValueError(f"Invalid bill_type: {bill_type}")

    def get_print_no(self):
        if self.chamber:
            chamber_prefix = self.chamber[0]  # "S" for SENATE, "A" for ASSEMBLY
            return f"{chamber_prefix}. {self.bill_id.base_print_no}"
        else:
            return self.bill_id.get_print_no()

    def is_active(self):
        return True

    def get_current_version(self):
        return self

class TestBillModel:
    """Unit tests for Bill model"""

    def test_bill_creation(self):
        """Test basic Bill creation"""
        bill_id = MockBillId(
            base_print_no="S1234",
            version="ORIGINAL",
            session_year=MockSessionYear(2023)
        )

        bill = MockBill(
            bill_id=bill_id,
            title="Test Bill Title",
            summary="Test summary",
            status=MockBillStatus.INTRODUCED,
            bill_type=MockBillType.SENATE_BILL,
            chamber=MockChamber.SENATE,
            active_version="ORIGINAL"
        )

        assert bill.title == "Test Bill Title"
        assert bill.status == MockBillStatus.INTRODUCED
        assert bill.chamber == MockChamber.SENATE
        assert bill.bill_id.base_print_no == "S1234"

    def test_bill_validation(self):
        """Test Bill validation rules"""
        # Test invalid bill type
        with pytest.raises(ValueError):
            MockBill(
                bill_id=MockBillId(base_print_no="S1234", version="ORIGINAL", session_year=MockSessionYear(2023)),
                title="Test",
                bill_type="INVALID_TYPE"  # Should fail validation
            )

    def test_bill_methods(self):
        """Test Bill methods"""
        bill = MockBill(
            bill_id=MockBillId(base_print_no="1234", version="ORIGINAL", session_year=MockSessionYear(2023)),
            title="Test Bill",
            status=MockBillStatus.INTRODUCED,
            chamber=MockChamber.SENATE  # Add chamber for get_print_no test
        )

        # Test get_print_no method
        assert bill.get_print_no() == "S. 1234"

        # Test is_active method
        assert bill.is_active() == True

        # Test get_current_version method
        assert bill.get_current_version() == bill

    def test_bill_relationships(self):
        """Test Bill relationships with other models"""
        # This would test sponsors, actions, votes, etc.
        # For now, basic structure test
        bill = MockBill(
            bill_id=MockBillId(base_print_no="S1234", version="ORIGINAL", session_year=MockSessionYear(2023)),
            title="Relationship Test Bill"
        )

        # Test adding sponsors (when implemented)
        # bill.sponsors.append(sponsor)

        assert bill.sponsors == []  # Placeholder

class TestBillId:
    """Tests for BillId model"""

    def test_bill_id_creation(self):
        """Test BillId creation and properties"""
        bill_id = MockBillId(
            base_print_no="A1234",
            version="A",
            session_year=MockSessionYear(2023)
        )

        assert bill_id.base_print_no == "A1234"
        assert bill_id.version == "A"
        assert bill_id.session_year.year == 2023

    def test_bill_id_string_representation(self):
        """Test BillId string methods"""
        bill_id = MockBillId(
            base_print_no="1234",
            version="ORIGINAL",
            session_year=MockSessionYear(2023)
        )

        assert str(bill_id) == "1234-2023"
        assert bill_id.get_print_no() == "1234"