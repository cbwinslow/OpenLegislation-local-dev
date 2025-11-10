#!/usr/bin/env python3
"""
OpenLegislation Ingestion Engine

High-performance ingestion engine with support for:
- GPU acceleration for data processing
- Parallel and async processing
- Multi-threading and multiprocessing
- Real-time performance monitoring
- Scalable architecture for large datasets

Author: OpenLegislation Team
Date: 2025-11-08
"""

import asyncio
import concurrent.futures
import json
import logging
import multiprocessing
import os
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Iterable, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import aiohttp
import psutil
import requests
from tqdm.asyncio import tqdm

# GPU Support (optional)
try:
    import torch
    import torch.cuda
    import cudf  # RAPIDS cuDF for GPU DataFrames
    import cupy as cp  # CuPy for GPU arrays
    GPU_AVAILABLE = torch.cuda.is_available()
    GPU_COUNT = torch.cuda.device_count() if GPU_AVAILABLE else 0
    RAPIDS_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    GPU_COUNT = 0
    cudf = None
    cp = None
    RAPIDS_AVAILABLE = False
    torch = None

try:
    from sqlalchemy import select
    from sqlalchemy.exc import SQLAlchemyError, IntegrityError
    from sqlalchemy.orm import sessionmaker
except ImportError:  # pragma: no cover - optional dependency
    select = None
    SQLAlchemyError = Exception
    IntegrityError = Exception
    sessionmaker = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion operation"""
    records_processed: int = 0
    duration: float = 0.0
    success: bool = True
    errors: List[str] = None
    performance_metrics: Dict[str, Any] = None
    data_quality_metrics: Dict[str, Any] = None

    def __post_init__(self):
        """
        Ensure mutable fields are initialized to empty containers when omitted.
        
        If `errors`, `performance_metrics`, or `data_quality_metrics` are `None` after datantiation,
        they are replaced with an empty list or empty dicts respectively to provide safe mutable defaults.
        """
        if self.errors is None:
            self.errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.data_quality_metrics is None:
            self.data_quality_metrics = {}


@dataclass
class FetchResponse:
    """Container for API fetch responses."""

    records: List[Dict[str, Any]]
    api_calls: int
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpsertSummary:
    """Summary of database upsert operations."""

    inserted: int = 0
    duplicates: int = 0
    errors: int = 0


class BaseDatabaseAdapter:
    """Interface for ingestion database interactions."""

    def prefetch_bill_keys(self, start: Optional[int], end: Optional[int]) -> Iterable[str]:
        """
        Retrieve bill identifier keys optionally constrained to a year range.
        
        Parameters:
        	start (Optional[int]): Earliest year (inclusive) to include when fetching bill keys. If `None`, no lower bound is applied.
        	end (Optional[int]): Latest year (inclusive) to include when fetching bill keys. If `None`, no upper bound is applied.
        
        Returns:
        	iterable_of_keys (Iterable[str]): An iterable of bill identifier strings that fall within the specified year range.
        """
        return []

    def prefetch_member_keys(self) -> Iterable[str]:
        """
        Provide existing member identifier keys from the adapter's store.
        
        Returns:
            Iterable[str]: An iterable of member identifier strings currently present; may be empty.
        """
        return []

    def prefetch_govinfo_keys(self) -> Iterable[str]:
        """
        Provide existing GovInfo record identifiers available in the adapter.
        
        Returns:
            Iterable[str]: An iterable of GovInfo record identifier strings; may be empty.
        """
        return []

    def bulk_upsert_bills(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Perform a bulk upsert of bill records into the configured datastore.
        
        Parameters:
            records (List[Dict[str, Any]]): List of canonical bill records to insert or update.
        
        Returns:
            UpsertSummary: Summary of the upsert operation containing counts for `inserted`, `duplicates`, and `errors`.
        """
        return UpsertSummary(inserted=len(records))

    def bulk_upsert_members(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Perform a bulk upsert of member records into the adapter's store.
        
        Records provided in `records` are treated as upsert candidates and counted as inserted by this adapter implementation.
        
        Parameters:
            records (List[Dict[str, Any]]): Member records to upsert, each represented as a dictionary.
        
        Returns:
            UpsertSummary: Summary of the operation. `inserted` equals the number of provided records; `duplicates` and `errors` are set to 0.
        """
        return UpsertSummary(inserted=len(records))

    def bulk_upsert_govinfo(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Perform a bulk upsert of GovInfo records into the adapter's store.
        
        Parameters:
            records (List[Dict[str, Any]]): List of GovInfo-formatted records to upsert.
        
        Returns:
            UpsertSummary: Summary of the upsert operation. The default implementation treats all provided records as inserted (Inserted count equals number of input records).
        """
        return UpsertSummary(inserted=len(records))


class SQLAlchemyAdapter(BaseDatabaseAdapter):
    """Database adapter that persists to the real PostgreSQL database."""

    def __init__(self):
        """
        Initialize the SQLAlchemy-backed database adapter by loading DB models, creating an engine and session factory, and wiring up model and upsert callables.
        
        This sets up:
        - self.engine: SQLAlchemy engine from database_models.get_engine()
        - self.Session: session factory bound to the engine
        - self.Bill, self.FederalMember, self.GovInfoBill: model classes
        - self._upsert_bill, self._upsert_member, self._upsert_govinfo: helper callables for upsert operations
        
        Raises:
            RuntimeError: If SQLAlchemy's sessionmaker is not available in the runtime.
        """
        from database_models import (
            get_engine,
            Bill,
            FederalMember,
            GovInfoBill,
            upsert_bill,
            upsert_federal_member,
            upsert_govinfo_bill,
        )

        self.engine = get_engine()
        if sessionmaker is None:
            raise RuntimeError("SQLAlchemy is required for SQLAlchemyAdapter")
        self.Session = sessionmaker(bind=self.engine)
        self.Bill = Bill
        self.FederalMember = FederalMember
        self.GovInfoBill = GovInfoBill
        self._upsert_bill = upsert_bill
        self._upsert_member = upsert_federal_member
        self._upsert_govinfo = upsert_govinfo_bill

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional SQLAlchemy session context.
        
        Yields a Session that is committed when the context block exits normally, rolled back if an exception is raised, and closed in all cases.
        
        Returns:
            session (Session): A SQLAlchemy Session instance to use within the context manager.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def prefetch_bill_keys(self, start: Optional[int], end: Optional[int]) -> Iterable[str]:
        """
        Fetches bill identifier keys from the database, optionally filtered by session year.
        
        Parameters:
            start (Optional[int]): Minimum session year to include (inclusive). If None, no lower bound is applied.
            end (Optional[int]): Maximum session year to include (inclusive). If None, no upper bound is applied.
        
        Returns:
            Iterable[str]: An iterable of keys in the format "bill_print_no:session_year" for matching bills.
        """
        if select is None:
            return []
        with self.session_scope() as session:
            query = session.execute(
                select(self.Bill.bill_print_no, self.Bill.bill_session_year)
            )
            results = []
            for bill_print_no, session_year in query:
                if start and session_year < start:
                    continue
                if end and session_year > end:
                    continue
                results.append(f"{bill_print_no}:{session_year}")
            return results

    def prefetch_member_keys(self) -> Iterable[str]:
        """
        Return all stored federal member Bioguide IDs from the database adapter.
        
        Queries the configured SQLAlchemy session for the `bioguide_id` column of the `FederalMember` model and returns a list of non-empty IDs. If the SQLAlchemy `select` function is unavailable in the environment, returns an empty list.
        
        Returns:
            Iterable[str]: List of Bioguide ID strings (empty list if unavailable or none found).
        """
        if select is None:
            return []
        with self.session_scope() as session:
            query = session.execute(select(self.FederalMember.bioguide_id))
            return [row[0] for row in query if row[0]]

    def prefetch_govinfo_keys(self) -> Iterable[str]:
        """
        Return the list of existing GovInfo package IDs stored in the database.
        
        Returns:
            list[str]: A list of package ID strings for GovInfo bills; returns an empty list if the SQLAlchemy `select` helper is unavailable or no package IDs are found.
        """
        if select is None:
            return []
        with self.session_scope() as session:
            query = session.execute(select(self.GovInfoBill.package_id))
            return [row[0] for row in query if row[0]]

    def bulk_upsert_bills(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Upserts a list of bill records into the configured database adapter, returning counts of inserted, duplicate, and failed records.
        
        Parameters:
            records (List[Dict[str, Any]]): List of bill records in the adapter's expected schema to be upserted.
        
        Returns:
            UpsertSummary: Summary of the operation with `inserted`, `duplicates`, and `errors` counts. Integrity constraint violations are counted as duplicates; other SQLAlchemy errors are counted as errors and logged.
        """
        summary = UpsertSummary()
        if not records:
            return summary

        with self.session_scope() as session:
            for record in records:
                try:
                    self._upsert_bill(session, record)
                    summary.inserted += 1
                except IntegrityError:
                    session.rollback()
                    summary.duplicates += 1
                except SQLAlchemyError as exc:  # pragma: no cover - database specific
                    logger.exception("Failed to upsert bill", extra={"error": str(exc), "record": record})
                    summary.errors += 1
                    session.rollback()
        return summary

    def bulk_upsert_members(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Upserts a list of member records into the configured database and returns a summary of the operation.
        
        Parameters:
            records (List[Dict[str, Any]]): Iterable of member records in the internal canonical schema to be upserted.
        
        Returns:
            UpsertSummary: Summary with counts for `inserted`, `duplicates`, and `errors`.
            
        Notes:
            - Records that violate unique constraints are counted as duplicates.
            - Database errors during an individual upsert are logged and counted as errors.
        """
        summary = UpsertSummary()
        if not records:
            return summary

        with self.session_scope() as session:
            for record in records:
                try:
                    self._upsert_member(session, record)
                    summary.inserted += 1
                except IntegrityError:
                    session.rollback()
                    summary.duplicates += 1
                except SQLAlchemyError as exc:  # pragma: no cover
                    logger.exception("Failed to upsert member", extra={"error": str(exc), "record": record})
                    summary.errors += 1
                    session.rollback()
        return summary

    def bulk_upsert_govinfo(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Upserts a batch of GovInfo records into the database and returns a summary of the operation.
        
        Parameters:
            records (List[Dict[str, Any]]): Iterable of GovInfo record dictionaries in the adapter's expected schema.
        
        Returns:
            UpsertSummary: Counts of `inserted`, `duplicates`, and `errors` produced while processing `records`.
            - `duplicates` is incremented for records that violate uniqueness constraints.
            - `errors` is incremented for other database-related failures; such failures are logged.
        """
        summary = UpsertSummary()
        if not records:
            return summary

        with self.session_scope() as session:
            for record in records:
                try:
                    self._upsert_govinfo(session, record)
                    summary.inserted += 1
                except IntegrityError:
                    session.rollback()
                    summary.duplicates += 1
                except SQLAlchemyError as exc:  # pragma: no cover
                    logger.exception("Failed to upsert GovInfo bill", extra={"error": str(exc), "record": record})
                    summary.errors += 1
                    session.rollback()
        return summary


class InMemoryAdapter(BaseDatabaseAdapter):
    """In-memory adapter used for tests and local development."""

    def __init__(self):
        """
        Initialize the in-memory persistence adapter used for testing and local runs.
        
        Attributes:
            _bills (dict): Mapping of bill keys to bill records.
            _members (dict): Mapping of member identifiers to member records.
            _govinfo (dict): Mapping of GovInfo identifiers to GovInfo records.
            _lock (threading.Lock): Thread-safe lock protecting concurrent access to the in-memory stores.
        """
        self._bills: Dict[str, Dict[str, Any]] = {}
        self._members: Dict[str, Dict[str, Any]] = {}
        self._govinfo: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _prefetch(self, store: Dict[str, Dict[str, Any]]) -> Iterable[str]:
        """
        Retrieve all keys from the given in-memory store in a thread-safe manner.
        
        Parameters:
            store (Dict[str, Dict[str, Any]]): Mapping of record keys to record data used by the adapter.
        
        Returns:
            keys (Iterable[str]): List of keys present in the provided store.
        """
        with self._lock:
            return list(store.keys())

    def prefetch_bill_keys(self, start: Optional[int], end: Optional[int]) -> Iterable[str]:
        """
        Return all stored bill keys.
        
        Parameters:
            start (Optional[int]): Inclusive start year to filter keys by year; currently ignored.
            end (Optional[int]): Inclusive end year to filter keys by year; currently ignored.
        
        Returns:
            Iterable[str]: An iterable of bill identifier strings present in the in-memory store.
        """
        return self._prefetch(self._bills)

    def prefetch_member_keys(self) -> Iterable[str]:
        """
        Return all stored federal member identifiers from the in-memory adapter.
        
        Returns:
            Iterable[str]: An iterable of member identifier strings currently present in the in-memory store.
        """
        return self._prefetch(self._members)

    def prefetch_govinfo_keys(self) -> Iterable[str]:
        """
        Return all stored GovInfo record keys from the in-memory adapter.
        
        Returns:
            Iterable[str]: An iterable of GovInfo record identifiers (strings) present in the adapter's store.
        """
        return self._prefetch(self._govinfo)

    def _bulk_store(self, store: Dict[str, Dict[str, Any]], records: List[Tuple[str, Dict[str, Any]]]) -> UpsertSummary:
        """
        Atomically insert new records into an in-memory store while counting inserted and duplicate entries.
        
        Parameters:
            store (Dict[str, Dict[str, Any]]): In-memory mapping of keys to records that will be updated in-place.
            records (List[Tuple[str, Dict[str, Any]]]): Sequence of (key, record) pairs to insert.
        
        Returns:
            UpsertSummary: Summary with `inserted` set to the number of records added and `duplicates` set to the number of keys that already existed.
        """
        summary = UpsertSummary()
        with self._lock:
            for key, record in records:
                if key in store:
                    summary.duplicates += 1
                    continue
                store[key] = record
                summary.inserted += 1
        return summary

    def bulk_upsert_bills(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Upserts multiple bill records into the in-memory bills store and returns a summary of the operation.
        
        Each input record must include the keys 'bill_print_no' and 'bill_session_year'; records are keyed as "bill_print_no:bill_session_year" to detect duplicates.
        
        Parameters:
            records (List[Dict[str, Any]]): List of bill records to insert or update.
        
        Returns:
            UpsertSummary: Counts of inserted records, detected duplicates, and errors.
        """
        tuples = [(f"{r['bill_print_no']}:{r['bill_session_year']}", r) for r in records]
        return self._bulk_store(self._bills, tuples)

    def bulk_upsert_members(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Insert or update multiple member records into the in-memory member store using `bioguide_id` as the key.
        
        Parameters:
            records (List[Dict[str, Any]]): Iterable of member record dictionaries. Only records with a truthy `bioguide_id` field are considered; others are ignored.
        
        Returns:
            UpsertSummary: Counts of inserted records, detected duplicates, and errors.
        """
        tuples = [(r['bioguide_id'], r) for r in records if r.get('bioguide_id')]
        return self._bulk_store(self._members, tuples)

    def bulk_upsert_govinfo(self, records: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Insert or update GovInfo records into the in-memory store using each record's `package_id` as the key.
        
        Parameters:
            records (List[Dict[str, Any]]): List of GovInfo record dictionaries. Records without a `package_id` are ignored.
        
        Returns:
            UpsertSummary: Summary of the upsert operation with `inserted`, `duplicates`, and `errors` counts.
        """
        tuples = [(r['package_id'], r) for r in records if r.get('package_id')]
        return self._bulk_store(self._govinfo, tuples)


class IngestionEngine:
    """
    High-performance ingestion engine with GPU/parallel/async support
    """

    def __init__(self, enable_parallel: bool = True, max_workers: int = 4,
                 enable_gpu: bool = False, gpu_memory_limit: int = None,
                 batch_size: int = 1000, timeout: int = 3600,
                 db_adapter: Optional[BaseDatabaseAdapter] = None):
        """
                 Initialize the ingestion engine and configure execution, GPU, batching, and persistence.
                 
                 Parameters:
                     enable_parallel (bool): Whether to enable concurrent execution across threads/processes.
                     max_workers (int): Maximum number of worker threads/processes to allocate when parallelism is enabled.
                     enable_gpu (bool): Request GPU-accelerated processing; actual GPU use depends on availability.
                     gpu_memory_limit (int | None): Per-device GPU memory limit in megabytes to apply if GPU is enabled.
                     batch_size (int): Number of records processed per batch during ingestion.
                     timeout (int): Default operation timeout in seconds for long-running ingestion tasks.
                     db_adapter (BaseDatabaseAdapter | None): Optional persistence adapter; a default adapter is created if omitted.
                 
                 Side effects:
                     - Creates thread and (optional) process executors for concurrent work.
                     - Attempts to configure GPU resources when requested and available.
                     - Initializes performance monitoring, HTTP session placeholders, persistence adapter, deduplication caches, and internal synchronization/metrics structures.
                 """
                 self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.enable_gpu = enable_gpu and GPU_AVAILABLE
        self.gpu_memory_limit = gpu_memory_limit
        self.batch_size = batch_size
        self.timeout = timeout

        # Initialize executors
        thread_workers = max(1, max_workers if enable_parallel else 1)
        self.thread_executor = ThreadPoolExecutor(max_workers=thread_workers)
        process_workers = max_workers // 2 if enable_parallel and max_workers > 1 else 0
        self.process_executor = ProcessPoolExecutor(max_workers=process_workers) if process_workers else None

        # GPU setup
        if self.enable_gpu:
            self._setup_gpu()

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

        # Session management for HTTP requests
        self.http_session = None
        self.aiohttp_session = None

        # Database adapter and dedupe caches
        self.db_adapter = db_adapter or self._create_default_adapter()
        self._existing_bill_keys: set[str] = set()
        self._existing_member_ids: set[str] = set()
        self._existing_govinfo_keys: set[str] = set()
        self._existing_loaded = {"bills": False, "members": False, "govinfo": False}
        self._state_lock = threading.Lock()
        self._run_metrics = defaultdict(int)

        logger.info(f"IngestionEngine initialized: parallel={enable_parallel}, gpu={self.enable_gpu}, workers={max_workers}")

    def _setup_gpu(self):
        """
        Configure the GPU environment for the ingestion engine.
        
        If GPUs are not available, disables GPU usage on the engine. If a per-process GPU memory limit is configured, applies that limit to the primary CUDA device and clears the CUDA cache to free memory. If configuration or initialization fails, disables GPU usage and records the failure.
        """
        if not GPU_AVAILABLE:
            logger.warning("GPU requested but not available")
            self.enable_gpu = False
            return

        try:
            # Set GPU memory limit
            if self.gpu_memory_limit:
                torch.cuda.set_per_process_memory_fraction(
                    self.gpu_memory_limit / torch.cuda.get_device_properties(0).total_memory
                )

            # Empty cache to start fresh
            torch.cuda.empty_cache()

            logger.info(f"GPU setup complete: {GPU_COUNT} devices available")
        except Exception as e:
            logger.error(f"GPU setup failed: {e}")
            self.enable_gpu = False

    def _create_default_adapter(self) -> BaseDatabaseAdapter:
        """
        Create the default database adapter for ingestion.
        
        Returns:
            A BaseDatabaseAdapter instance: a SQLAlchemyAdapter when available, otherwise an InMemoryAdapter as a fallback.
        """
        try:
            adapter = SQLAlchemyAdapter()
            logger.info("Using SQLAlchemyAdapter for ingestion persistence")
            return adapter
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning(
                "Falling back to in-memory adapter for ingestion",
                extra={"error": str(exc)}
            )
            return InMemoryAdapter()

    async def _run_in_thread(self, func: Callable, *args, **kwargs):
        """
        Execute a synchronous callable in the engine's thread pool and return its result.
        
        Parameters:
            func (Callable): The synchronous function to execute.
            *args: Positional arguments to pass to `func`.
            **kwargs: Keyword arguments to pass to `func`.
        
        Returns:
            The value returned by `func` when executed with the provided arguments.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.thread_executor, lambda: func(*args, **kwargs))

    async def _ensure_existing_bill_keys(self, start: Optional[int], end: Optional[int]):
        """
        Ensure bill keys within an optional year range are loaded into the engine's in-memory cache.
        
        If the cache is already populated for bills, this is a no-op. Otherwise it fetches existing bill keys from the configured database adapter and updates the engine's internal cache and loaded flag.
        
        Parameters:
            start (Optional[int]): Start year (inclusive) to restrict which bill keys to prefetch. If None, no lower bound is applied.
            end (Optional[int]): End year (inclusive) to restrict which bill keys to prefetch. If None, no upper bound is applied.
        """
        if self._existing_loaded["bills"]:
            return
        keys = await self._run_in_thread(self.db_adapter.prefetch_bill_keys, start, end)
        with self._state_lock:
            self._existing_bill_keys.update(keys)
            self._existing_loaded["bills"] = True
        logger.debug("Prefetched bill keys", extra={"count": len(self._existing_bill_keys)})

    async def _ensure_existing_member_ids(self):
        """
        Populate the engine's in-memory cache of existing federal member IDs by fetching them from the configured database adapter.
        
        If the cache is already populated this method is a no-op. On success it updates the engine's internal member ID set and marks the members cache as loaded; it also emits a debug log with the resulting count.
        """
        if self._existing_loaded["members"]:
            return
        ids = await self._run_in_thread(self.db_adapter.prefetch_member_keys)
        with self._state_lock:
            self._existing_member_ids.update(ids)
            self._existing_loaded["members"] = True
        logger.debug("Prefetched member ids", extra={"count": len(self._existing_member_ids)})

    async def _ensure_existing_govinfo_keys(self):
        """
        Populate the in-memory cache of existing GovInfo keys if they haven't been loaded yet.
        
        If the cache is not yet populated, fetches GovInfo keys from the configured database adapter (performed in a worker thread), updates the engine's in-memory key set under the internal state lock, and marks the GovInfo cache as loaded. If the cache is already marked loaded, this is a no-op. Logs the resulting cached key count for debugging.
        """
        if self._existing_loaded["govinfo"]:
            return
        keys = await self._run_in_thread(self.db_adapter.prefetch_govinfo_keys)
        with self._state_lock:
            self._existing_govinfo_keys.update(keys)
            self._existing_loaded["govinfo"] = True
        logger.debug("Prefetched GovInfo keys", extra={"count": len(self._existing_govinfo_keys)})

    def _dedupe_records(self, records: List[Dict[str, Any]], cache: set, key_func: Callable[[Dict[str, Any]], str]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Filter the input records by removing those whose generated keys are already present in the provided cache, updating the cache with new keys.
        
        Parameters:
            records (List[Dict[str, Any]]): Iterable of record dictionaries to deduplicate.
            cache (set): Mutable set of keys representing already-seen records; the set is updated in-place with keys of returned records.
            key_func (Callable[[Dict[str, Any]], str]): Function that returns a string key for a record; records with falsy keys are skipped.
        
        Returns:
            Tuple[List[Dict[str, Any]], int]: A tuple `(new_records, duplicates)` where `new_records` is the list of records whose keys were not found in `cache`, and `duplicates` is the number of records skipped because their key was already present.
        """
        new_records = []
        duplicates = 0
        with self._state_lock:
            for record in records:
                key = key_func(record)
                if not key:
                    continue
                if key in cache:
                    duplicates += 1
                    continue
                cache.add(key)
                new_records.append(record)
        if duplicates:
            logger.info("Duplicate records skipped", extra={"count": duplicates})
        return new_records, duplicates

    def _record_summary(self, summary: UpsertSummary, prefix: str):
        """
        Update the engine's run metrics counters for a batch upsert.
        
        Parameters:
            summary (UpsertSummary): Counts from a single upsert operation (inserted, duplicates, errors).
            prefix (str): Metric name prefix (e.g., 'bills', 'members', 'govinfo') used to update keys
                '{prefix}_inserted', '{prefix}_duplicates', and '{prefix}_errors'.
        
        """
        with self._state_lock:
            self._run_metrics[f'{prefix}_duplicates'] += summary.duplicates
            self._run_metrics[f'{prefix}_errors'] += summary.errors
            self._run_metrics[f'{prefix}_inserted'] += summary.inserted

    def _build_completion_criteria(self, category: str, inserted: int, duplicates: int,
                                   extra: Dict[str, Any]) -> Dict[str, Any]:
        """
                                   Builds a structured completion criteria dictionary for a given ingestion category.
                                   
                                   Parameters:
                                   	category (str): Category of ingestion; one of 'congress', 'members', or 'govinfo'.
                                   	inserted (int): Number of records inserted during the ingestion step.
                                   	duplicates (int): Number of duplicate records detected during deduplication.
                                   	extra (Dict[str, Any]): Additional context used to populate criteria. Expected keys by category:
                                   		- 'congress': may include 'api_calls' (int) and 'congress' (int).
                                   		- 'members': may include 'chunks_processed' (int).
                                   		- 'govinfo': may include 'collection' (str) and 'time_window' (any truthy value).
                                   
                                   Returns:
                                   	criteria (Dict[str, Any]): A dictionary with two top-level keys:
                                   		- 'mandatory': mapping of checks that must be satisfied (booleans or presence checks).
                                   		- 'optional': mapping of supplemental metadata or flags relevant to the category.
                                   """
                                   criteria = {
            "mandatory": {
                "records_inserted_non_negative": inserted >= 0,
                "deduplication_executed": duplicates >= 0,
                "logging_enabled": True,
            },
            "optional": {}
        }

        if category == 'congress':
            criteria['mandatory']["api_calls_recorded"] = extra.get('api_calls', 0) > 0
            criteria['mandatory']["congress_number"] = extra.get('congress') is not None
            criteria['optional']["gpu_enabled"] = self.enable_gpu
        elif category == 'members':
            criteria['mandatory']["unique_members_processed"] = inserted + duplicates > 0
            criteria['optional']["chunks_processed"] = extra.get('chunks_processed', 0)
            criteria['optional']["parallel_enabled"] = self.enable_parallel
        elif category == 'govinfo':
            criteria['mandatory']["collection_provided"] = bool(extra.get('collection'))
            criteria['optional']["time_window_applied"] = bool(extra.get('time_window'))
            criteria['optional']["gpu_enabled"] = self.enable_gpu

        return criteria

    @staticmethod
    def _parse_date(date_value: Optional[str]):
        """
        Parse a date string using common ISO-like formats.
        
        Parameters:
            date_value (Optional[str]): A date/time string to parse. Accepted formats: "YYYY-MM-DD", "YYYY-MM-DDTHH:MM:SSZ", and "YYYY-MM-DDTHH:MM:SS". If falsy or not matching supported formats, parsing fails.
        
        Returns:
            `datetime.date` if the input was successfully parsed, `None` otherwise.
        """
        if not date_value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(date_value, fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    def _map_congress_bill(self, bill: Dict[str, Any], congress_num: int) -> Dict[str, Any]:
        """
        Map a raw Congress.gov bill payload into the engine's canonical bill schema.
        
        Parameters:
        	bill (Dict[str, Any]): Raw bill object as returned by the Congress.gov API; may contain alternate field names (e.g., "type" or "billType", "number" or "billNumber", "latestAction" or "latestActionDetails").
        	congress_num (int): Congress session number to associate with the mapped bill.
        
        Returns:
        	Dict[str, Any]: Canonical bill dictionary with keys:
        		- bill_print_no: Print identifier (e.g., "HR123").
        		- bill_session_year: The provided congress_num.
        		- title: Official or provided title.
        		- summary: Bill summary if present.
        		- active_version: Active/latest version code or value.
        		- data_source: Literal "congress.gov".
        		- congress: The provided congress_num.
        		- bill_type: Uppercase bill type (e.g., "HR", "S").
        		- sponsor_party: Sponsor party if available.
        		- sponsor_state: Sponsor state if available.
        		- status: Human-readable latest status or action text.
        		- status_date: Parsed date of the latest action (or None if unparsable).
        		- short_title: Short title when available, otherwise the title.
        """
        bill_type = (bill.get("type") or bill.get("billType") or "").upper()
        number = str(bill.get("number") or bill.get("billNumber") or "").upper()
        bill_print_no = f"{bill_type}{number}".strip()
        latest_action = bill.get("latestAction", {}) or bill.get("latestActionDetails", {})
        status = latest_action.get("actionDescription") or latest_action.get("text") or bill.get("status")
        introduced = bill.get("introducedDate") or bill.get("introducedOn")

        return {
            "bill_print_no": bill_print_no,
            "bill_session_year": congress_num,
            "title": bill.get("title") or bill.get("titleOfficial"),
            "summary": bill.get("summary"),
            "active_version": bill.get("latestVersion", {}).get("versionCode") if isinstance(bill.get("latestVersion"), dict) else bill.get("latestVersion"),
            "data_source": "congress.gov",
            "congress": congress_num,
            "bill_type": bill_type,
            "sponsor_party": bill.get("sponsors", [{}])[0].get("party") if bill.get("sponsors") else None,
            "sponsor_state": bill.get("sponsors", [{}])[0].get("state") if bill.get("sponsors") else None,
            "status": status,
            "status_date": self._parse_date(latest_action.get("actionDate") or latest_action.get("date")),
            "short_title": bill.get("shortTitle") or bill.get("title")
        }

    def _map_member(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a raw member record from the source API into the engine's canonical member schema.
        
        Parameters:
        	member (Dict[str, Any]): Raw member object returned by the source API (e.g., Congress.gov).
        
        Returns:
        	Dict[str, Any]: Canonical member dictionary with keys:
        		- bioguide_id: Bioguide identifier if present.
        		- first_name: Given name.
        		- last_name: Family name.
        		- full_name: Preferred full name.
        		- party: Party affiliation.
        		- state: State represented.
        		- district: Congressional district (if applicable).
        		- chamber: Lowercased chamber name ("house"/"senate") or None.
        		- active: `True` if currently serving, `False` otherwise.
        		- congress: Congress number associated with the record or its first term.
        		- date_of_birth: Parsed birth date (or `None` if unavailable).
        		- place_of_birth: Birth place string (if available).
        		- education: Education information from the biography.
        		- profession: Profession information from the biography.
        		- contact_website: Public contact website (if provided).
        		- office_address: Office address string (if provided).
        		- terms: List of term objects as provided by the source.
        		- committees: List of committee assignments (if provided).
        		- last_updated: Timestamp of the last update from biography or record.
        """
        biography = member.get("biography", {})
        terms = member.get("terms") or []
        return {
            "bioguide_id": member.get("bioguideId") or member.get("bioguideID"),
            "first_name": member.get("firstName"),
            "last_name": member.get("lastName"),
            "full_name": member.get("name") or member.get("fullName"),
            "party": member.get("party"),
            "state": member.get("state"),
            "district": member.get("district"),
            "chamber": (member.get("chamber") or "").lower() or None,
            "active": bool(member.get("currentMember", True)),
            "congress": member.get("congress") or (terms[0].get("congress") if terms else None),
            "date_of_birth": self._parse_date(biography.get("birthDate") or biography.get("dateOfBirth")),
            "place_of_birth": biography.get("placeOfBirth"),
            "education": biography.get("education"),
            "profession": biography.get("profession"),
            "contact_website": member.get("contactWebsite"),
            "office_address": member.get("office"),
            "terms": terms,
            "committees": member.get("committees"),
            "last_updated": biography.get("lastUpdated") or member.get("updateDate")
        }

    def _store_members_sync(self, members: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Persist a list of member records into the configured database adapter after deduplicating against the in-memory member ID cache.
        
        Parameters:
            members (List[Dict[str, Any]]): Member records already mapped to the internal schema; each record should include a `bioguide_id` when available.
        
        Returns:
            UpsertSummary: Summary counts for the operation:
                - `inserted`: number of records inserted,
                - `duplicates`: number of duplicates (including those found during deduplication and reported by the adapter),
                - `errors`: number of records that failed to upsert.
        """
        if not members:
            return UpsertSummary()

        key_func = lambda record: record.get('bioguide_id') or ''
        new_records, duplicates = self._dedupe_records(members, self._existing_member_ids, key_func)

        if not new_records:
            return UpsertSummary(inserted=0, duplicates=duplicates, errors=0)

        summary = self.db_adapter.bulk_upsert_members(new_records)
        summary.duplicates += duplicates
        return summary

    def _map_govinfo_bill(self, bill: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a raw GovInfo API item into the engine's canonical GovInfo bill schema.
        
        Parameters:
            bill (dict): Raw GovInfo item (API response) containing top-level fields and a nested "metadata" object.
        
        Returns:
            dict: Canonical GovInfo bill with keys:
                - package_id: GovInfo package identifier.
                - congress: Congress number associated with the bill.
                - bill_number: Official bill number.
                - title: Bill title.
                - collection_code: Collection code or name for the GovInfo item.
                - last_modified: Last modified timestamp from metadata.
                - originating_office: Originating office information.
                - download_url: Primary download URL for the item.
        """
        metadata = bill.get("metadata", {})
        return {
            "package_id": bill.get("packageId") or bill.get("package_id"),
            "congress": metadata.get("congress"),
            "bill_number": metadata.get("billNumber") or bill.get("billNumber"),
            "title": metadata.get("title") or bill.get("title"),
            "collection_code": metadata.get("collectionCode") or bill.get("collection"),
            "last_modified": metadata.get("lastModified"),
            "originating_office": metadata.get("originatingOffice"),
            "download_url": bill.get("download") or metadata.get("download")
        }

    async def __aenter__(self):
        """
        Prepare the ingestion engine for use by initializing the HTTP client session used for API requests.
        
        Returns:
            self: The engine instance with an active aiohttp ClientSession assigned to `self.aiohttp_session`.
        """
        # Create HTTP sessions
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        self.aiohttp_session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.aiohttp_session:
            await self.aiohttp_session.close()

        # Close executors
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
        if self.process_executor:
            self.process_executor.shutdown(wait=True)

        # Clean up GPU memory
        if self.enable_gpu and torch:
            torch.cuda.empty_cache()

    async def ingest_congress_data(self, api_key: str = None, start_congress: int = 80,
                                  end_congress: int = 118) -> IngestionResult:
        """
                                  Orchestrates ingestion of congressional bills across a range of Congress sessions.
                                  
                                  Parameters:
                                      api_key (str | None): Optional API key to authenticate requests against the Congress.gov API.
                                      start_congress (int): Starting Congress number (inclusive).
                                      end_congress (int): Ending Congress number (inclusive).
                                  
                                  Returns:
                                      IngestionResult: Aggregated ingestion outcome containing:
                                          - records_processed: total number of records ingested,
                                          - duration: elapsed time in seconds,
                                          - success: `true` if no errors occurred, `false` otherwise,
                                          - errors: list of error messages encountered,
                                          - performance_metrics: runtime metrics including API call counts and monitoring data,
                                          - data_quality_metrics: includes `duplicates_skipped`, `segments_processed`, and a `completion_criteria` structure with per-segment completion details.
                                  """
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("congress_ingestion")

        try:
            logger.info(f"Starting congress data ingestion: {start_congress}-{end_congress}")

            # Create ingestion tasks
            tasks = []
            for congress_num in range(start_congress, end_congress + 1):
                task = self._ingest_congress_async(congress_num, api_key)
                tasks.append(task)

            # Execute with progress tracking
            results = []
            with tqdm(total=len(tasks), desc="Congress ingestion") as pbar:
                if self.enable_parallel and len(tasks) > 1:
                    # Parallel execution
                    semaphore = asyncio.Semaphore(self.max_workers)

                    async def bounded_task(task_func):
                        async with semaphore:
                            result = await task_func
                            pbar.update(1)
                            return result

                    bounded_tasks = [bounded_task(task) for task in tasks]
                    results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
                else:
                    # Sequential execution
                    for task in tasks:
                        result = await task
                        results.append(result)
                        pbar.update(1)

            valid_results = [r for r in results if isinstance(r, IngestionResult)]
            total_records = sum(r.records_processed for r in valid_results)
            total_duplicates = sum(r.data_quality_metrics.get('duplicates_skipped', 0) for r in valid_results)
            api_calls = sum(r.performance_metrics.get('api_calls', 0) for r in valid_results)
            errors = [str(r) for r in results if isinstance(r, Exception)]
            for res in valid_results:
                if res.errors:
                    errors.extend(res.errors)

            # Performance metrics
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)
            duration = time.time() - start_time
            perf_metrics['api_calls'] = perf_metrics.get('api_calls', 0) + api_calls

            completion = {
                'mandatory': {
                    'segments_completed': len(valid_results) == len(results),
                    'total_records_non_negative': total_records >= 0,
                    'deduplication_executed': total_duplicates >= 0,
                },
                'optional': {
                    'segment_details': [res.data_quality_metrics.get('completion_criteria', {}) for res in valid_results]
                }
            }

            result = IngestionResult(
                records_processed=total_records,
                duration=duration,
                success=len(errors) == 0,
                errors=errors,
                performance_metrics=perf_metrics,
                data_quality_metrics={
                    'duplicates_skipped': total_duplicates,
                    'segments_processed': len(valid_results),
                    'completion_criteria': completion
                }
            )

            logger.info(f"Congress ingestion completed: {total_records} records in {duration:.2f}s")
            return result

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"Congress ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _ingest_congress_async(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """Ingest data for a specific congress number"""
        try:
            # Use GPU acceleration if available
            if self.enable_gpu:
                return await self._gpu_ingest_congress(congress_num, api_key)
            else:
                return await self._cpu_ingest_congress(congress_num, api_key)
        except Exception as e:
            logger.error(f"Failed to ingest congress {congress_num}: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _gpu_ingest_congress(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """
        Ingest congressional bills for a given Congress using RAPIDS GPU acceleration; falls back to the CPU ingestion path if RAPIDS is unavailable or an error occurs.
        
        Parameters:
            congress_num (int): Numeric identifier of the Congress to ingest (e.g., 117).
            api_key (str, optional): API key for Congress.gov requests; if omitted, the engine's default behavior is used.
        
        Returns:
            IngestionResult: Summary of the ingestion run including:
                - records_processed: number of records inserted.
                - performance_metrics: contains at least 'gpu_processing_time' (seconds) when GPU was used and 'api_calls'.
                - data_quality_metrics: contains at least 'duplicates_skipped', 'source', and 'completion_criteria'.
        """
        if not RAPIDS_AVAILABLE:
            # Fallback to CPU if RAPIDS not available
            return await self._cpu_ingest_congress(congress_num, api_key)

        try:
            fetch = await self._fetch_congress_bills(congress_num, api_key)
            bills_data = fetch.records

            if not bills_data:
                completion = self._build_completion_criteria(
                    'congress', 0, 0, {"api_calls": fetch.api_calls, "congress": congress_num}
                )
                return IngestionResult(
                    records_processed=0,
                    performance_metrics={'gpu_processing_time': 0.0, 'api_calls': fetch.api_calls},
                    data_quality_metrics={'duplicates_skipped': 0, 'source': fetch.source, 'completion_criteria': completion}
                )

            # Process on GPU using RAPIDS
            gpu_start = time.time()

            # Convert to GPU DataFrame
            df = cudf.DataFrame(bills_data)

            # GPU-accelerated data processing
            df = self._gpu_process_bills_dataframe(df)

            # Convert back to CPU for database insertion
            cpu_df = df.to_pandas()

            gpu_time = time.time() - gpu_start

            # Insert to database
            insert_result = await self._insert_bills_batch(cpu_df.to_dict('records'))
            completion = self._build_completion_criteria(
                'congress', insert_result['inserted'], insert_result['duplicates'],
                {"api_calls": fetch.api_calls, "congress": congress_num}
            )

            return IngestionResult(
                records_processed=insert_result['inserted'],
                performance_metrics={'gpu_processing_time': gpu_time, 'api_calls': fetch.api_calls},
                data_quality_metrics={
                    'duplicates_skipped': insert_result['duplicates'],
                    'source': fetch.source,
                    'completion_criteria': completion
                }
            )

        except Exception as e:
            logger.error(f"GPU congress ingestion failed: {e}")
            # Fallback to CPU
            return await self._cpu_ingest_congress(congress_num, api_key)

    def _gpu_process_bills_dataframe(self, df):
        """Process bills dataframe on GPU"""
        # Text processing on GPU
        if 'title' in df.columns:
            df['title_length'] = df['title'].str.len()
            df['title_words'] = df['title'].str.count(' ') + 1

        # Date processing
        if 'introduced_date' in df.columns:
            df['introduced_date'] = cudf.to_datetime(df['introduced_date'])

        # Categorize bill types
        if 'bill_type' in df.columns:
            df['is_resolution'] = df['bill_type'].str.contains('res', case=False)
            df['is_joint'] = df['bill_type'].str.contains('jres|sres', case=False)

        return df

    async def _cpu_ingest_congress(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """
        Ingest congressional bills for a specific Congress using the CPU processing path and persist them via the engine's database adapter.
        
        Parameters:
        	congress_num (int): Numeric identifier of the Congress to ingest (e.g., 117).
        	api_key (str, optional): API key to use for upstream requests; if omitted, the engine's default configuration is used.
        
        Returns:
        	IngestionResult: Result summary containing
        		- records_processed: number of records inserted,
        		- duration: total time taken (may be zero if not measured here),
        		- success: boolean indicating overall success,
        		- errors: list of error messages per failed batch,
        		- performance_metrics: includes `api_calls` used,
        		- data_quality_metrics: includes `duplicates_skipped`, `source`, and `completion_criteria`.
        """
        try:
            fetch = await self._fetch_congress_bills(congress_num, api_key)
            bills_data = fetch.records

            if not bills_data:
                completion = self._build_completion_criteria(
                    'congress', 0, 0, {"api_calls": fetch.api_calls, "congress": congress_num}
                )
                return IngestionResult(
                    records_processed=0,
                    performance_metrics={'api_calls': fetch.api_calls},
                    data_quality_metrics={'duplicates_skipped': 0, 'source': fetch.source, 'completion_criteria': completion}
                )

            total_inserted = 0
            duplicates = 0
            errors = []
            for i in range(0, len(bills_data), self.batch_size):
                batch = bills_data[i:i + self.batch_size]
                result = await self._insert_bills_batch(batch)
                total_inserted += result['inserted']
                duplicates += result['duplicates']
                if result['errors']:
                    errors.append(f"batch_{i // self.batch_size}: {result['errors']}")

            completion = self._build_completion_criteria(
                'congress', total_inserted, duplicates,
                {"api_calls": fetch.api_calls, "congress": congress_num}
            )

            return IngestionResult(
                records_processed=total_inserted,
                errors=errors,
                performance_metrics={'api_calls': fetch.api_calls},
                data_quality_metrics={
                    'duplicates_skipped': duplicates,
                    'source': fetch.source,
                    'completion_criteria': completion
                }
            )

        except Exception as e:
            logger.error(f"CPU congress ingestion failed: {e}")
            raise

    async def _fetch_congress_bills(self, congress_num: int, api_key: str = None) -> FetchResponse:
        """
        Fetch mapped bill records for a specific Congress from the Congress.gov API, following pagination until no further pages.
        
        Parameters:
            congress_num (int): Numeric Congress identifier to fetch bills for.
            api_key (str, optional): Congress.gov API key to include in requests.
        
        Returns:
            FetchResponse: Container with:
                - `records`: list of mapped bill dictionaries (only bills with a `bill_print_no` are included),
                - `api_calls`: number of API requests made,
                - `source`: `"congress.gov"`,
                - `metadata`: dictionary containing the `congress` number.
        """
        base_url = f"https://api.congress.gov/v3/bill/{congress_num}"
        params = {'format': 'json', 'limit': self.batch_size}
        if api_key:
            params['api_key'] = api_key

        api_calls = 0
        records: List[Dict[str, Any]] = []
        url = base_url
        next_params = params

        while url:
            try:
                async with self.aiohttp_session.get(url, params=next_params, timeout=self.timeout) as response:
                    api_calls += 1
                    if response.status != 200:
                        logger.warning(
                            "Congress API request failed",
                            extra={"status": response.status, "congress": congress_num}
                        )
                        break

                    payload = await response.json()
                    bills = payload.get('bills', [])
                    for bill in bills:
                        mapped = self._map_congress_bill(bill, congress_num)
                        if mapped.get('bill_print_no'):
                            records.append(mapped)

                    pagination = payload.get('pagination', {})
                    next_link = pagination.get('next')
                    if next_link:
                        url = next_link
                        next_params = None  # absolute URL already contains params
                    else:
                        break

                    await asyncio.sleep(0)  # yield control
            except asyncio.TimeoutError:
                logger.warning("Congress API request timed out", extra={"congress": congress_num})
                break
            except Exception as exc:
                logger.error("Failed to fetch Congress data", extra={"error": str(exc), "congress": congress_num})
                break

        return FetchResponse(records=records, api_calls=api_calls, source="congress.gov", metadata={"congress": congress_num})

    async def _insert_bills_batch(self, bills: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert a batch of canonical bill records into the configured database adapter, skipping records already present.
        
        Parameters:
            bills (List[Dict[str, Any]]): List of canonical bill records. Each record is expected to include keys used for deduplication such as
                `bill_print_no` and `bill_session_year`.
        
        Returns:
            Dict[str, int]: Summary counts with keys:
                - "inserted": number of records successfully inserted,
                - "duplicates": number of records identified as duplicates (both pre-existing and within the batch),
                - "errors": number of records that failed to upsert.
        """
        if not bills:
            return {"inserted": 0, "duplicates": 0, "errors": 0}

        years = [record.get('bill_session_year') for record in bills if record.get('bill_session_year') is not None]
        start_year = min(years) if years else None
        end_year = max(years) if years else None

        await self._ensure_existing_bill_keys(start_year, end_year)

        key_func = lambda record: f"{record.get('bill_print_no')}:{record.get('bill_session_year')}"
        new_records, duplicates = self._dedupe_records(bills, self._existing_bill_keys, key_func)

        if not new_records:
            self._run_metrics['bill_duplicates'] += duplicates
            return {"inserted": 0, "duplicates": duplicates, "errors": 0}

        summary: UpsertSummary = await self._run_in_thread(self.db_adapter.bulk_upsert_bills, new_records)
        summary.duplicates += duplicates
        self._record_summary(summary, 'bill')

        return {"inserted": summary.inserted, "duplicates": summary.duplicates, "errors": summary.errors}

    async def _insert_govinfo_batch(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert a batch of GovInfo records into the configured database adapter, deduplicating against cached package IDs.
        
        This method ensures existing GovInfo package IDs are prefetched, removes records whose `package_id` already exists in the engine cache, and delegates insertion of the remaining records to the engine's database adapter. It updates the engine's internal run metrics with the resulting upsert summary.
        
        Parameters:
            records (List[Dict[str, Any]]): List of GovInfo records in the engine's canonical schema. Each record should include a `package_id` key used for deduplication.
        
        Returns:
            dict: A summary with keys:
                - inserted (int): number of records successfully inserted.
                - duplicates (int): number of records identified as duplicates (both pre-existing and in-batch).
                - errors (int): number of records that failed to insert.
        """
        if not records:
            return {"inserted": 0, "duplicates": 0, "errors": 0}

        await self._ensure_existing_govinfo_keys()

        key_func = lambda record: record.get('package_id') or ''
        new_records, duplicates = self._dedupe_records(records, self._existing_govinfo_keys, key_func)

        if not new_records:
            summary = UpsertSummary(inserted=0, duplicates=duplicates, errors=0)
            self._record_summary(summary, 'govinfo')
            return {"inserted": 0, "duplicates": duplicates, "errors": 0}

        summary: UpsertSummary = await self._run_in_thread(self.db_adapter.bulk_upsert_govinfo, new_records)
        summary.duplicates += duplicates
        self._record_summary(summary, 'govinfo')
        return {"inserted": summary.inserted, "duplicates": summary.duplicates, "errors": summary.errors}

    async def ingest_federal_members(self, congress: Optional[int] = None, api_key: str = None) -> IngestionResult:
        """
        Ingest federal members from Congress.gov, process them in chunks (optionally using GPU/parallel workers), and persist results via the configured database adapter.
        
        Parameters:
        	congress (Optional[int]): If provided, restricts fetched members to the specified Congress number.
        	api_key (str): Optional API key used when calling the Congress.gov API.
        
        Returns:
        	IngestionResult: Aggregated outcome including number of records processed, duration, success flag, any errors, performance metrics (including `api_calls`), and data quality metrics (`duplicates_skipped`, `source`, and `completion_criteria`).
        """
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("members_ingestion")

        try:
            logger.info("Starting federal members ingestion")

            # Fetch members data
            fetch = await self._fetch_federal_members(congress, api_key)
            members_data = fetch.records

            if not members_data:
                completion = self._build_completion_criteria(
                    'members', 0, 0, {"chunks_processed": 0}
                )
                return IngestionResult(
                    records_processed=0,
                    performance_metrics={'api_calls': fetch.api_calls},
                    data_quality_metrics={'duplicates_skipped': 0, 'source': fetch.source, 'completion_criteria': completion}
                )

            summaries: List[UpsertSummary] = []
            chunk_count = 0

            if self.enable_parallel and len(members_data) > self.batch_size:
                chunks = [members_data[i:i + self.batch_size]
                          for i in range(0, len(members_data), self.batch_size)]
                chunk_count = len(chunks)
                loop = asyncio.get_event_loop()
                tasks = []

                for chunk in chunks:
                    if self.enable_gpu:
                        executor = self.process_executor or self.thread_executor
                        task = loop.run_in_executor(executor, self._gpu_process_members_chunk, chunk)
                    else:
                        task = self._process_members_chunk_async(chunk)
                    tasks.append(task)

                raw_results = await asyncio.gather(*tasks)
                for summary in raw_results:
                    if isinstance(summary, UpsertSummary):
                        summaries.append(summary)
                    else:
                        summaries.append(UpsertSummary(inserted=int(summary)))
            else:
                chunk_count = 1
                if self.enable_gpu:
                    summary = await self._run_in_thread(self._gpu_process_members_chunk, members_data)
                else:
                    summary = await self._process_members_chunk_async(members_data)
                summaries.append(summary)

            duration = time.time() - start_time
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)
            perf_metrics['api_calls'] = fetch.api_calls

            total_processed = sum(summary.inserted for summary in summaries)
            duplicates = sum(summary.duplicates for summary in summaries)
            error_count = sum(summary.errors for summary in summaries)
            data_errors = []
            if error_count:
                data_errors.append(f"member_upsert_errors={error_count}")

            completion = self._build_completion_criteria(
                'members', total_processed, duplicates, {"chunks_processed": chunk_count}
            )

            return IngestionResult(
                records_processed=total_processed,
                duration=duration,
                errors=data_errors,
                performance_metrics=perf_metrics,
                data_quality_metrics={
                    'duplicates_skipped': duplicates,
                    'source': fetch.source,
                    'completion_criteria': completion
                }
            )

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"Federal members ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _fetch_federal_members(self, congress: Optional[int] = None, api_key: str = None) -> FetchResponse:
        """
        Fetch federal member records from the Congress.gov API, mapping each API member to the engine's internal schema.
        
        Parameters:
        	congress (Optional[int]): If provided, restrict results to this Congress number.
        	api_key (str): Optional API key to include with requests.
        
        Returns:
        	FetchResponse: Contains `records` (list of mapped member dicts; only members with a `bioguide_id` are included), `api_calls` (number of HTTP requests performed), `source` ("congress.gov"), and `metadata` (includes the requested `congress`).
        """
        base_url = "https://api.congress.gov/v3/member"
        params: Dict[str, Any] = {'format': 'json', 'limit': self.batch_size}
        if congress:
            params['congress'] = congress
        if api_key:
            params['api_key'] = api_key

        api_calls = 0
        records: List[Dict[str, Any]] = []
        url = base_url
        next_params = params

        while url:
            try:
                async with self.aiohttp_session.get(url, params=next_params, timeout=self.timeout) as response:
                    api_calls += 1
                    if response.status != 200:
                        logger.warning("Members API request failed", extra={"status": response.status})
                        break

                    payload = await response.json()
                    members = payload.get('members', [])
                    for member in members:
                        mapped = self._map_member(member)
                        if mapped.get('bioguide_id'):
                            records.append(mapped)

                    pagination = payload.get('pagination', {})
                    next_link = pagination.get('next')
                    if next_link:
                        url = next_link
                        next_params = None
                    else:
                        break

                    await asyncio.sleep(0)
            except asyncio.TimeoutError:
                logger.warning("Members API request timed out")
                break
            except Exception as exc:
                logger.error("Failed to fetch members", extra={"error": str(exc)})
                break

        return FetchResponse(records=records, api_calls=api_calls, source="congress.gov", metadata={"congress": congress})

    async def _process_members_chunk_async(self, members: List[Dict[str, Any]]) -> UpsertSummary:
        """
        Process a chunk of federal member records and persist them to the configured adapter.
        
        Parameters:
            members (List[Dict[str, Any]]): List of member records in the engine's canonical schema.
        
        Returns:
            UpsertSummary: Summary of the upsert operation containing counts for inserted records, duplicates, and errors.
        
        Notes:
            Updates the engine's per-run member summary metrics.
        """
        if not members:
            return UpsertSummary()

        await self._ensure_existing_member_ids()
        summary: UpsertSummary = await self._run_in_thread(self._store_members_sync, members)
        self._record_summary(summary, 'member')
        return summary

    def _gpu_process_members_chunk(self, members: List[Dict]) -> UpsertSummary:
        """
        Process a chunk of member records, using GPU acceleration when available.
        
        Parameters:
            members (List[Dict]): Member records to process and persist; each dict should contain member fields (e.g., "full_name").
        
        Returns:
            UpsertSummary: Summary of the upsert operation containing counts for inserted records, duplicates, and errors.
        """
        if not members:
            return UpsertSummary()

        processed_members = members

        if self.enable_gpu and RAPIDS_AVAILABLE:
            try:
                df = cudf.DataFrame(members)
                if 'full_name' in df.columns:
                    df['full_name_gpu'] = df['full_name'].str.upper()
                processed_members = df.to_pandas().to_dict('records')
            except Exception as exc:
                logger.warning("GPU member processing fallback", extra={"error": str(exc)})

        summary = self._store_members_sync(processed_members)
        self._record_summary(summary, 'member')
        return summary

    async def ingest_govinfo_bills(self, collection: str = 'BILLS', api_key: str = None,
                                   start_date: Optional[str] = None, end_date: Optional[str] = None) -> IngestionResult:
        """
                                   Ingest GovInfo.gov collection items and persist them as canonical bill records.
                                   
                                   Fetches GovInfo items for the given collection and time window, processes and upserts them into the configured database adapter, and returns ingestion metrics and data-quality summaries.
                                   
                                   Parameters:
                                       collection (str): GovInfo collection name to fetch (default 'BILLS').
                                       api_key (Optional[str]): Optional API key for GovInfo requests.
                                       start_date (Optional[str]): Inclusive start date filter (ISO-like string) for fetched items.
                                       end_date (Optional[str]): Inclusive end date filter (ISO-like string) for fetched items.
                                   
                                   Returns:
                                       IngestionResult: Summary of the ingestion containing:
                                           - records_processed: number of records inserted.
                                           - duration: elapsed wall-clock time for the operation.
                                           - success: `True` when ingestion completed without unhandled exceptions (may still contain per-record errors).
                                           - errors: list of error messages encountered during ingestion.
                                           - performance_metrics: runtime metrics including API call count and resource usage.
                                           - data_quality_metrics: includes `duplicates_skipped`, `source`, and `completion_criteria` describing coverage for the requested collection and time window.
                                   """
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("govinfo_ingestion")

        try:
            logger.info(f"Starting GovInfo bills ingestion: {collection}")

            # Fetch GovInfo data
            fetch = await self._fetch_govinfo_bills(collection, api_key, start_date, end_date)
            bills_data = fetch.records

            if not bills_data:
                completion = self._build_completion_criteria(
                    'govinfo', 0, 0,
                    {"collection": collection, "time_window": bool(start_date or end_date)}
                )
                return IngestionResult(
                    records_processed=0,
                    performance_metrics={'api_calls': fetch.api_calls},
                    data_quality_metrics={'duplicates_skipped': 0, 'source': fetch.source, 'completion_criteria': completion}
                )

            if self.enable_gpu and RAPIDS_AVAILABLE:
                summary = await self._gpu_process_govinfo_bills(bills_data)
            else:
                summary = await self._cpu_process_govinfo_bills(bills_data)

            duration = time.time() - start_time
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)
            perf_metrics['api_calls'] = fetch.api_calls

            completion = self._build_completion_criteria(
                'govinfo', summary.inserted, summary.duplicates,
                {"collection": collection, "time_window": bool(start_date or end_date)}
            )

            errors = []
            if summary.errors:
                errors.append(f"govinfo_upsert_errors={summary.errors}")

            return IngestionResult(
                records_processed=summary.inserted,
                duration=duration,
                errors=errors,
                performance_metrics=perf_metrics,
                data_quality_metrics={
                    'duplicates_skipped': summary.duplicates,
                    'source': fetch.source,
                    'completion_criteria': completion
                }
            )

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"GovInfo bills ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _fetch_govinfo_bills(self, collection: str, api_key: str = None,
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> FetchResponse:
        """
                                   Fetches GovInfo collection items and maps them to internal bill records.
                                   
                                   Parameters:
                                   	collection (str): GovInfo collection identifier to query (e.g., a collection name).
                                   	api_key (Optional[str]): GovInfo API key to include in requests.
                                   	start_date (Optional[str]): ISO-like start date filter for the collection (inclusive).
                                   	end_date (Optional[str]): ISO-like end date filter for the collection (inclusive).
                                   
                                   Returns:
                                   	FetchResponse: Container with `records` (list of mapped bill dicts that include `package_id`), `api_calls` (number of HTTP requests performed), and `source` set to "govinfo.gov". Metadata includes the queried `collection`.
                                   """
        base_url = f"https://api.govinfo.gov/collections/{collection}"
        params: Dict[str, Any] = {'pageSize': self.batch_size}
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        if api_key:
            params['api_key'] = api_key

        api_calls = 0
        records: List[Dict[str, Any]] = []
        offset = 0

        while True:
            params['offset'] = offset
            try:
                async with self.aiohttp_session.get(base_url, params=params, timeout=self.timeout) as response:
                    api_calls += 1
                    if response.status != 200:
                        logger.warning("GovInfo API request failed", extra={"status": response.status, "collection": collection})
                        break

                    payload = await response.json()
                    items = payload.get('packages', [])
                    for item in items:
                        mapped = self._map_govinfo_bill(item)
                        if mapped.get('package_id'):
                            records.append(mapped)

                    if len(items) < self.batch_size:
                        break
                    offset += self.batch_size
                    await asyncio.sleep(0)
            except asyncio.TimeoutError:
                logger.warning("GovInfo API request timed out", extra={"collection": collection})
                break
            except Exception as exc:
                logger.error("Failed to fetch GovInfo data", extra={"error": str(exc), "collection": collection})
                break

        return FetchResponse(records=records, api_calls=api_calls, source="govinfo.gov", metadata={"collection": collection})

    async def _gpu_process_govinfo_bills(self, bills: List[Dict]) -> UpsertSummary:
        """
        Process and persist a list of GovInfo bill records using GPU acceleration when available; falls back to the CPU path on failure.
        
        Parameters:
            bills (List[Dict]): GovInfo bill records in the normalized internal schema to be persisted.
        
        Returns:
            UpsertSummary: Counts of `inserted`, `duplicates`, and `errors` resulting from the upsert operation.
        """
        try:
            # Convert to GPU DataFrame
            df = cudf.DataFrame(bills)

            # GPU processing
            df = self._gpu_process_bills_dataframe(df)

            # Insert to database
            cpu_data = df.to_pandas().to_dict('records')
            result = await self._insert_govinfo_batch(cpu_data)
            return UpsertSummary(
                inserted=result["inserted"],
                duplicates=result["duplicates"],
                errors=result["errors"]
            )

        except Exception as e:
            logger.error(f"GPU GovInfo processing failed: {e}")
            # Fallback to CPU
            return await self._cpu_process_govinfo_bills(bills)

    async def _cpu_process_govinfo_bills(self, bills: List[Dict]) -> UpsertSummary:
        """
        Process and persist a list of GovInfo bill records in CPU-mode batching.
        
        Parameters:
            bills (List[Dict]): GovInfo records to be inserted or upserted; each dict should match the engine's internal GovInfo schema.
        
        Returns:
            UpsertSummary: Aggregated counts across all batches: `inserted`, `duplicates`, and `errors`.
        """
        summary = UpsertSummary()
        for i in range(0, len(bills), self.batch_size):
            batch = bills[i:i + self.batch_size]
            result = await self._insert_govinfo_batch(batch)
            summary.inserted += result["inserted"]
            summary.duplicates += result["duplicates"]
            summary.errors += result["errors"]

        return summary

    async def ingest_custom_data(self, parameters: Dict[str, Any]) -> IngestionResult:
        """
        Hook for ingesting arbitrary/custom data sources according to the provided parameters.
        
        Parameters:
            parameters (dict): Configuration and metadata for the custom ingestion run. Expected keys and semantics are implementation-dependent (e.g., source identifiers, pagination options, API credentials, mapping rules, or batch settings).
        
        Returns:
            IngestionResult: Summary of the ingestion run including `records_processed`, `duration`, `success`, `errors`, `performance_metrics`, and `data_quality_metrics`.
        """
        # Implementation for custom data ingestion
        return IngestionResult(records_processed=0)


class PerformanceMonitor:
    """Performance monitoring for ingestion operations"""

    def __init__(self):
        self.monitors = {}
        self.gpu_available = GPU_AVAILABLE

    async def start_monitoring(self, monitor_id: str) -> str:
        """Start performance monitoring"""
        self.monitors[monitor_id] = {
            'start_time': time.time(),
            'start_cpu': psutil.cpu_percent(),
            'start_memory': psutil.virtual_memory().percent,
            'gpu_start': torch.cuda.memory_allocated() if self.gpu_available else 0,
            'network_start': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        }
        return monitor_id

    async def stop_monitoring(self, monitor_id: str) -> Dict[str, Any]:
        """Stop performance monitoring and return metrics"""
        if monitor_id not in self.monitors:
            return {}

        start_data = self.monitors[monitor_id]
        end_time = time.time()

        # Calculate metrics
        cpu_end = psutil.cpu_percent()
        memory_end = psutil.virtual_memory().percent
        network_end = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

        metrics = {
            'duration_seconds': end_time - start_data['start_time'],
            'cpu_usage_percent': cpu_end,
            'memory_usage_percent': memory_end,
            'memory_peak_percent': psutil.virtual_memory().percent,
            'network_io_mb': (network_end - start_data['network_start']) / (1024 * 1024),
            'gpu_available': self.gpu_available,
            'gpu_memory_used_mb': 0,
            'throughput_records_per_second': 0  # Will be set by caller
        }

        if self.gpu_available:
            gpu_end = torch.cuda.memory_allocated()
            metrics['gpu_memory_used_mb'] = (gpu_end - start_data['gpu_start']) // (1024 * 1024)
            metrics['gpu_utilization_percent'] = torch.cuda.utilization() if hasattr(torch.cuda, 'utilization') else 0

        del self.monitors[monitor_id]
        return metrics


class GPUManager:
    """GPU resource management"""

    def __init__(self):
        self.devices = list(range(GPU_COUNT)) if GPU_AVAILABLE else []
        self.memory_limits = {}

    def get_available_device(self) -> Optional[int]:
        """Get the most available GPU device"""
        if not self.devices:
            return None

        # Find device with most free memory
        best_device = None
        max_free_memory = 0

        for device_id in self.devices:
            if torch.cuda.get_device_properties(device_id).total_memory > max_free_memory:
                free_memory = torch.cuda.get_device_properties(device_id).total_memory - torch.cuda.memory_allocated(device_id)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    best_device = device_id

        return best_device

    def set_memory_limit(self, device_id: int, memory_mb: int):
        """Set memory limit for a device"""
        if device_id in self.devices:
            total_memory = torch.cuda.get_device_properties(device_id).total_memory
            limit_fraction = memory_mb / total_memory
            torch.cuda.set_per_process_memory_fraction(limit_fraction, device_id)
            self.memory_limits[device_id] = memory_mb


# Global instances
_gpu_manager = GPUManager()

def get_gpu_manager() -> GPUManager:
    """Get global GPU manager instance"""
    return _gpu_manager


async def create_ingestion_engine(enable_parallel: bool = True, max_workers: int = 4,
                                 enable_gpu: bool = False, gpu_memory_limit: int = None) -> IngestionEngine:
    """Factory function to create an ingestion engine"""
    engine = IngestionEngine(
        enable_parallel=enable_parallel,
        max_workers=max_workers,
        enable_gpu=enable_gpu,
        gpu_memory_limit=gpu_memory_limit
    )

    # Initialize async context
    await engine.__aenter__()
    return engine


if __name__ == '__main__':
    # Example usage
    async def main():
        async with await create_ingestion_engine(enable_parallel=True, enable_gpu=True) as engine:
            # Test congress data ingestion
            result = await engine.ingest_congress_data(
                api_key="your_api_key",
                start_congress=117,
                end_congress=118
            )

            print(f"Ingestion result: {result.records_processed} records processed in {result.duration:.2f}s")

    asyncio.run(main())