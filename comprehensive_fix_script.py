#!/usr/bin/env python3
"""
Comprehensive Fix Script - Solve ALL import and test issues
"""
import os
import sys
from pathlib import Path

def main():
    """Apply comprehensive fixes"""
    print("🔧 COMPREHENSIVE FIX - Solving All Issues")
    print("=" * 50)
    
    project_root = Path.cwd()
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    # Step 1: Fix Python path issues
    print("1. Fixing Python path configuration...")
    fix_python_path_issues(project_root)
    print("   ✅ Python path fixed\n")
    
    # Step 2: Fix test imports with absolute imports
    print("2. Fixing test import issues...")
    fix_test_imports(tests_dir, src_dir)
    print("   ✅ Test imports fixed\n")
    
    # Step 3: Create setup.py for proper package structure
    print("3. Creating package structure...")
    create_package_structure(project_root)
    print("   ✅ Package structure created\n")
    
    # Step 4: Fix IDE path resolution
    print("4. Configuring IDE path resolution...")
    configure_ide_paths(project_root)
    print("   ✅ IDE configuration updated\n")
    
    print("🎉 ALL FIXES APPLIED!")
    print("\nNext steps:")
    print("1. Restart your IDE/editor")
    print("2. Run: python -m pytest tests/ -v -k 'not gui' --tb=short")
    print("3. For development, run: pip install -e .")

def fix_python_path_issues(project_root):
    """Fix Python path configuration issues"""
    
    # Create __init__.py files
    init_files = [
        project_root / "__init__.py",
        project_root / "src" / "__init__.py", 
        project_root / "tests" / "__init__.py"
    ]
    
    for init_file in init_files:
        init_file.parent.mkdir(exist_ok=True)
        with open(init_file, 'w') as f:
            f.write('# Package init file\n')
    
    # Create .env file for environment variables
    env_content = f"""# Project environment configuration
PYTHONPATH={project_root}/src:{project_root}:$PYTHONPATH
PROJECT_ROOT={project_root}
"""
    
    with open(project_root / ".env", 'w') as f:
        f.write(env_content)

def fix_test_imports(tests_dir, src_dir):
    """Fix all test import issues with proper path management"""
    
    # Fix conftest.py with better path handling
    conftest_content = '''import pytest
import tempfile
import pandas as pd
from pathlib import Path
import sys
import os

# Configure Python path for testing
def setup_test_paths():
    """Setup proper Python paths for testing"""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    # Add paths in correct order
    paths_to_add = [
        str(project_root),
        str(src_dir), 
        str(tests_dir)
    ]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return project_root, src_dir, tests_dir

# Setup paths immediately
PROJECT_ROOT, SRC_DIR, TESTS_DIR = setup_test_paths()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment automatically"""
    setup_test_paths()
    yield
    # Cleanup if needed

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
    # Import with proper path
    from device_manager import NetworkDevice
    
    devices = [
        NetworkDevice('test-device-1', '192.168.1.1', 'admin', 'pass', 'cisco_ios'),
        NetworkDevice('test-device-2', '192.168.1.2', 'admin', 'pass', 'cisco_ios')
    ]
    
    return devices
'''
    
    with open(tests_dir / "conftest.py", 'w') as f:
        f.write(conftest_content)
    
    # Fix test_connection.py with proper imports
    test_connection_content = '''"""Test connection functionality"""
import pytest
import sys
from pathlib import Path

# Setup paths at module level
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
src_dir = project_root / "src"
tests_dir = project_root / "tests"

# Add paths
for path in [str(project_root), str(src_dir), str(tests_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Now import modules
try:
    from connection import test_direct_connection, test_ssh_connection, test_interactive_shell
    from mock_ssh_server import MockSSHServer
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Python path: {sys.path}")
    raise

class TestConnectionFunctionality:
    """Test connection functions"""
    
    def test_direct_connection_function(self):
        """Test direct connection functionality"""
        result = test_direct_connection()
        assert result is True

    def test_ssh_connection_function(self):
        """Test SSH connection with authentication"""
        result = test_ssh_connection()
        assert result is True

    def test_interactive_shell_function(self):
        """Test interactive shell functionality"""
        result = test_interactive_shell()
        assert result is True

class TestMockSSHServer:
    """Test mock SSH server functionality"""
    
    def test_mock_ssh_server_lifecycle(self):
        """Test mock SSH server start/stop"""
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
    
    def test_mock_ssh_server_multiple_instances(self):
        """Test multiple server instances"""
        servers = []
        
        try:
            # Create multiple servers on different ports
            for port in [2224, 2225]:
                server = MockSSHServer(port=port)
                server.start()
                servers.append(server)
                assert server.running is True
        
        finally:
            # Clean up all servers
            for server in servers:
                server.stop()
                assert server.running is False
'''
    
    with open(tests_dir / "test_connection.py", 'w') as f:
        f.write(test_connection_content)
    
    # Fix integration test with better error handling
    integration_test_content = '''"""Integration tests with proper error handling"""
import pytest
import tempfile
import time
import sys
from pathlib import Path

# Setup paths
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
src_dir = project_root / "src"
tests_dir = project_root / "tests"

for path in [str(project_root), str(src_dir), str(tests_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import test helpers
from test_helpers import TimeoutTest, TestProgress

class TestIntegrationWorkflows:
    """Integration test workflows"""
    
    def test_complete_workflow_with_timeout(self, temp_dir, sample_device_excel):
        """Test complete workflow with timeout protection"""
        
        with TimeoutTest(timeout=30):
            # Import here to ensure paths are set
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
            progress = TestProgress()
            
            # Run inventory with timeout protection
            start_time = time.time()
            results = command_runner.run_bulk_inventory(devices, progress.callback)
            execution_time = time.time() - start_time
            
            # Verify results
            assert len(results) == 2
            assert progress.completed
            assert execution_time < 5  # Should complete quickly
            
            # Generate report
            output_file = temp_dir / "integration_test_report.xlsx"
            excel_handler.generate_report(results, output_file)
            
            # Verify report exists and has content
            assert output_file.exists()
            
            import pandas as pd
            df = pd.read_excel(output_file)
            assert not df.empty
            assert 'Device' in df.columns

    def test_error_handling_workflow(self, temp_dir):
        """Test workflow with error conditions"""
        
        with TimeoutTest(timeout=15):
            from device_manager import DeviceManager, NetworkDevice
            from command_runner import CommandRunner
            from excel_handler import ExcelHandler
            
            # Initialize components
            device_manager = DeviceManager()
            command_runner = CommandRunner()
            excel_handler = ExcelHandler()
            
            # Create device that will have connection issues
            test_device = NetworkDevice(
                hostname="unreachable-device",
                ip_address="192.168.1.999",  # Valid format but unreachable
                username="test",
                password="test",
                device_type="cisco_ios"
            )
            
            device_manager.add_device(test_device)
            
            # Run inventory (should handle errors gracefully)
            results = command_runner.run_bulk_inventory([test_device])
            
            # Verify error handling
            assert len(results) == 1
            
            # Generate report with error data
            output_file = temp_dir / "error_test_report.xlsx"
            excel_handler.generate_report(results, output_file)
            
            assert output_file.exists()

    def test_bulk_device_processing(self, temp_dir):
        """Test processing multiple devices efficiently"""
        
        with TimeoutTest(timeout=20):
            from device_manager import DeviceManager, NetworkDevice
            from command_runner import CommandRunner
            
            device_manager = DeviceManager()
            command_runner = CommandRunner()
            
            # Create test devices
            devices = []
            for i in range(5):  # Reduced number for faster testing
                device = NetworkDevice(
                    hostname=f"bulk-test-device-{i:02d}",
                    ip_address=f"192.168.1.{i+100}",
                    username="admin",
                    password="password",
                    device_type="cisco_ios"
                )
                devices.append(device)
                device_manager.add_device(device)
            
            # Progress tracking
            progress = TestProgress()
            
            # Run bulk inventory
            start_time = time.time()
            results = command_runner.run_bulk_inventory(devices, progress.callback)
            execution_time = time.time() - start_time
            
            # Verify results
            assert len(results) == 5
            assert progress.completed
            assert execution_time < 10  # Should be reasonably fast
            
            # Verify all devices have results
            for device_name, device_result in results.items():
                assert device_name.startswith('bulk-test-device-')
                assert isinstance(device_result, dict)
'''
    
    with open(tests_dir / "test_integration_full.py", 'w') as f:
        f.write(integration_test_content)

def create_package_structure(project_root):
    """Create proper package structure for the project"""
    
    # Create setup.py for proper package installation
    setup_content = '''from setuptools import setup, find_packages

setup(
    name="switch-inventory-tool",
    version="0.1.0",
    description="Network Switch Inventory Management Tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=1.3.0",
        "openpyxl>=3.0.7",
        "PyYAML>=5.4.0",
        "pytest>=6.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "switch-inventory=main:main",
        ],
    },
)
'''
    
    with open(project_root / "setup.py", 'w') as f:
        f.write(setup_content)
    
    # Create pyproject.toml for modern Python packaging
    pyproject_content = '''[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "switch-inventory-tool"
version = "0.1.0"
description = "Network Switch Inventory Management Tool"
requires-python = ">=3.8"
dependencies = [
    "pandas>=1.3.0",
    "openpyxl>=3.0.7", 
    "PyYAML>=5.4.0",
    "pytest>=6.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_paths = ["src", "."]
addopts = "-v --tb=short"

[tool.setuptools.packages.find]
where = ["src"]
'''
    
    with open(project_root / "pyproject.toml", 'w') as f:
        f.write(pyproject_content)

def configure_ide_paths(project_root):
    """Configure IDE path resolution"""
    
    # Create .vscode settings for VS Code
    vscode_dir = project_root / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    vscode_settings = {
        "python.defaultInterpreterPath": "./venv/bin/python",
        "python.analysis.extraPaths": [
            "./src",
            "./tests"
        ],
        "python.envFile": "${workspaceFolder}/.env",
        "python.testing.pytestEnabled": True,
        "python.testing.pytestArgs": [
            "tests",
            "--tb=short",
            "-v"
        ],
        "python.testing.cwd": "${workspaceFolder}",
        "files.associations": {
            "*.py": "python"
        }
    }
    
    import json
    with open(vscode_dir / "settings.json", 'w') as f:
        json.dump(vscode_settings, f, indent=4)
    
    # Create .editorconfig for consistent formatting
    editorconfig_content = '''root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{yml,yaml}]
indent_style = space
indent_size = 2
'''
    
    with open(project_root / ".editorconfig", 'w') as f:
        f.write(editorconfig_content)
    
    # Create pytest.ini for consistent test configuration
    pytest_ini_content = '''[tool:pytest]
testpaths = tests
python_paths = src .
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
'''
    
    with open(project_root / "pytest.ini", 'w') as f:
        f.write(pytest_ini_content)

if __name__ == "__main__":
    main()