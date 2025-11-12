#!/usr/bin/env python3
"""
Suture Log Monitor
Real-time monitoring of log files for errors
"""

import time
import os
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime


class LogMonitor:
    """Monitor log files in real-time for errors"""
    
    def __init__(self, callback: Callable = None):
        self.callback = callback
        self.running = False
        self.file_positions = {}
    
    def _get_file_size(self, file_path: str) -> int:
        """Get current file size"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def _read_new_lines(self, file_path: str) -> list:
        """Read only new lines from file since last check"""
        path = Path(file_path)
        
        if not path.exists():
            return []
        
        current_size = self._get_file_size(file_path)
        last_position = self.file_positions.get(file_path, 0)
        
        # File was truncated or rotated
        if current_size < last_position:
            last_position = 0
        
        new_lines = []
        
        try:
            with open(file_path, 'r', errors='ignore') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                self.file_positions[file_path] = f.tell()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return new_lines
    
    def monitor_file(self, file_path: str, analyzer, interval: int = 1):
        """
        Monitor a single file for errors
        
        Args:
            file_path: Path to log file
            analyzer: ErrorAnalyzer instance
            interval: Check interval in seconds
        """
        print(f"Monitoring: {file_path}")
        print(f"Press Ctrl+C to stop...\n")
        
        self.running = True
        
        try:
            while self.running:
                new_lines = self._read_new_lines(file_path)
                
                if new_lines:
                    # Analyze new content
                    content = ''.join(new_lines)
                    matches = analyzer.analyze_text(content)
                    
                    if matches and self.callback:
                        self.callback(matches, file_path)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            self.running = False
    
    def monitor_multiple(self, file_paths: list, analyzer, interval: int = 1):
        """
        Monitor multiple files simultaneously
        
        Args:
            file_paths: List of file paths
            analyzer: ErrorAnalyzer instance
            interval: Check interval in seconds
        """
        print(f"Monitoring {len(file_paths)} file(s):")
        for path in file_paths:
            print(f"  • {path}")
        print(f"\nPress Ctrl+C to stop...\n")
        
        self.running = True
        
        try:
            while self.running:
                for file_path in file_paths:
                    new_lines = self._read_new_lines(file_path)
                    
                    if new_lines:
                        content = ''.join(new_lines)
                        matches = analyzer.analyze_text(content)
                        
                        if matches and self.callback:
                            self.callback(matches, file_path)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            self.running = False
    
    def monitor_systemd_journal(self, analyzer, unit: Optional[str] = None, interval: int = 2):
        """
        Monitor systemd journal in real-time
        
        Args:
            analyzer: ErrorAnalyzer instance
            unit: Specific systemd unit to monitor (optional)
            interval: Check interval in seconds
        """
        import subprocess
        
        cmd = ['journalctl', '-f', '--no-pager']
        if unit:
            cmd.extend(['-u', unit])
        
        print(f"Monitoring systemd journal{f' for {unit}' if unit else ''}...")
        print("Press Ctrl+C to stop...\n")
        
        self.running = True
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                if not self.running:
                    process.terminate()
                    break
                
                matches = analyzer.analyze_text(line)
                if matches and self.callback:
                    self.callback(matches, 'systemd-journal')
                    
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            self.running = False
            process.terminate()
    
    def stop(self):
        """Stop monitoring"""
        self.running = False


class MonitorStats:
    """Track monitoring statistics"""
    
    def __init__(self):
        self.total_errors = 0
        self.errors_by_severity = {}
        self.errors_by_category = {}
        self.start_time = datetime.now()
    
    def add_error(self, match):
        """Add error to statistics"""
        self.total_errors += 1
        
        # Count by severity
        severity = match.severity
        self.errors_by_severity[severity] = \
            self.errors_by_severity.get(severity, 0) + 1
        
        # Count by category
        category = match.category
        self.errors_by_category[category] = \
            self.errors_by_category.get(category, 0) + 1
    
    def get_summary(self) -> str:
        """Get statistics summary"""
        runtime = datetime.now() - self.start_time
        
        summary = f"\n{'=' * 50}\n"
        summary += f"Monitoring Statistics\n"
        summary += f"{'=' * 50}\n"
        summary += f"Runtime: {runtime}\n"
        summary += f"Total Errors: {self.total_errors}\n"
        
        if self.errors_by_severity:
            summary += f"\nBy Severity:\n"
            for severity, count in sorted(self.errors_by_severity.items()):
                summary += f"  {severity}: {count}\n"
        
        if self.errors_by_category:
            summary += f"\nBy Category:\n"
            for category, count in sorted(self.errors_by_category.items()):
                summary += f"  {category}: {count}\n"
        
        return summary
