from pydantic import BaseModel
from typing import Dict, Set, Optional, TypeVar, Generic
from datetime import datetime
from collections import defaultdict

from .spotcheck_reference_id import SpotCheckReferenceId
from .spotcheck_mismatch import SpotCheckMismatch
from .spotcheck_mismatch_type import SpotCheckMismatchType
from .mismatch_state import MismatchState
from .spotcheck_mismatch_key import SpotCheckMismatchKey
from .spotcheck_prior_mismatch import SpotCheckPriorMismatch

ContentKey = TypeVar('ContentKey')

class SpotCheckObservation(BaseModel, Generic[ContentKey]):
    """A SpotCheckObservation is the result of performing a SpotCheck against some reference data. It contains
    any mismatches that were detected between the reference content and the observed content."""

    # The source used to compare our data against.
    reference_id: Optional[SpotCheckReferenceId] = None

    # A key that identifies the content being checked.
    key: ContentKey

    # The datetime this observation was made.
    observed_date_time: datetime = datetime.now()

    # The date time when the report that generated this observation was run
    report_date_time: Optional[datetime] = None

    # Mapping of mismatches that exist between the reference content and our content.
    mismatches: Dict[SpotCheckMismatchType, SpotCheckMismatch] = {}

    # Mapping of prior mismatches keyed by the mismatch type. This is only populated if the observation
    # is made within the content of previously saved reports and the mismatch is one that has appeared before.
    prior_mismatches: Dict[SpotCheckMismatchType, Set[SpotCheckPriorMismatch]] = {}

    def __init__(self, **data):
        super().__init__(**data)
        if self.mismatches is None:
            self.mismatches = {}
        if self.prior_mismatches is None:
            self.prior_mismatches = defaultdict(set)

    # --- Constructors ---

    @classmethod
    def get_ref_missing_obs(cls, reference_id: SpotCheckReferenceId, key: ContentKey) -> 'SpotCheckObservation[ContentKey]':
        """Generates an observation with a reference data missing observation"""
        from .spotcheck_mismatch_type import SpotCheckMismatchType
        obs = cls(reference_id=reference_id, key=key)
        obs.add_mismatch(SpotCheckMismatch.create_simple(
            SpotCheckMismatchType.REFERENCE_DATA_MISSING, key, ""))
        return obs

    @classmethod
    def get_observe_data_missing_obs(cls, reference_id: SpotCheckReferenceId, key: ContentKey) -> 'SpotCheckObservation[ContentKey]':
        """Generates an observation with an observed data missing observation"""
        from .spotcheck_mismatch_type import SpotCheckMismatchType
        obs = cls(reference_id=reference_id, key=key)
        obs.add_mismatch(SpotCheckMismatch.create_simple(
            SpotCheckMismatchType.OBSERVE_DATA_MISSING, "", key))
        return obs

    # --- Methods ---

    def has_mismatch(self, mismatch_type: SpotCheckMismatchType) -> bool:
        return mismatch_type in self.mismatches

    def add_mismatch(self, mismatch: SpotCheckMismatch) -> None:
        self.check_reportable(mismatch.mismatch_type)
        self.mismatches[mismatch.mismatch_type] = mismatch

    def get_mismatch_status_counts(self, ignored: bool) -> Dict[MismatchState, int]:
        """Returns the number of mismatches grouped by mismatch status."""
        if self.mismatches is None:
            raise ValueError("Collection of mismatches is null")

        counts = defaultdict(int)
        for mismatch in self.mismatches.values():
            if not mismatch.is_ignored ^ ignored:
                counts[mismatch.state] += 1
        return dict(counts)

    def get_mismatch_status_types(self, ignored: bool) -> Dict[SpotCheckMismatchType, Set[MismatchState]]:
        """Returns a mapping of mismatch type to status."""
        if self.mismatches is None:
            raise ValueError("Collection of mismatches is null")

        result = defaultdict(set)
        for mismatch in self.mismatches.values():
            if not mismatch.is_ignored ^ ignored:
                result[mismatch.mismatch_type].add(mismatch.state)
        return dict(result)

    def get_mismatch_types(self, ignored: bool) -> Set[SpotCheckMismatchType]:
        """Returns the set of mismatch types that there are mismatches for."""
        if self.mismatches is None:
            raise ValueError("Collection of mismatches is null")

        return {mismatch.mismatch_type for mismatch in self.mismatches.values()
                if not mismatch.is_ignored ^ ignored}

    def get_mismatch_keys(self) -> Set[SpotCheckMismatchKey[ContentKey]]:
        """Get a set of mismatch keys for this observation."""
        return {SpotCheckMismatchKey(self.key, mismatch.mismatch_type)
                for mismatch in self.mismatches.values()}

    def check_reportable(self, mismatch_type: SpotCheckMismatchType) -> None:
        """Check to make sure the given mismatch type can be reported by this observation"""
        if self.reference_id is None:
            return  # Allow for now if no reference_id set

        reference_type = self.reference_id.reference_type
        # The mismatch type must be registered as being checked by the observation's reference type.
        # Otherwise it cannot be resolved.
        if mismatch_type not in reference_type.checked_mismatch_types():
            raise ValueError(
                f"{mismatch_type} mismatches cannot be reported in {reference_type} observations.")

    def merge(self, other: 'SpotCheckObservation[ContentKey]') -> None:
        """Merge another observation of the same content in the same report into this observation."""
        if self.key != other.key:
            raise ValueError(f"Attempt to merge two observations with different keys: {self.key} and {other.key}")

        self.mismatches.update(other.mismatches)
        for mismatch_type, priors in other.prior_mismatches.items():
            self.prior_mismatches[mismatch_type].update(priors)

    # --- Basic Getters/Setters ---

    @property
    def get_report_date_time(self) -> Optional[datetime]:
        return self.report_date_time

    def set_report_date_time(self, report_date_time: datetime) -> None:
        self.report_date_time = report_date_time

    @property
    def get_reference_id(self) -> Optional[SpotCheckReferenceId]:
        return self.reference_id

    def set_reference_id(self, reference_id: SpotCheckReferenceId) -> None:
        self.reference_id = reference_id

    @property
    def get_key(self) -> ContentKey:
        return self.key

    def set_key(self, key: ContentKey) -> None:
        self.key = key

    @property
    def get_observed_date_time(self) -> datetime:
        return self.observed_date_time

    def set_observed_date_time(self, observed_date_time: datetime) -> None:
        self.observed_date_time = observed_date_time

    @property
    def get_mismatches(self) -> Dict[SpotCheckMismatchType, SpotCheckMismatch]:
        return self.mismatches

    @property
    def get_prior_mismatches(self) -> Dict[SpotCheckMismatchType, Set[SpotCheckPriorMismatch]]:
        return self.prior_mismatches