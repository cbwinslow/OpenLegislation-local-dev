#!/usr/bin/env python3
"""
Ingestion Progress Event System for OpenLegislation

Provides progress reporting and cancellation support for long-running ingestion processes.
Includes detailed progress tracking with row numbers and completion percentages.

Features:
- Progress event callbacks for real-time monitoring
- Cancellation support with graceful shutdown
- Row number/total tracking (e.g., "Processing member 247 of 538")
- Success/failure rate reporting
- Time estimation and ETA calculations

Usage:
    from ingestion_progress import IngestionProgressEvent

    progress = IngestionProgressEvent(total_items=538)

    # Register callback
    def on_progress(event):
        print(f"{event.current_item}/{event.total_items} - {event.percentage:.1f}%")

    progress.add_callback(on_progress)

    # During processing
    progress.update(current_item=247, status="Processing member data")
    # Check for cancellation
    if progress.is_cancelled():
        break
"""

import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Any


@dataclass
class ProgressEvent:
    """Event data for progress updates"""

    current_item: int
    total_items: int
    percentage: float
    status: str
    start_time: datetime
    elapsed_time: float
    estimated_time_remaining: Optional[float]
    items_per_second: float
    successful_items: int = 0
    failed_items: int = 0
    success_rate: float = 0.0
    member_name: Optional[str] = None
    bioguide_id: Optional[str] = None
    event_type: str = "progress"  # progress, completed, cancelled, error


class IngestionProgressEvent:
    """Progress tracking and cancellation support for ingestion processes"""

    def __init__(self, total_items: int, description: str = "Processing items"):
        self.total_items = total_items
        self.description = description
        self.current_item = 0
        self.successful_items = 0
        self.failed_items = 0
        self.start_time = datetime.now()
        self._cancelled = False
        self._callbacks: List[Callable[[ProgressEvent], None]] = []
        self._lock = threading.Lock()

        # Set up signal handlers for graceful cancellation
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle cancellation signals"""
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        self.cancel()

    def add_callback(self, callback: Callable[[ProgressEvent], None]):
        """Add a callback function for progress events"""
        with self._lock:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressEvent], None]):
        """Remove a callback function"""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def cancel(self):
        """Cancel the ingestion process"""
        with self._lock:
            self._cancelled = True
            self._fire_event("cancelled", "Ingestion cancelled by user")

    def is_cancelled(self) -> bool:
        """Check if the process has been cancelled"""
        return self._cancelled

    def update(
        self,
        current_item: Optional[int] = None,
        status: str = "",
        member_name: Optional[str] = None,
        bioguide_id: Optional[str] = None,
        success: Optional[bool] = None,
    ):
        """Update progress and fire progress event

        Args:
            current_item: Current item number (1-based)
            status: Status message
            member_name: Name of current member being processed
            bioguide_id: Bioguide ID of current member
            success: True for success, False for failure, None for in-progress
        """
        if self._cancelled:
            return

        with self._lock:
            if current_item is not None:
                self.current_item = current_item

            if success is True:
                self.successful_items += 1
            elif success is False:
                self.failed_items += 1

            self._fire_event("progress", status, member_name, bioguide_id)

    def _fire_event(
        self,
        event_type: str,
        status: str,
        member_name: Optional[str] = None,
        bioguide_id: Optional[str] = None,
    ):
        """Fire progress event to all callbacks"""
        if not self._callbacks:
            return

        elapsed = (datetime.now() - self.start_time).total_seconds()
        percentage = (
            (self.current_item / self.total_items * 100) if self.total_items > 0 else 0
        )

        # Calculate items per second
        items_per_second = self.current_item / elapsed if elapsed > 0 else 0

        # Estimate time remaining
        remaining_items = self.total_items - self.current_item
        estimated_time_remaining = (
            remaining_items / items_per_second if items_per_second > 0 else None
        )

        # Calculate success rate
        total_processed = self.successful_items + self.failed_items
        success_rate = (
            (self.successful_items / total_processed * 100)
            if total_processed > 0
            else 0
        )

        event = ProgressEvent(
            current_item=self.current_item,
            total_items=self.total_items,
            percentage=percentage,
            status=status,
            start_time=self.start_time,
            elapsed_time=elapsed,
            estimated_time_remaining=estimated_time_remaining,
            items_per_second=items_per_second,
            successful_items=self.successful_items,
            failed_items=self.failed_items,
            success_rate=success_rate,
            member_name=member_name,
            bioguide_id=bioguide_id,
            event_type=event_type,
        )

        # Call all callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in progress callback: {e}")

    def complete(self, status: str = "Ingestion completed"):
        """Mark the ingestion as completed"""
        with self._lock:
            self._fire_event("completed", status)

    def get_summary(self) -> dict:
        """Get a summary of the ingestion progress"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        total_processed = self.successful_items + self.failed_items

        return {
            "total_items": self.total_items,
            "current_item": self.current_item,
            "successful": self.successful_items,
            "failed": self.failed_items,
            "pending": self.total_items - total_processed,
            "success_rate": (
                (self.successful_items / total_processed * 100)
                if total_processed > 0
                else 0
            ),
            "elapsed_time": elapsed,
            "cancelled": self._cancelled,
            "completion_percentage": (
                (self.current_item / self.total_items * 100)
                if self.total_items > 0
                else 0
            ),
        }


# Default progress callback for console output
def console_progress_callback(event: ProgressEvent):
    """Default console progress callback"""
    if event.event_type == "progress":
        eta_str = ""
        if event.estimated_time_remaining:
            eta = timedelta(seconds=int(event.estimated_time_remaining))
            eta_str = f" (ETA: {eta})"

        member_info = ""
        if event.member_name:
            member_info = f" - {event.member_name}"
        elif event.bioguide_id:
            member_info = f" - {event.bioguide_id}"

        print(
            f"[{event.current_item:3d}/{event.total_items:3d}] "
            f"{event.percentage:5.1f}% {event.status}{member_info}{eta_str}"
        )

    elif event.event_type == "completed":
        total_processed = event.successful_items + event.failed_items
        success_rate = (
            (event.successful_items / total_processed * 100)
            if total_processed > 0
            else 0
        )
        elapsed = timedelta(seconds=int(event.elapsed_time))

        print(f"\n✓ {event.status}")
        print(f"  Processed: {total_processed}/{event.total_items}")
        print(f"  Successful: {event.successful_items}")
        print(f"  Failed: {event.failed_items}")
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Total Time: {elapsed}")

    elif event.event_type == "cancelled":
        print(f"\n⚠ {event.status}")
        print(
            f"  Processed: {event.current_item}/{event.total_items} before cancellation"
        )


# Utility function to create progress tracker with console output
def create_progress_tracker(
    total_items: int, description: str = "Processing"
) -> IngestionProgressEvent:
    """Create a progress tracker with default console output"""
    progress = IngestionProgressEvent(total_items, description)
    progress.add_callback(console_progress_callback)
    return progress
