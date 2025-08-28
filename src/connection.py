import socket
import time
import threading
import logging

logger = logging.getLogger(__name__)

class MockSSHConnection:
    """Mock SSH connection for testing"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.connected = False
    
    def connect(self):
        """Simulate connection"""
        time.sleep(0.01)  # Small delay to simulate network
        self.connected = True
        return True
    
    def send_command(self, command):
        """Send command and return mock response"""
        if not self.connected:
            raise Exception("Not connected")
        
        mock_responses = {
            'show version': 'Mock device version info',
            'show interfaces': 'Mock interface info',
            'enable': 'Password:',
            'conf t': 'Entering configuration mode'
        }
        
        for cmd, response in mock_responses.items():
            if cmd in command.lower():
                return response
        
        return f"Mock response for: {command}"
    
    def close(self):
        """Close connection"""
        self.connected = False

def test_direct_connection():
    """Test direct connection functionality"""
    conn = MockSSHConnection("192.168.1.1", 22, "admin", "password")
    assert conn.connect() is True
    assert conn.connected is True
    conn.close()
    assert conn.connected is False
    return True

def test_ssh_connection():
    """Test SSH connection with authentication"""
    conn = MockSSHConnection("test-device", 22, "testuser", "testpass")
    result = conn.connect()
    assert result is True
    
    response = conn.send_command("show version")
    assert "Mock device version info" in response
    
    conn.close()
    return True

def test_interactive_shell():
    """Test interactive shell functionality"""
    conn = MockSSHConnection("test-device")
    conn.connect()
    
    # Test multiple commands
    commands = ["enable", "show version", "conf t"]
    responses = []
    
    for cmd in commands:
        response = conn.send_command(cmd)
        responses.append(response)
    
    assert len(responses) == len(commands)
    conn.close()
    return True

class MockSSHServer:
    """Mock SSH server for testing"""
    
    def __init__(self, port=2222):
        self.port = port
        self.running = False
        self.server_thread = None
    
    def start(self):
        """Start the mock SSH server"""
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(0.1)  # Give server time to start
    
    def stop(self):
        """Stop the mock SSH server"""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=1)
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            time.sleep(0.1)  # Simulate server activity
