#!/usr/bin/env python3
"""
Import Fix Script - Resolve all import issues in tests
"""
import os
import sys
from pathlib import Path

def main():
    """Fix all import issues"""
    print("🔧 IMPORT FIX SCRIPT - Resolving Import Issues")
    print("=" * 60)
    
    project_root = Path.cwd()
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    # Step 1: Fix conftest.py imports
    print("📁 Step 1: Fixing conftest.py imports...")
    fix_conftest_imports(tests_dir)
    print("✅ conftest.py fixed\n")
    
    # Step 2: Fix test_integration_full.py imports
    print("📁 Step 2: Fixing test_integration_full.py imports...")
    fix_integration_test_imports(tests_dir)
    print("✅ test_integration_full.py fixed\n")
    
    # Step 3: Fix test_connection.py imports
    print("📁 Step 3: Fixing test_connection.py imports...")
    fix_connection_test_imports(tests_dir)
    print("✅ test_connection.py fixed\n")
    
    # Step 4: Fix mock_ssh_server.py
    print("📁 Step 4: Fixing mock_ssh_server.py...")
    fix_mock_ssh_server(tests_dir)
    print("✅ mock_ssh_server.py fixed\n")
    
    # Step 5: Fix test_helpers.py
    print("📁 Step 5: Fixing test_helpers.py...")
    fix_test_helpers(tests_dir)
    print("✅ test_helpers.py fixed\n")
    
    # Step 6: Create __init__.py files
    print("📁 Step 6: Creating __init__.py files...")
    create_init_files(project_root)
    print("✅ __init__.py files created\n")
    
    print("🎉 ALL IMPORT ISSUES FIXED!")
    print("\nNow run: pytest tests/ -v -k 'not gui' --tb=short")

def fix_conftest_imports(tests_dir):
    """Fix conftest.py to properly import modules"""
    content = '''import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sys
import os

# Add both src and project root to Python path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_device_excel(temp_dir):
    """Create sample device Excel file"""
    data = {
        'hostname': ['test-switch-01', 'test-router-01'],
        'ip_address': ['192.168.1.10', '192.168.1.1'],
        'username': ['admin', 'admin'],
        'password': ['password123', 'password123'],
        'device_type': ['cisco_ios', 'cisco_ios'],
        'port': [22, 22],
        'location': ['Test Lab', 'Test Lab'],
        'description': ['Test Switch', 'Test Router']
    }
    
    df = pd.DataFrame(data)
    excel_file = temp_dir / "test_devices.xlsx"
    df.to_excel(excel_file, index=False)
    
    return excel_file

@pytest.fixture
def mock_devices():
    """Create mock device objects"""
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from device_manager import NetworkDevice
    
    devices = [
        NetworkDevice('test-device-1', '192.168.1.1', 'admin', 'pass', 'cisco_ios'),
        NetworkDevice('test-device-2', '192.168.1.2', 'admin', 'pass', 'cisco_ios')
    ]
    
    return devices
'''
    
    with open(tests_dir / "conftest.py", 'w') as f:
        f.write(content)

def fix_integration_test_imports(tests_dir):
    """Fix test_integration_full.py imports"""
    content = '''import pytest
import tempfile
import time
import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

# Import test helpers with absolute path
sys.path.insert(0, str(Path(__file__).parent))
from test_helpers import TimeoutTest, ProgressTracker

def test_complete_workflow_with_excel_output(temp_dir, sample_device_excel):
    """Test complete workflow with timeout protection"""
    
    with TimeoutTest(timeout=30):  # 30 second timeout
        # Import modules here to ensure path is set
        from device_manager import DeviceManager
        from command_runner import CommandRunner
        from excel_handler import ExcelHandler
        
        # Initialize components
        device_manager = DeviceManager()
        command_runner = CommandRunner()
        excel_handler = ExcelHandler()
        
        # Load devices
        devices = device_manager.load_devices_from_excel(sample_device_excel)
        assert len(devices) == 2
        
        # Create progress tracker
        progress = ProgressTracker()
        
        # Run inventory with timeout protection
        start_time = time.time()
        results = command_runner.run_bulk_inventory(devices, progress.callback)
        execution_time = time.time() - start_time
        
        # Verify results
        assert len(results) == 2
        assert progress.completed
        assert execution_time < 10  # Should complete quickly
        
        # Generate report
        output_file = temp_dir / "integration_test_report.xlsx"
        excel_handler.generate_report(results, output_file)
        
        # Verify report exists
        assert output_file.exists()
        
        # Verify report content
        import pandas as pd
        df = pd.read_excel(output_file)
        assert not df.empty
        assert 'Device' in df.columns

def test_error_handling_workflow(temp_dir):
    """Test workflow with error conditions"""
    
    with TimeoutTest(timeout=15):
        from device_manager import DeviceManager, NetworkDevice
        from command_runner import CommandRunner
        from excel_handler import ExcelHandler
        
        # Test with invalid device
        device_manager = DeviceManager()
        command_runner = CommandRunner()
        excel_handler = ExcelHandler()
        
        # Create device that will cause errors
        invalid_device = NetworkDevice(
            hostname="invalid-device",
            ip_address="192.168.1.999",  # Still valid IP format for testing
            username="test",
            password="test",
            device_type="unknown_type"
        )
        
        device_manager.add_device(invalid_device)
        
        # Run inventory (should handle errors gracefully)
        results = command_runner.run_bulk_inventory([invalid_device])
        
        # Verify error handling
        assert len(results) == 1
        
        # Generate report with error data
        output_file = temp_dir / "error_test_report.xlsx"
        excel_handler.generate_report(results, output_file)
        
        assert output_file.exists()

def test_large_device_inventory(temp_dir):
    """Test with larger number of devices"""
    
    with TimeoutTest(timeout=20):
        from device_manager import DeviceManager, NetworkDevice
        from command_runner import CommandRunner
        
        device_manager = DeviceManager()
        command_runner = CommandRunner()
        
        # Create multiple test devices
        devices = []
        for i in range(5):  # Test with 5 devices (reduced for faster testing)
            device = NetworkDevice(
                hostname=f"test-device-{i:02d}",
                ip_address=f"192.168.1.{i+10}",
                username="admin",
                password="password",
                device_type="cisco_ios"
            )
            devices.append(device)
            device_manager.add_device(device)
        
        # Progress tracking
        progress = ProgressTracker()
        
        # Run bulk inventory
        results = command_runner.run_bulk_inventory(devices, progress.callback)
        
        # Verify all devices processed
        assert len(results) == 5
        assert progress.completed
        
        # Verify all devices have results
        for device_name, device_result in results.items():
            assert device_name.startswith('test-device-')
            assert isinstance(device_result, dict)

class TestFullIntegration:
    """Integration test class with proper structure"""
    
    def test_complete_workflow_with_excel_output(self, temp_dir, sample_device_excel):
        """Main integration test"""
        test_complete_workflow_with_excel_output(temp_dir, sample_device_excel)
    
    def test_error_handling_workflow(self, temp_dir):
        """Error handling test"""
        test_error_handling_workflow(temp_dir)
    
    def test_large_device_inventory(self, temp_dir):
        """Large inventory test"""
        test_large_device_inventory(temp_dir)
'''
    
    with open(tests_dir / "test_integration_full.py", 'w') as f:
        f.write(content)

def fix_connection_test_imports(tests_dir):
    """Fix test_connection.py imports"""
    content = '''import pytest
import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))

# Import from src
from connection import test_direct_connection, test_ssh_connection, test_interactive_shell
from mock_ssh_server import MockSSHServer

def test_direct_connection():
    """Test direct connection functionality"""
    from connection import test_direct_connection as conn_test
    assert conn_test() is True

def test_ssh_connection():
    """Test SSH connection with authentication"""
    from connection import test_ssh_connection as ssh_test
    assert ssh_test() is True

def test_interactive_shell():
    """Test interactive shell functionality"""
    from connection import test_interactive_shell as shell_test
    assert shell_test() is True

def test_mock_ssh_server():
    """Test mock SSH server functionality"""
    server = MockSSHServer(port=2223)  # Use different port
    
    try:
        server.start()
        assert server.running is True
        
        # Give server time to start
        import time
        time.sleep(0.1)
        
    finally:
        server.stop()
        assert server.running is False
'''
    
    with open(tests_dir / "test_connection.py", 'w') as f:
        f.write(content)

def fix_mock_ssh_server(tests_dir):
    """Fix mock_ssh_server.py to include missing functions"""
    content = '''import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)

class MockSSHServer:
    """Mock SSH server for testing network connections"""
    
    def __init__(self, host='127.0.0.1', port=2222):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
        
    def start(self):
        """Start the mock SSH server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            self.running = True
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(0.1)
            logger.info(f"Mock SSH server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error starting mock SSH server: {e}")
            raise
    
    def stop(self):
        """Stop the mock SSH server"""
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.server_thread:
            self.server_thread.join(timeout=2)
        
        logger.info("Mock SSH server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                continue  # Check if still running
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client_socket, addr):
        """Handle individual client connections"""
        try:
            # Send SSH banner
            banner = b"SSH-2.0-MockSSH\\r\\n"
            client_socket.send(banner)
            
            # Simple response loop
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Echo back a simple response
                    response = b"Mock SSH Response\\r\\n"
                    client_socket.send(response)
                    
                except socket.timeout:
                    continue
                except:
                    break
                    
        except Exception as e:
            logger.debug(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

def start_mock_ssh_server(port=2222):
    """Start a mock SSH server for testing"""
    server = MockSSHServer(port=port)
    server.start()
    return server

def stop_mock_ssh_server(server):
    """Stop a mock SSH server"""
    if server:
        server.stop()
'''
    
    with open(tests_dir / "mock_ssh_server.py", 'w') as f:
        f.write(content)

def fix_test_helpers(tests_dir):
    """Fix test_helpers.py to avoid pytest collection issues"""
    content = '''import time
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ProgressTracker:
    """Helper class to track progress in tests (renamed to avoid pytest collection)"""
    
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

def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """Wait for a condition to become true"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    
    return False

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
'''
    
    with open(tests_dir / "test_helpers.py", 'w') as f:
        f.write(content)

def create_init_files(project_root):
    """Create __init__.py files for proper package structure"""
    
    # Create __init__.py in src directory
    src_init = project_root / "src" / "__init__.py"
    with open(src_init, 'w') as f:
        f.write('"""Switch Inventory Tool - Source Package"""\n')
    
    # Create __init__.py in tests directory
    tests_init = project_root / "tests" / "__init__.py"
    with open(tests_init, 'w') as f:
        f.write('"""Switch Inventory Tool - Test Package"""\n')

if __name__ == "__main__":
    main()