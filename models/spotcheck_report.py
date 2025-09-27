from pydantic import BaseModel
from typing import Dict, TypeVar, Optional, Set, Collection, List
from datetime import datetime
from collections import defaultdict
import collections

from .spotcheck_report_id import SpotCheckReportId
from .spotcheck_observation import SpotCheckObservation
from .spotcheck_report_summary import SpotCheckReportSummary
from .mismatch_state import MismatchState
from .spotcheck_mismatch_type import SpotCheckMismatchType

ContentKey = TypeVar('ContentKey')

class SpotCheckReport(BaseModel):
    """A SpotCheckReport is basically a collection of observations that have 1 or more mismatches associated
    within them. The ContentKey is templated to allow for reports on specific content types."""

    # Auto increment id
    id: int = 0

    # Identifier for this report.
    report_id: Optional[SpotCheckReportId] = None

    # Map of all observations associated with this report.
    observation_map: Dict[ContentKey, SpotCheckObservation[ContentKey]] = {}

    # miscellaneous notes pertaining to this report
    notes: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.observation_map is None:
            self.observation_map = {}

    # --- Constructors ---

    @classmethod
    def create_empty(cls) -> 'SpotCheckReport':
        return cls()

    @classmethod
    def create_with_report_id(cls, report_id: SpotCheckReportId) -> 'SpotCheckReport':
        return cls(report_id=report_id)

    @classmethod
    def create_with_report_id_and_notes(cls, report_id: SpotCheckReportId, notes: str) -> 'SpotCheckReport':
        return cls(report_id=report_id, notes=notes)

    # --- Methods ---

    def get_summary(self) -> SpotCheckReportSummary:
        summary = SpotCheckReportSummary(report_id=self.report_id, notes=self.notes)
        summary.add_counts_from_observations(self.observation_map.values())
        return summary

    def get_open_mismatch_count(self, ignored: bool) -> int:
        """Get a count of open mismatches
        @param ignored boolean - returns the count of ignored mismatches if true, which are not included if false
        @return long
        """
        return sum(
            sum(1 for mismatch in obs.mismatches.values()
                if (not mismatch.is_ignored() ^ ignored) and mismatch.state == MismatchState.OPEN)
            for obs in self.observation_map.values()
        )

    def get_mismatch_status_counts(self, ignored: bool) -> Dict[MismatchState, int]:
        """Get the number of mismatches across all observations grouped by the mismatch status.
        @param ignored boolean - get the status count of ignored mismatches if true, which are not included if false
        @return Map<SpotCheckMismatchStatus, Long>
        """
        if self.observation_map is None:
            raise ValueError("The observations on this report have not yet been set.")

        counts = defaultdict(int)
        for status in MismatchState:
            counts[status] = 0

        for obs in self.observation_map.values():
            for status, count in obs.get_mismatch_status_counts(ignored).items():
                counts[status] += count

        return dict(counts)

    def get_mismatch_type_status_counts(self, ignored: bool) -> Dict[SpotCheckMismatchType, Dict[MismatchState, int]]:
        """Gets a count of mismatch types grouped by statuses across all observations.
        @param ignored boolean - get type/status counts of ignored mismatches if true, which are not included if false
        @return Map<SpotCheckMismatchType, Map<SpotCheckMismatchStatus, Long>>
        """
        if self.observation_map is None:
            raise ValueError("The observations on this report have not yet been set.")

        counts = defaultdict(lambda: defaultdict(int))

        for obs in self.observation_map.values():
            for mismatch_type, status_counts in obs.get_mismatch_status_types(ignored).items():
                for status, count in status_counts.items():
                    counts[mismatch_type][status] += count

        return {k: dict(v) for k, v in counts.items()}

    def get_mismatch_status_type_counts(self, ignored: bool) -> Dict[MismatchState, Dict[SpotCheckMismatchType, int]]:
        """Gets a count of mismatch statuses grouped by type across all observations.
        @param ignored boolean - get status/type counts of ignored mismatches if true, which are not included if false
        @return Map<SpotCheckMismatchStatus, Map<SpotCheckMismatchType, Long>>
        """
        if self.observation_map is None:
            raise ValueError("The observations on this report have not yet been set.")

        # Using a nested defaultdict for the table structure
        count_table = defaultdict(lambda: defaultdict(int))

        for obs in self.observation_map.values():
            for mismatch_type, status_types in obs.get_mismatch_status_types(ignored).items():
                for status in status_types:
                    current_value = count_table[status][mismatch_type]
                    count_table[status][mismatch_type] = current_value + 1

        return {k: dict(v) for k, v in count_table.items()}

    def get_mismatch_type_counts(self, ignored: bool) -> Dict[SpotCheckMismatchType, int]:
        """Get the number of mismatches across all observations grouped by the mismatch type.
        @param ignored boolean - get type counts of ignored mismatches if true, which are not included if false
        @return Map<SpotCheckMismatchType, Long>
        """
        if self.observation_map is None:
            raise ValueError("The observations on this report have not yet been set.")

        counts = defaultdict(int)

        for obs in self.observation_map.values():
            for mismatch_type in obs.get_mismatch_types(ignored):
                counts[mismatch_type] += 1

        return dict(counts)

    def add_observation(self, observation: SpotCheckObservation[ContentKey]) -> None:
        """Add the observation to the map."""
        if observation is None:
            raise ValueError("Supplied observation cannot be null")

        observation.reference_id = self.report_id.get_reference_id() if self.report_id else None
        observation.observed_date_time = datetime.now()

        # If there is already an observation for this key, attempt to merge the new one in.
        if observation.key in self.observation_map:
            prior_obs = self.observation_map[observation.key]
            prior_obs.merge(observation)
        else:
            self.observation_map[observation.key] = observation

    def add_observations(self, observations: Collection[SpotCheckObservation[ContentKey]]) -> None:
        """Add the collection of observations to the map."""
        if observations is None:
            raise ValueError("Supplied observation collection cannot be null")

        for obs in observations:
            self.add_observation(obs)

    def get_observed_count(self) -> int:
        """Get the number of content items observed"""
        return len(self.observation_map) if self.observation_map else 0

    def get_checked_keys(self) -> Set[ContentKey]:
        """Get ContentKey's that were checked by this report."""
        return {obs.key for obs in self.observation_map.values()}

    def add_ref_missing_obs(self, missing_key: ContentKey) -> None:
        """Add an observation to the report indicating that content is missing from the reference data
        @param missingKey ContentKey - id of the missing data
        """
        self.add_observation(SpotCheckObservation.get_ref_missing_obs(
            self.report_id.get_reference_id() if self.report_id else None, missing_key))

    def add_observed_data_missing_obs(self, missing_key: ContentKey) -> None:
        """Add an observation to the report indicating that content is missing from Openleg data
        @param missingKey ContentKey - id of the missing data
        """
        self.add_observation(SpotCheckObservation.get_observe_data_missing_obs(
            self.report_id.get_reference_id() if self.report_id else None, missing_key))

    def add_empty_observation(self, content_key: ContentKey) -> None:
        """Add an empty observation to the report, indicating that there are no errors.
        @param contentKey ContentKey
        """
        self.add_observation(SpotCheckObservation(
            reference_id=self.report_id.get_reference_id() if self.report_id else None,
            key=content_key))

    def get_observations(self) -> Collection[SpotCheckObservation[ContentKey]]:
        """Get all observations in this report."""
        return list(self.observation_map.values()) if self.observation_map else []

    def get_mismatch_keys(self) -> Set['SpotCheckMismatchKey[ContentKey]']:
        """Get all mismatch keys from all observations."""
        from .spotcheck_mismatch_key import SpotCheckMismatchKey

        mismatch_keys = set()
        for obs in self.observation_map.values():
            mismatch_keys.update(obs.get_mismatch_keys())
        return mismatch_keys

    # --- Delegates ---

    def get_report_date_time(self) -> Optional[datetime]:
        return self.report_id.report_date_time if self.report_id else None

    def get_reference_date_time(self) -> Optional[datetime]:
        return self.report_id.reference_date_time if self.report_id else None

    def get_reference_type(self):
        return self.report_id.reference_type if self.report_id else None

    # --- Basic Getters/Setters ---

    def get_id(self) -> int:
        return self.id

    def set_id(self, id: int) -> None:
        self.id = id

    def get_report_id(self) -> Optional[SpotCheckReportId]:
        return self.report_id

    def set_report_id(self, report_id: SpotCheckReportId) -> None:
        self.report_id = report_id

    def get_observation_map(self) -> Dict[ContentKey, SpotCheckObservation[ContentKey]]:
        return self.observation_map

    def set_observation_map(self, observation_map: Dict[ContentKey, SpotCheckObservation[ContentKey]]) -> None:
        self.observation_map = observation_map

    def get_notes(self) -> Optional[str]:
        return self.notes

    def set_notes(self, notes: str) -> None:
        self.notes = notes