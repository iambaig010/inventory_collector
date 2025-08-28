# tests/test_ssh_connector.py
import pytest
from unittest.mock import patch, MagicMock
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from src.core.ssh_connector import SSHConnector
from src.core.device_manager import NetworkDevice

class TestSSHConnector:
    @pytest.fixture
    def connector(self):
        return SSHConnector(max_retries=3, base_delay=0.1)  # Fast for testing
        
    @pytest.fixture
    def test_device(self):
        return NetworkDevice(
            hostname='test-switch',
            ip_address='127.0.0.1',
            username='testuser',
            password='testing123',
            device_type='cisco_ios',
            port=2222
        )
        
    @patch('src.core.ssh_connector.ConnectHandler')
    def test_successful_connection(self, mock_connect, connector, test_device):
        # Mock successful connection
        mock_connection = MagicMock()
        mock_connection.send_command.return_value = "10:30:00 UTC"
        mock_connect.return_value = mock_connection
        
        result = connector.connect_with_retry(test_device)
        
        assert result == mock_connection
        mock_connect.assert_called_once()
        mock_connection.send_command.assert_called_once()
        
    @patch('src.core.ssh_connector.ConnectHandler')
    def test_timeout_retry_logic(self, mock_connect, connector, test_device):
        # First two attempts timeout, third succeeds
        mock_connection = MagicMock()
        mock_connection.send_command.return_value = "10:30:00 UTC"
        
        mock_connect.side_effect = [
            NetmikoTimeoutException("Timeout 1"),
            NetmikoTimeoutException("Timeout 2"),
            mock_connection
        ]
        
        result = connector.connect_with_retry(test_device)
        
        assert result == mock_connection
        assert mock_connect.call_count == 3
        
    @patch('src.core.ssh_connector.ConnectHandler')
    def test_authentication_failure_no_retry(self, mock_connect, connector, test_device):
        # Auth failure should not retry
        mock_connect.side_effect = NetmikoAuthenticationException("Bad auth")
        
        with pytest.raises(NetmikoAuthenticationException):
            connector.connect_with_retry(test_device)
            
        # Should only try once for auth failure
        assert mock_connect.call_count == 1

# Integration test with mock server
class TestSSHConnectorIntegration:
    def test_real_mock_connection(self, mock_cisco_server):
        """Test connection to mock SSH server"""
        host, port = mock_cisco_server
        device = NetworkDevice(
            hostname='mock-switch',
            ip_address=host,
            username='testuser',
            password='testing123',
            device_type='cisco_ios',
            port=port
        )
        
        connector = SSHConnector()
        connection = connector.connect_with_retry(device)
        
        # Test sending a command
        output = connection.send_command('show version')
        assert 'Cisco IOS' in output
        assert 'FOC1932X0K1' in output
        
        connector.disconnect(connection)