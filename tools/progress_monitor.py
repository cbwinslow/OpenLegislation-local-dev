#!/usr/bin/env python3
"""
Progress Monitor and TUI for OpenLegislation Data Ingestion

Provides real-time monitoring of:
- Download progress across multiple collections
- System resource usage (CPU, memory, disk, network)
- Database ingestion statistics
- Error tracking and recovery status

Features:
- Terminal-based progress bars
- Real-time statistics updates
- Resume capability tracking
- Performance metrics
- Error reporting and alerts
"""

import curses
import json
import os
import psutil
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class ProgressStats:
    """Tracks progress statistics for data ingestion"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all statistics"""
        self.start_time = datetime.now()
        self.collections = defaultdict(dict)
        self.total_files = 0
        self.processed_files = 0
        self.failed_files = 0
        self.bytes_downloaded = 0
        self.current_speed = 0
        self.errors = []
        self.warnings = []

    def update_collection(self, collection: str, congress: int, session: int,
                         files_found: int = 0, files_downloaded: int = 0,
                         bytes_downloaded: int = 0, status: str = "pending"):
        """Update statistics for a specific collection"""
        key = f"{collection}_{congress}_{session}"
        self.collections[key].update({
            'collection': collection,
            'congress': congress,
            'session': session,
            'files_found': files_found,
            'files_downloaded': files_downloaded,
            'bytes_downloaded': bytes_downloaded,
            'status': status,
            'last_update': datetime.now()
        })

    def add_error(self, error_msg: str, collection: str = None):
        """Add an error to the tracking"""
        self.errors.append({
            'timestamp': datetime.now(),
            'message': error_msg,
            'collection': collection
        })

    def add_warning(self, warning_msg: str, collection: str = None):
        """Add a warning to the tracking"""
        self.warnings.append({
            'timestamp': datetime.now(),
            'message': warning_msg,
            'collection': collection
        })

    def get_overall_progress(self) -> Dict[str, Any]:
        """Get overall progress statistics"""
        total_found = sum(c.get('files_found', 0) for c in self.collections.values())
        total_downloaded = sum(c.get('files_downloaded', 0) for c in self.collections.values())
        total_bytes = sum(c.get('bytes_downloaded', 0) for c in self.collections.values())

        elapsed = datetime.now() - self.start_time
        elapsed_seconds = elapsed.total_seconds()

        # Calculate rates
        download_rate = total_bytes / elapsed_seconds if elapsed_seconds > 0 else 0
        file_rate = total_downloaded / elapsed_seconds if elapsed_seconds > 0 else 0

        # Estimate completion
        if total_found > 0 and total_downloaded > 0:
            progress_pct = (total_downloaded / total_found) * 100
            remaining_files = total_found - total_downloaded
            eta_seconds = remaining_files / file_rate if file_rate > 0 else 0
            eta = timedelta(seconds=int(eta_seconds))
        else:
            progress_pct = 0.0
            eta = timedelta(seconds=0)

        return {
            'progress_percent': progress_pct,
            'total_files_found': total_found,
            'total_files_downloaded': total_downloaded,
            'total_bytes_downloaded': total_bytes,
            'download_rate_bps': download_rate,
            'file_rate_fps': file_rate,
            'elapsed_time': elapsed,
            'estimated_time_remaining': eta,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class SystemMonitor:
    """Monitors system resources during ingestion"""

    def __init__(self):
        self.history = []
        self.max_history = 100

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # Network I/O (since last check)
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024**2)
            net_recv_mb = net_io.bytes_recv / (1024**2)

            stats = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_gb': memory_used_gb,
                'memory_total_gb': memory_total_gb,
                'disk_percent': disk_percent,
                'disk_used_gb': disk_used_gb,
                'disk_total_gb': disk_total_gb,
                'network_sent_mb': net_sent_mb,
                'network_recv_mb': net_recv_mb,
                'timestamp': datetime.now()
            }

            # Keep history
            self.history.append(stats)
            if len(self.history) > self.max_history:
                self.history.pop(0)

            return stats

        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now()
            }


class ProgressTUI:
    """Terminal User Interface for progress monitoring"""

    def __init__(self, stats: ProgressStats, monitor: SystemMonitor):
        self.stats = stats
        self.monitor = monitor
        self.running = False
        self.screen = None

    def start(self):
        """Start the TUI"""
        self.running = True
        curses.wrapper(self._run_tui)

    def stop(self):
        """Stop the TUI"""
        self.running = False

    def _run_tui(self, screen):
        """Main TUI loop"""
        self.screen = screen
        curses.curs_set(0)  # Hide cursor
        screen.timeout(1000)  # Refresh every second

        while self.running:
            try:
                self._draw_screen()
                key = screen.getch()

                # Handle input
                if key == ord('q') or key == ord('Q'):
                    self.running = False
                elif key == ord('r') or key == ord('R'):
                    # Reset stats
                    self.stats.reset()

            except KeyboardInterrupt:
                self.running = False

    def _draw_screen(self):
        """Draw the TUI screen"""
        if not self.screen:
            return

        self.screen.clear()

        # Get current stats
        progress = self.stats.get_overall_progress()
        system = self.monitor.get_system_stats()

        height, width = self.screen.getmaxyx()

        # Title
        title = "OpenLegislation Data Ingestion Monitor"
        self.screen.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Progress bar
        progress_pct = progress['progress_percent']
        bar_width = min(50, width - 20)
        filled = int(bar_width * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        progress_text = f"Progress: [{bar}] {progress_pct:.1f}%"
        self.screen.addstr(2, 2, progress_text)

        # Statistics
        line = 4
        self.screen.addstr(line, 2, f"Files Found: {progress['total_files_found']:,}", curses.A_DIM)
        line += 1
        self.screen.addstr(line, 2, f"Files Downloaded: {progress['total_files_downloaded']:,}", curses.A_DIM)
        line += 1
        self.screen.addstr(line, 2, f"Data Downloaded: {progress['total_bytes_downloaded'] / (1024**3):.2f} GB", curses.A_DIM)
        line += 1
        self.screen.addstr(line, 2, f"Download Speed: {progress['download_rate_bps'] / (1024**2):.2f} MB/s", curses.A_DIM)
        line += 1
        self.screen.addstr(line, 2, f"Elapsed Time: {progress['elapsed_time']}", curses.A_DIM)
        line += 1
        self.screen.addstr(line, 2, f"ETA: {progress['estimated_time_remaining']}", curses.A_DIM)

        # System stats
        line += 2
        self.screen.addstr(line, 2, "System Resources:", curses.A_BOLD)
        line += 1
        if 'error' not in system:
            self.screen.addstr(line, 2, f"CPU: {system['cpu_percent']:.1f}%", curses.A_DIM)
            line += 1
            self.screen.addstr(line, 2, f"Memory: {system['memory_used_gb']:.1f}/{system['memory_total_gb']:.1f} GB ({system['memory_percent']:.1f}%)", curses.A_DIM)
            line += 1
            self.screen.addstr(line, 2, f"Disk: {system['disk_used_gb']:.1f}/{system['disk_total_gb']:.1f} GB ({system['disk_percent']:.1f}%)", curses.A_DIM)
        else:
            self.screen.addstr(line, 2, f"System monitoring error: {system['error']}", curses.A_DIM)

        # Errors and warnings
        if self.stats.errors or self.stats.warnings:
            line += 2
            self.screen.addstr(line, 2, "Issues:", curses.A_BOLD)
            line += 1

            # Show recent errors/warnings
            issues = (self.stats.errors[-3:] + self.stats.warnings[-3:])[-5:]  # Last 5 issues
            for issue in issues:
                issue_type = "ERROR" if issue in self.stats.errors else "WARN"
                timestamp = issue['timestamp'].strftime('%H:%M:%S')
                msg = f"[{timestamp}] {issue_type}: {issue['message'][:50]}..."
                color = curses.A_RED if issue_type == "ERROR" else curses.A_YELLOW
                self.screen.addstr(line, 2, msg, color)
                line += 1

        # Help text
        help_text = "Press 'q' to quit, 'r' to reset stats"
        self.screen.addstr(height - 1, (width - len(help_text)) // 2, help_text, curses.A_DIM)

        self.screen.refresh()


class DownloadProgressTracker:
    """Tracks download progress and provides resume capability"""

    def __init__(self, progress_file: str = ".download_progress.json"):
        self.progress_file = Path(progress_file)
        self.progress = self._load_progress()

    def _load_progress(self) -> Dict[str, Any]:
        """Load existing progress from file"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'collections': {},
            'completed_files': set(),
            'last_run': None,
            'version': '1.0'
        }

    def save_progress(self):
        """Save current progress to file"""
        progress_copy = self.progress.copy()
        progress_copy['completed_files'] = list(self.progress['completed_files'])
        progress_copy['last_run'] = datetime.now().isoformat()

        with open(self.progress_file, 'w') as f:
            json.dump(progress_copy, f, indent=2, default=str)

    def is_file_completed(self, file_path: str) -> bool:
        """Check if a file has already been downloaded"""
        return file_path in self.progress['completed_files']

    def mark_file_completed(self, file_path: str):
        """Mark a file as completed"""
        self.progress['completed_files'].add(file_path)
        self.save_progress()

    def get_resume_info(self) -> Dict[str, Any]:
        """Get information for resuming downloads"""
        return {
            'completed_count': len(self.progress['completed_files']),
            'last_run': self.progress.get('last_run'),
            'collections_status': self.progress.get('collections', {})
        }

    def reset_progress(self):
        """Reset all progress (for fresh start)"""
        self.progress = {
            'collections': {},
            'completed_files': set(),
            'last_run': None,
            'version': '1.0'
        }
        self.save_progress()


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """Create a text-based progress bar"""
    if total == 0:
        return "░" * width

    progress = min(current / total, 1.0)
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_time_delta(td: timedelta) -> str:
    """Format timedelta into human-readable format"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


# Global instances for easy access
stats = ProgressStats()
monitor = SystemMonitor()
tracker = DownloadProgressTracker()


def update_progress(collection: str, congress: int, session: int,
                   files_found: int = 0, files_downloaded: int = 0,
                   bytes_downloaded: int = 0, status: str = "in_progress"):
    """Update progress for a collection"""
    stats.update_collection(collection, congress, session,
                          files_found, files_downloaded,
                          bytes_downloaded, status)


def log_error(message: str, collection: str = None):
    """Log an error"""
    stats.add_error(message, collection)


def log_warning(message: str, collection: str = None):
    """Log a warning"""
    stats.add_warning(message, collection)


def print_progress_summary():
    """Print a summary of current progress"""
    progress = stats.get_overall_progress()

    print(f"\n{'='*60}")
    print("DOWNLOAD PROGRESS SUMMARY")
    print(f"{'='*60}")
    print(f"Progress: {progress['progress_percent']:.1f}%")
    print(f"Files: {progress['total_files_downloaded']:,} / {progress['total_files_found']:,}")
    print(f"Data: {format_bytes(progress['total_bytes_downloaded'])}")
    print(f"Speed: {progress['download_rate_bps'] / (1024**2):.2f} MB/s")
    print(f"Elapsed: {format_time_delta(progress['elapsed_time'])}")
    print(f"ETA: {format_time_delta(progress['estimated_time_remaining'])}")

    if stats.errors:
        print(f"Errors: {len(stats.errors)}")
    if stats.warnings:
        print(f"Warnings: {len(stats.warnings)}")

    print(f"{'='*60}\n")


if __name__ == '__main__':
    # Example usage
    print("Progress Monitor Demo")

    # Simulate some progress
    for i in range(10):
        update_progress("BILLS", 119, 1,
                       files_found=1000,
                       files_downloaded=i*100,
                       bytes_downloaded=i*100*1024*1024)
        time.sleep(0.5)
        print_progress_summary()

    print("Demo complete. Use ProgressTUI class for full TUI experience.")