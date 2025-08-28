#!/usr/bin/env python3
"""
Quick fixes for common test issues
"""
import os
import yaml
import time
from pathlib import Path

def create_command_configs():
    """Create missing command configurations"""
    config_dir = Path("src/configs")
    config_dir.mkdir(exist_ok=True)
    
    command_configs = {
        'cisco_ios': [
            {
                'name': 'show_version',
                'command': 'show version',
                'description': 'Device version and hardware info'
            },
            {
                'name': 'show_interfaces_status',
                'command': 'show interfaces status',
                'description': 'Interface status information'
            },
            {
                'name': 'show_ip_interface_brief',
                'command': 'show ip interface brief',
                'description': 'IP interface summary'
            },
            {
                'name': 'show_running_config',
                'command': 'show running-config',
                'description': 'Current running configuration'
            },
            {
                'name': 'show_cdp_neighbors',
                'command': 'show cdp neighbors detail',
                'description': 'CDP neighbor information'
            }
        ],
        'cisco_nxos': [
            {
                'name': 'show_version',
                'command': 'show version',
                'description': 'Device version and hardware info'
            },
            {
                'name': 'show_interface_brief',
                'command': 'show interface brief',
                'description': 'Interface brief information'
            }
        ],
        'juniper_junos': [
            {
                'name': 'show_version',
                'command': 'show version',
                'description': 'Device version information'
            },
            {
                'name': 'show_interfaces_terse',
                'command': 'show interfaces terse',
                'description': 'Interface summary'
            }
        ]
    }
    
    config_file = config_dir / "command_configs.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(command_configs, f, default_flow_style=False)
    
    print(f"✓ Created command configurations at {config_file}")

def create_test_configs():
    """Create test configuration directory"""
    test_config_dir = Path("tests/configs")
    test_config_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock responses for testing
    mock_responses = {
        'cisco_ios': {
            'show version': '''
Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 15.0(2)SE4
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2013 by Cisco Systems, Inc.
''',
            'show interfaces status': '''
Port      Name               Status       Vlan       Duplex  Speed Type
Gi0/1                        notconnect   1            auto   auto 10/100/1000BaseTX
Gi0/2                        connected    1          a-full  a-100 10/100/1000BaseTX
''',
            'show ip interface brief': '''
Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/1        unassigned      YES unset  up                    up
GigabitEthernet0/1     192.168.1.1     YES manual up                    up
'''
        }
    }
    
    responses_file = test_config_dir / "mock_responses.yaml"
    with open(responses_file, 'w') as f:
        yaml.dump(mock_responses, f, default_flow_style=False)
    
    print(f"✓ Created test configurations at {test_config_dir}")

def fix_mock_server_timing():
    """Create a helper for mock server timing issues"""
    timing_fix_file = Path("tests/timing_helper.py")
    
    timing_helper_code = '''
import time
import socket
import threading
from contextlib import contextmanager

@contextmanager
def wait_for_server(host='127.0.0.1', port=2222, timeout=10):
    """Context manager that waits for server to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                yield True
                return
        except:
            pass
        
        time.sleep(0.1)
    
    raise TimeoutError(f"Server on {host}:{port} not ready within {timeout}s")

def ensure_server_stopped(port=2222):
    """Ensure no server is running on the given port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"Warning: Server already running on port {port}")
            time.sleep(2)  # Give it time to cleanup
    except:
        pass
'''
    
    with open(timing_fix_file, 'w') as f:
        f.write(timing_helper_code)
    
    print(f"✓ Created timing helper at {timing_fix_file}")

def create_pytest_fixtures():
    """Create improved pytest fixtures"""
    conftest_file = Path("tests/conftest.py")
    
    conftest_code = '''
import pytest
import time
import tempfile
import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

@pytest.fixture(scope="session")
def mock_ssh_server():
    """Session-scoped mock SSH server"""
    from tests.mock_ssh_server import start_mock_ssh_server
    from tests.timing_helper import wait_for_server, ensure_server_stopped
    
    port = 2222
    ensure_server_stopped(port)
    
    # Start server
    server_thread = start_mock_ssh_server(port, 'cisco_ios')
    
    # Wait for server to be ready
    with wait_for_server(port=port):
        yield port
    
    # Cleanup handled by thread

@pytest.fixture
def sample_device():
    """Sample device for testing"""
    return {
        'hostname': 'TEST-DEVICE',
        'ip_address': '127.0.0.1',
        'username': 'test',
        'password': 'test',
        'device_type': 'cisco_ios',
        'port': 2222
    }

@pytest.fixture
def sample_excel_file():
    """Create a temporary Excel file with sample devices"""
    devices = [
        {
            'hostname': 'TEST-SW01',
            'ip_address': '127.0.0.1',
            'username': 'test',
            'password': 'test',
            'device_type': 'cisco_ios',
            'port': 2222,
            'location': 'Test Lab',
            'description': 'Test Switch 1'
        }
    ]
    
    df = pd.DataFrame(devices)
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
        df.to_excel(tmp_file.name, index=False)
        yield tmp_file.name
    
    # Cleanup
    try:
        os.unlink(tmp_file.name)
    except:
        pass
'''
    
    with open(conftest_file, 'w') as f:
        f.write(conftest_code)
    
    print(f"✓ Created pytest fixtures at {conftest_file}")

def main():
    """Apply all quick fixes"""
    print("Applying quick fixes for test failures...\n")
    
    try:
        create_command_configs()
        create_test_configs() 
        fix_mock_server_timing()
        create_pytest_fixtures()
        
        print(f"\n✓ All quick fixes applied successfully!")
        print("\nNext steps:")
        print("1. Run: pytest tests/ -v -k 'not gui' --tb=short")
        print("2. If still failing, run: python debug_test_runner.py")
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
