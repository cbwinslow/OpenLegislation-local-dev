#!/usr/bin/env python3
"""
Resume Manager for OpenLegislation Data Ingestion

Features:
- Tracks download progress with persistent state
- Prevents duplicate downloads and processing
- Resumes interrupted downloads from last checkpoint
- Handles network failures and system restarts
- Provides deduplication for data integrity
- Supports parallel processing coordination

Usage:
    from resume_manager import DownloadResumeManager

    manager = DownloadResumeManager()
    if manager.should_download(file_url):
        # Download file
        manager.mark_completed(file_url)
"""

import hashlib
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Set, Any


class DownloadResumeManager:
    """Manages download state and resume capability"""

    def __init__(self, state_file: str = ".download_state.pkl",
                 max_age_days: int = 30):
        self.state_file = Path(state_file)
        self.max_age_days = max_age_days
        self.lock = Lock()
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load persistent state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'rb') as f:
                    state = pickle.load(f)

                # Clean old entries
                self._clean_old_entries(state)
                return state

            except Exception as e:
                print(f"Warning: Could not load state file: {e}")
                return self._create_empty_state()
        else:
            return self._create_empty_state()

    def _create_empty_state(self) -> Dict[str, Any]:
        """Create empty state structure"""
        return {
            'version': '1.0',
            'created': datetime.now(),
            'collections': defaultdict(dict),
            'completed_files': set(),
            'failed_files': set(),
            'in_progress_files': set(),
            'file_hashes': {},  # For deduplication
            'last_updated': datetime.now(),
            'stats': {
                'total_downloads': 0,
                'total_failures': 0,
                'total_bytes': 0,
                'start_time': datetime.now()
            }
        }

    def _clean_old_entries(self, state: Dict[str, Any]):
        """Remove old entries to prevent state file from growing too large"""
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        # Clean completed files older than cutoff
        if 'completed_files_timestamps' in state:
            timestamps = state['completed_files_timestamps']
            to_remove = []
            for file_path, timestamp in timestamps.items():
                if timestamp < cutoff_date:
                    to_remove.append(file_path)

            for file_path in to_remove:
                state['completed_files'].discard(file_path)
                del timestamps[file_path]

    def _save_state(self):
        """Save current state to disk"""
        with self.lock:
            self.state['last_updated'] = datetime.now()

            # Convert sets to lists for JSON serialization
            state_copy = self.state.copy()
            state_copy['completed_files'] = list(self.state['completed_files'])
            state_copy['failed_files'] = list(self.state['failed_files'])
            state_copy['in_progress_files'] = list(self.state['in_progress_files'])

            try:
                with open(self.state_file, 'wb') as f:
                    pickle.dump(state_copy, f)
            except Exception as e:
                print(f"Warning: Could not save state: {e}")

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate hash of file for deduplication"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def is_duplicate(self, file_path: str) -> bool:
        """Check if file is a duplicate based on hash"""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return False

        return file_hash in self.state['file_hashes']

    def should_download(self, file_url: str, file_path: str = None) -> bool:
        """Check if a file should be downloaded"""
        with self.lock:
            # Check if already completed
            if file_url in self.state['completed_files']:
                return False

            # Check if currently in progress
            if file_url in self.state['in_progress_files']:
                return False

            # Check if previously failed (allow retry after some time)
            if file_url in self.state['failed_files']:
                # Allow retry after 1 hour
                # In a real implementation, you might want more sophisticated retry logic
                return True

            return True

    def mark_in_progress(self, file_url: str):
        """Mark a file as currently being downloaded"""
        with self.lock:
            self.state['in_progress_files'].add(file_url)
            self._save_state()

    def mark_completed(self, file_url: str, file_path: str = None, file_size: int = 0):
        """Mark a file as successfully downloaded"""
        with self.lock:
            self.state['completed_files'].add(file_url)
            self.state['in_progress_files'].discard(file_url)
            self.state['failed_files'].discard(file_url)

            # Update stats
            self.state['stats']['total_downloads'] += 1
            self.state['stats']['total_bytes'] += file_size

            # Store file hash for deduplication
            if file_path and os.path.exists(file_path):
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    self.state['file_hashes'][file_hash] = file_url

            self._save_state()

    def mark_failed(self, file_url: str, error: str = None):
        """Mark a file as failed to download"""
        with self.lock:
            self.state['in_progress_files'].discard(file_url)
            self.state['failed_files'].add(file_url)
            self.state['stats']['total_failures'] += 1

            # Store error info if provided
            if error:
                if 'errors' not in self.state:
                    self.state['errors'] = {}
                self.state['errors'][file_url] = {
                    'error': error,
                    'timestamp': datetime.now()
                }

            self._save_state()

    def get_resume_info(self) -> Dict[str, Any]:
        """Get information for resuming downloads"""
        with self.lock:
            completed = len(self.state['completed_files'])
            in_progress = len(self.state['in_progress_files'])
            failed = len(self.state['failed_files'])

            return {
                'completed_count': completed,
                'in_progress_count': in_progress,
                'failed_count': failed,
                'total_processed': completed + in_progress + failed,
                'stats': self.state['stats'],
                'last_updated': self.state.get('last_updated')
            }

    def get_failed_files(self) -> List[str]:
        """Get list of files that failed to download"""
        with self.lock:
            return list(self.state['failed_files'])

    def retry_failed_files(self):
        """Reset failed files for retry"""
        with self.lock:
            self.state['failed_files'].clear()
            self._save_state()

    def reset_state(self):
        """Reset all state (for fresh start)"""
        with self.lock:
            self.state = self._create_empty_state()
            self._save_state()

    def get_collection_progress(self, collection: str, congress: int, session: int) -> Dict[str, Any]:
        """Get progress for a specific collection"""
        key = f"{collection}_{congress}_{session}"
        return self.state['collections'].get(key, {})

    def update_collection_progress(self, collection: str, congress: int, session: int,
                                 progress: Dict[str, Any]):
        """Update progress for a collection"""
        key = f"{collection}_{congress}_{session}"
        self.state['collections'][key] = progress
        self.state['collections'][key]['last_updated'] = datetime.now()
        self._save_state()


class DeduplicationManager:
    """Handles deduplication of downloaded content"""

    def __init__(self, hash_cache_file: str = ".file_hashes.json"):
        self.hash_cache_file = Path(hash_cache_file)
        self.hash_cache = self._load_hash_cache()
        self.lock = Lock()

    def _load_hash_cache(self) -> Dict[str, str]:
        """Load hash cache from disk"""
        if self.hash_cache_file.exists():
            try:
                with open(self.hash_cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_hash_cache(self):
        """Save hash cache to disk"""
        try:
            with open(self.hash_cache_file, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save hash cache: {e}")

    def is_duplicate(self, file_path: str) -> bool:
        """Check if file content is duplicate"""
        file_hash = self._calculate_hash(file_path)
        if not file_hash:
            return False

        return file_hash in self.hash_cache

    def mark_processed(self, file_path: str, metadata: Dict[str, Any] = None):
        """Mark file as processed and store metadata"""
        with self.lock:
            file_hash = self._calculate_hash(file_path)
            if file_hash:
                self.hash_cache[file_hash] = {
                    'file_path': str(file_path),
                    'processed_at': datetime.now().isoformat(),
                    'metadata': metadata or {}
                }
                self._save_hash_cache()

    def get_duplicate_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about duplicate file"""
        file_hash = self._calculate_hash(file_path)
        if file_hash and file_hash in self.hash_cache:
            return self.hash_cache[file_hash]
        return None

    def _calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def cleanup_old_entries(self, max_age_days: int = 90):
        """Remove old entries from cache"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        to_remove = []

        for hash_val, info in self.hash_cache.items():
            processed_at = info.get('processed_at')
            if processed_at:
                try:
                    processed_date = datetime.fromisoformat(processed_at)
                    if processed_date < cutoff_date:
                        to_remove.append(hash_val)
                except Exception:
                    pass

        for hash_val in to_remove:
            del self.hash_cache[hash_val]

        if to_remove:
            self._save_hash_cache()
            print(f"Cleaned up {len(to_remove)} old hash cache entries")


class ParallelDownloadCoordinator:
    """Coordinates parallel downloads to prevent conflicts"""

    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self.active_downloads = set()
        self.completed_downloads = set()
        self.lock = Lock()

    def can_start_download(self, file_url: str) -> bool:
        """Check if a download can be started"""
        with self.lock:
            if file_url in self.active_downloads or file_url in self.completed_downloads:
                return False
            return len(self.active_downloads) < self.max_concurrent

    def start_download(self, file_url: str):
        """Mark download as started"""
        with self.lock:
            self.active_downloads.add(file_url)

    def complete_download(self, file_url: str):
        """Mark download as completed"""
        with self.lock:
            self.active_downloads.discard(file_url)
            self.completed_downloads.add(file_url)

    def fail_download(self, file_url: str):
        """Mark download as failed"""
        with self.lock:
            self.active_downloads.discard(file_url)

    def get_active_count(self) -> int:
        """Get number of active downloads"""
        with self.lock:
            return len(self.active_downloads)

    def wait_for_slot(self):
        """Wait for a download slot to become available"""
        while not self.can_start_download("dummy"):
            time.sleep(0.1)


# Global instances
resume_manager = DownloadResumeManager()
dedupe_manager = DeduplicationManager()
coordinator = ParallelDownloadCoordinator()


def check_and_download_file(file_url: str, output_path: str,
                          force: bool = False) -> bool:
    """Check if file should be downloaded and download if needed"""
    # Check with resume manager
    if not force and not resume_manager.should_download(file_url, output_path):
        print(f"Skipping already downloaded: {file_url}")
        return True

    # Check deduplication
    if os.path.exists(output_path) and dedupe_manager.is_duplicate(output_path):
        print(f"Skipping duplicate content: {file_url}")
        resume_manager.mark_completed(file_url, output_path)
        return True

    # Wait for download slot
    coordinator.wait_for_slot()
    coordinator.start_download(file_url)

    try:
        # Mark as in progress
        resume_manager.mark_in_progress(file_url)

        # Download file (simplified - in real implementation, use requests)
        print(f"Downloading: {file_url}")

        # Simulate download
        time.sleep(0.1)  # Replace with actual download

        # Check file size
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        # Mark as completed
        resume_manager.mark_completed(file_url, output_path, file_size)
        dedupe_manager.mark_processed(output_path, {'url': file_url})
        coordinator.complete_download(file_url)

        print(f"Completed: {file_url}")
        return True

    except Exception as e:
        print(f"Failed to download {file_url}: {e}")
        resume_manager.mark_failed(file_url, str(e))
        coordinator.fail_download(file_url)
        return False


def get_resume_status() -> Dict[str, Any]:
    """Get comprehensive resume status"""
    resume_info = resume_manager.get_resume_info()

    return {
        'resume_info': resume_info,
        'failed_files': resume_manager.get_failed_files(),
        'active_downloads': coordinator.get_active_count(),
        'state_file_exists': resume_manager.state_file.exists(),
        'hash_cache_exists': dedupe_manager.hash_cache_file.exists()
    }


def print_resume_status():
    """Print human-readable resume status"""
    status = get_resume_status()

    print(f"\n{'='*50}")
    print("RESUME STATUS")
    print(f"{'='*50}")

    resume_info = status['resume_info']
    print(f"Completed downloads: {resume_info['completed_count']:,}")
    print(f"In-progress downloads: {resume_info['in_progress_count']}")
    print(f"Failed downloads: {resume_info['failed_count']}")
    print(f"Total processed: {resume_info['total_processed']:,}")

    stats = resume_info['stats']
    print(f"Total bytes downloaded: {stats['total_bytes'] / (1024**3):.2f} GB")
    print(f"Success rate: {(stats['total_downloads'] / max(stats['total_downloads'] + stats['total_failures'], 1)) * 100:.1f}%")

    if status['failed_files']:
        print(f"\nFailed files ({len(status['failed_files'])}):")
        for failed_file in status['failed_files'][:5]:  # Show first 5
            print(f"  - {failed_file}")
        if len(status['failed_files']) > 5:
            print(f"  ... and {len(status['failed_files']) - 5} more")

    print(f"\nState file: {'✓' if status['state_file_exists'] else '✗'}")
    print(f"Hash cache: {'✓' if status['hash_cache_exists'] else '✗'}")
    print(f"Active downloads: {status['active_downloads']}")

    print(f"{'='*50}\n")


def cleanup_old_state(days: int = 30):
    """Clean up old state entries"""
    print(f"Cleaning up state older than {days} days...")
    resume_manager._clean_old_entries(resume_manager.state)
    dedupe_manager.cleanup_old_entries(days)
    print("Cleanup complete")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Resume Manager for Data Ingestion')
    parser.add_argument('--status', action='store_true', help='Show resume status')
    parser.add_argument('--reset', action='store_true', help='Reset all state')
    parser.add_argument('--retry-failed', action='store_true', help='Retry failed downloads')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Clean up state older than DAYS')

    args = parser.parse_args()

    if args.status:
        print_resume_status()
    elif args.reset:
        print("Resetting all download state...")
        resume_manager.reset_state()
        print("Reset complete")
    elif args.retry_failed:
        print("Retrying failed downloads...")
        resume_manager.retry_failed_files()
        print("Failed downloads marked for retry")
    elif args.cleanup:
        cleanup_old_state(args.cleanup)
    else:
        parser.print_help()