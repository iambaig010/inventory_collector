import time
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Helper class to track progress in tests (renamed to avoid pytest collision)"""

    def __init__(self):
        self.progress_calls = []
        self.completed = False

    def callback(self, current, total, message):
        """Progress callback for testing"""
        self.progress_calls.append({
            'current': current,
            'total': total,
            'message': message,
            'timestamp': time.time()
        })
        if current >= total:
            self.completed = True

class _TestProgress(ProgressTracker):
    """Alias for ProgressTracker - underscore prevents pytest collection"""
    pass

TestProgress = _TestProgress

def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """Wait for a condition to become true"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False

class TimeoutTest:
    """Context manager for tests with timeout"""
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.timer = None
        self.timed_out = False
    def __enter__(self):
        self.timer = threading.Timer(self.timeout, self._timeout_handler)
        self.timer.start()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        if self.timed_out:
            raise TimeoutError(f"Test timed out after {self.timeout} seconds")
    def _timeout_handler(self):
        self.timed_out = True

def create_test_excel_file(file_path, data=None):
    """Create a test Excel file with device data"""
    import pandas as pd
    if data is None:
        data = {
            'hostname': ['test-device-1', 'test-device-2'],
            'ip_address': ['192.168.1.10', '192.168.1.11'],
            'username': ['admin', 'admin'],
            'password': ['password', 'password'],
            'device_type': ['cisco_ios', 'cisco_ios'],
            'port': [22, 22],
            'location': ['Lab', 'Lab'],
            'description': ['Test Device 1', 'Test Device 2']
        }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return file_path

def cleanup_test_files(*file_paths):
    """Clean up test files"""
    for file_path in file_paths:
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
        except Exception as e:
            logger.warning(f"Could not remove test file {file_path}: {e}")
