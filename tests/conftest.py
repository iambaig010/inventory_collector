import pytest
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
    for path in [str(project_root), str(src_dir), str(tests_dir)]:
        if path not in sys.path:
            sys.path.insert(0, path)
    return project_root, src_dir, tests_dir

PROJECT_ROOT, SRC_DIR, TESTS_DIR = setup_test_paths()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    setup_test_paths()
    yield

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_device_excel(temp_dir):
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
def sample_cisco_output():
    return {
        'show_version': 'Cisco IOS Software Version 15.0(2)SE4',
        'show_interfaces': 'GigabitEthernet0/1 is up, line protocol is up'
    }
