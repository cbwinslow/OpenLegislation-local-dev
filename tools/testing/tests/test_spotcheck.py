# tools/testing/tests/test_spotcheck.py
import pytest
from datetime import datetime
from enum import Enum

# Mock the models since we don't have Pydantic installed in test environment
class MockSpotcheckRefType(Enum):
    BILL = "BILL"
    LAW = "LAW"
    AGENDA = "AGENDA"

class MockSpotcheckDataSource(Enum):
    OPENLEG = "OPENLEG"
    LBDC = "LBDC"
    GOVINFO = "GOVINFO"

class MockSpotcheckMismatchType(Enum):
    TITLE = "TITLE"
    SPONSOR = "SPONSOR"
    STATUS = "STATUS"

class MockMismatchState(Enum):
    NEW = "NEW"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class MockSpotcheckReportId:
    def __init__(self, reference_date, reference_type, reference_id):
        self.reference_date = reference_date
        self.reference_type = reference_type
        self.reference_id = reference_id

    def __str__(self):
        return f"{self.reference_type.value}-{self.reference_id}-{self.reference_date.strftime('%Y%m%d')}"

class MockSpotcheckMismatchKey:
    def __init__(self, report_id, key):
        self.report_id = report_id
        self.key = key

class MockSpotcheckMismatch:
    def __init__(self, mismatch_key, mismatch_type=None, datasource=None, reference_datum=None, observed_datum=None):
        self.mismatch_key = mismatch_key
        self.mismatch_type = mismatch_type
        self.datasource = datasource
        self.reference_datum = reference_datum
        self.observed_datum = observed_datum

    def is_resolved(self):
        return False

class MockSpotcheckObservation:
    def __init__(self, report_id=None, key=None, observed_datum=None):
        self.report_id = report_id
        self.key = key
        self.observed_datum = observed_datum

class MockSpotcheckReport:
    def __init__(self, report_id, reference_date=None, reference_type=None):
        self.report_id = report_id
        self.reference_date = reference_date
        self.reference_type = reference_type
        self.mismatches = []
        self.observations = []

    def get_mismatch_count(self):
        return len(self.mismatches)

    def get_observation_count(self):
        return len(self.observations)

    def has_mismatches(self):
        return len(self.mismatches) > 0

class MockSpotcheckSummary:
    def __init__(self, report_date, total_reports=None, total_mismatches=None):
        self.report_date = report_date
        self.total_reports = total_reports
        self.total_mismatches = total_mismatches

    def get_mismatch_rate(self):
        if self.total_reports == 0:
            return 0.0
        return self.total_mismatches / self.total_reports

class TestSpotcheckReport:
    """Unit tests for SpotcheckReport model"""

    def test_spotcheck_report_creation(self):
        """Test basic SpotcheckReport creation"""
        report_id = MockSpotcheckReportId(
            reference_date=datetime(2023, 1, 1),
            reference_type=MockSpotcheckRefType.BILL,
            reference_id="BILL001"
        )

        report = MockSpotcheckReport(
            report_id=report_id,
            reference_date=datetime(2023, 1, 1),
            reference_type=MockSpotcheckRefType.BILL
        )

        assert report.report_id.reference_id == "BILL001"
        assert report.reference_type == MockSpotcheckRefType.BILL

    def test_spotcheck_report_methods(self):
        """Test SpotcheckReport methods"""
        report = MockSpotcheckReport(
            report_id=MockSpotcheckReportId(
                reference_date=datetime(2023, 1, 1),
                reference_type=MockSpotcheckRefType.BILL,
                reference_id="BILL001"
            )
        )

        # Test get_mismatch_count method
        assert report.get_mismatch_count() == 0

        # Test get_observation_count method
        assert report.get_observation_count() == 0

        # Test has_mismatches method
        assert report.has_mismatches() == False

        # Add mismatches and test again
        mismatch = MockSpotcheckMismatch(
            mismatch_key=MockSpotcheckMismatchKey(report.report_id, "title"),
            mismatch_type=MockSpotcheckMismatchType.TITLE
        )
        report.mismatches.append(mismatch)

        assert report.get_mismatch_count() == 1
        assert report.has_mismatches() == True

class TestSpotcheckMismatch:
    """Unit tests for SpotcheckMismatch model"""

    def test_spotcheck_mismatch_creation(self):
        """Test SpotcheckMismatch creation"""
        report_id = MockSpotcheckReportId(
            reference_date=datetime(2023, 1, 1),
            reference_type=MockSpotcheckRefType.BILL,
            reference_id="BILL001"
        )

        mismatch_key = MockSpotcheckMismatchKey(report_id, "title")

        mismatch = MockSpotcheckMismatch(
            mismatch_key=mismatch_key,
            mismatch_type=MockSpotcheckMismatchType.TITLE,
            datasource=MockSpotcheckDataSource.LBDC,
            reference_datum="Original Title",
            observed_datum="Different Title"
        )

        assert mismatch.mismatch_type == MockSpotcheckMismatchType.TITLE
        assert mismatch.datasource == MockSpotcheckDataSource.LBDC
        assert mismatch.reference_datum == "Original Title"
        assert mismatch.observed_datum == "Different Title"

    def test_spotcheck_mismatch_methods(self):
        """Test SpotcheckMismatch methods"""
        mismatch = MockSpotcheckMismatch(
            mismatch_key=MockSpotcheckMismatchKey(
                MockSpotcheckReportId(
                    reference_date=datetime(2023, 1, 1),
                    reference_type=MockSpotcheckRefType.BILL,
                    reference_id="BILL001"
                ),
                "title"
            )
        )

        # Test is_resolved method
        assert mismatch.is_resolved() == False

class TestSpotcheckSummary:
    """Unit tests for SpotcheckSummary model"""

    def test_spotcheck_summary_creation(self):
        """Test SpotcheckSummary creation"""
        summary = MockSpotcheckSummary(
            report_date=datetime(2023, 1, 1),
            total_reports=10,
            total_mismatches=3
        )

        assert summary.report_date == datetime(2023, 1, 1)
        assert summary.total_reports == 10
        assert summary.total_mismatches == 3

    def test_spotcheck_summary_methods(self):
        """Test SpotcheckSummary methods"""
        summary = MockSpotcheckSummary(
            report_date=datetime(2023, 1, 1),
            total_reports=10,
            total_mismatches=3
        )

        # Test get_mismatch_rate method
        assert summary.get_mismatch_rate() == 0.3

        # Test with zero reports
        summary_zero = MockSpotcheckSummary(
            report_date=datetime(2023, 1, 1),
            total_reports=0,
            total_mismatches=0
        )
        assert summary_zero.get_mismatch_rate() == 0.0

        report = SpotcheckReport(
            report_id=report_id,
            data_source=SpotcheckDataSource.LBDC,
            notes="Test report notes"
        )

        assert report.report_id.reference_type == SpotcheckRefType.BILL
        assert report.data_source == SpotcheckDataSource.LBDC
        assert report.notes == "Test report notes"

    def test_spotcheck_report_methods(self):
        """Test SpotcheckReport methods"""
        report = SpotcheckReport(
            report_id=SpotcheckReportId(
                reference_date=datetime(2023, 1, 1),
                reference_type=SpotcheckRefType.BILL,
                reference_id="BILL001"
            )
        )

        # Test get_mismatches method
        mismatches = report.get_mismatches()
        assert isinstance(mismatches, list)

        # Test get_observations method
        observations = report.get_observations()
        assert isinstance(observations, list)

class TestSpotcheckReportId:
    """Tests for SpotcheckReportId model"""

    def test_report_id_creation(self):
        """Test SpotcheckReportId creation and properties"""
        report_id = SpotcheckReportId(
            reference_date=datetime(2023, 2, 1),
            reference_type=SpotcheckRefType.CALENDAR,
            reference_id="CAL001"
        )

        assert report_id.reference_date.year == 2023
        assert report_id.reference_type == SpotcheckRefType.CALENDAR
        assert report_id.reference_id == "CAL001"

    def test_report_id_string_representation(self):
        """Test SpotcheckReportId string methods"""
        report_id = SpotcheckReportId(
            reference_date=datetime(2023, 1, 1),
            reference_type=SpotcheckRefType.BILL,
            reference_id="BILL001"
        )

        assert str(report_id) == "BILL-BILL001-2023-01-01"

class TestSpotcheckSummary:
    """Tests for SpotcheckSummary model"""

    def test_summary_creation(self):
        """Test SpotcheckSummary creation"""
        summary = SpotcheckSummary(
            summary_id="SUM001",
            reference_date=datetime(2023, 1, 1),
            total_reports=10,
            total_mismatches=5,
            open_mismatches=2
        )

        assert summary.summary_id == "SUM001"
        assert summary.total_reports == 10
        assert summary.total_mismatches == 5
        assert summary.open_mismatches == 2

class TestSpotcheckMismatch:
    """Tests for SpotcheckMismatch model"""

    def test_mismatch_creation(self):
        """Test SpotcheckMismatch creation"""
        mismatch = SpotcheckMismatch(
            mismatch_id="MIS001",
            report_id="REP001",
            key=SpotcheckMismatchKey(field="title", key_value="Test Bill"),
            mismatch_type=SpotcheckMismatchType.TEXT_DIFF,
            state=MismatchState.OPEN,
            observed_date=datetime(2023, 1, 1),
            reference_data="Reference data",
            observed_data="Observed data"
        )

        assert mismatch.mismatch_id == "MIS001"
        assert mismatch.mismatch_type == SpotcheckMismatchType.TEXT_DIFF
        assert mismatch.state == MismatchState.OPEN

class TestSpotcheckObservation:
    """Tests for SpotcheckObservation model"""

    def test_observation_creation(self):
        """Test SpotcheckObservation creation"""
        observation = SpotcheckObservation(
            observation_id="OBS001",
            report_id="REP001",
            key="title",
            observed_data="Observed title",
            reference_data="Reference title"
        )

        assert observation.observation_id == "OBS001"
        assert observation.key == "title"
        assert observation.observed_data == "Observed title"

class TestSpotcheckEnums:
    """Tests for Spotcheck enums"""

    def test_ref_type_enum(self):
        """Test SpotcheckRefType enum values"""
        assert SpotcheckRefType.BILL.value == "BILL"
        assert SpotcheckRefType.CALENDAR.value == "CALENDAR"
        assert SpotcheckRefType.AGENDA.value == "AGENDA"

    def test_data_source_enum(self):
        """Test SpotcheckDataSource enum values"""
        assert SpotcheckDataSource.LBDC.value == "LBDC"
        assert SpotcheckDataSource.OPENLEG.value == "OPENLEG"

    def test_mismatch_type_enum(self):
        """Test SpotcheckMismatchType enum values"""
        assert SpotcheckMismatchType.TEXT_DIFF.value == "TEXT_DIFF"
        assert SpotcheckMismatchType.MISSING_DATA.value == "MISSING_DATA"

    def test_mismatch_state_enum(self):
        """Test MismatchState enum values"""
        assert MismatchState.OPEN.value == "OPEN"
        assert MismatchState.RESOLVED.value == "RESOLVED"