#!/usr/bin/env python3
"""
Debug script to identify test failures
"""
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def debug_command_runner():
    """Debug the command runner test failures"""
    print("=== Debugging Command Runner ===")
    
    try:
        from src.core.command_runner import CommandRunner
        from tests.mock_ssh_server import start_mock_ssh_server
        import threading
        import time
        
        print("✓ Imports successful")
        
        # Start mock server
        print("Starting mock SSH server...")
        server_thread = start_mock_ssh_server(2222, 'cisco_ios')
        time.sleep(1)  # Give server time to start
        print("✓ Mock server started")
        
        # Test device
        test_device = {
            'hostname': 'TEST-DEVICE',
            'ip_address': '127.0.0.1',
            'username': 'test',
            'password': 'test',
            'device_type': 'cisco_ios',
            'port': 2222
        }
        
        # Test command runner
        runner = CommandRunner()
        print("✓ CommandRunner created")
        
        # Try to get commands for cisco_ios
        commands = runner.device_commands.get('cisco_ios', [])
        print(f"✓ Found {len(commands)} commands for cisco_ios")
        
        if not commands:
            print("❌ No commands found for cisco_ios device type")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error in command runner debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_device_manager():
    """Debug device manager"""
    print("\n=== Debugging Device Manager ===")
    
    try:
        from src.core.device_manager import DeviceManager
        import pandas as pd
        import tempfile
        
        print("✓ Imports successful")
        
        # Create test Excel file
        test_data = [
            {
                'hostname': 'TEST-SW01',
                'ip_address': '192.168.1.1',
                'username': 'admin',
                'password': 'admin',
                'device_type': 'cisco_ios',
                'port': 22,
                'location': 'Test Lab',
                'description': 'Test Switch'
            }
        ]
        
        df = pd.DataFrame(test_data)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            df.to_excel(tmp_file.name, index=False)
            tmp_path = tmp_file.name
        
        print("✓ Test Excel file created")
        
        # Test device manager
        manager = DeviceManager()
        devices = manager.load_devices_from_excel(tmp_path)
        print(f"✓ Loaded {len(devices)} devices")
        
        # Cleanup
        os.unlink(tmp_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in device manager debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_excel_handler():
    """Debug Excel handler"""
    print("\n=== Debugging Excel Handler ===")
    
    try:
        from src.utils.excel_handler import ExcelHandler
        import tempfile
        
        print("✓ Imports successful")
        
        handler = ExcelHandler()
        print("✓ ExcelHandler created")
        
        # Test template creation
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            template_path = tmp_file.name
        
        handler.create_device_template(template_path)
        print("✓ Template created successfully")
        
        # Cleanup
        os.unlink(template_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Error in Excel handler debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def debug_mock_server():
    """Debug mock SSH server"""
    print("\n=== Debugging Mock SSH Server ===")
    
    try:
        from tests.mock_ssh_server import start_mock_ssh_server, MockSSHServer
        import threading
        import time
        import socket
        
        print("✓ Imports successful")
        
        # Test server creation
        server = MockSSHServer('cisco_ios')
        print("✓ Mock server instance created")
        
        # Test port availability
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 2223))
        sock.close()
        
        if result == 0:
            print("❌ Port 2223 already in use")
            return False
        
        print("✓ Port 2223 available")
        
        # Start server
        server_thread = start_mock_ssh_server(2223, 'cisco_ios')
        time.sleep(1)
        print("✓ Mock server started")
        
        # Test connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 2223))
        sock.close()
        
        if result == 0:
            print("✓ Can connect to mock server")
            return True
        else:
            print("❌ Cannot connect to mock server")
            return False
        
    except Exception as e:
        print(f"❌ Error in mock server debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("Starting comprehensive debug session...\n")
    
    results = {
        'command_runner': debug_command_runner(),
        'device_manager': debug_device_manager(),
        'excel_handler': debug_excel_handler(),
        'mock_server': debug_mock_server()
    }
    
    print(f"\n=== Debug Results ===")
    for component, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{component}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\nRecommended fixes:")
        if not results['command_runner']:
            print("- Check command_configs.yaml file exists and has cisco_ios commands")
        if not results['device_manager']:
            print("- Check pandas/openpyxl installation")
        if not results['excel_handler']:
            print("- Check Excel file permissions and openpyxl installation")
        if not results['mock_server']:
            print("- Check paramiko installation and port availability")

if __name__ == "__main__":
    main()