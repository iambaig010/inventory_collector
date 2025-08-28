# tests/test_command_runner.py
import pytest
from unittest.mock import patch, MagicMock
from src.core.command_runner import CommandRunner
from src.core.device_manager import NetworkDevice

class TestCommandRunner:
    @pytest.fixture
    def runner(self):
        return CommandRunner()
        
    @pytest.fixture
    def test_device(self):
        return NetworkDevice(
            hostname='test-switch',
            ip_address='127.0.0.1',
            username='testuser',
            password='testpass',
            device_type='cisco_ios',
            port=2222
        )
        
    def test_default_configs_loaded(self, runner):
        """Test that default configs are loaded when no file exists"""
        assert 'cisco_ios' in runner.vendor_configs
        assert 'version' in runner.vendor_configs['cisco_ios']['commands']
        
    @patch('src.core.command_runner.SSHConnector')
    def test_run_device_commands_success(self, mock_ssh_class, runner, test_device):
        # Setup mocks
        mock_connection = MagicMock()
        mock_connection.send_command.return_value = "Mock command output"
        
        mock_ssh = MagicMock()
        mock_ssh.connect_with_retry.return_value = mock_connection
        mock_ssh_class.return_value = mock_ssh
        
        # Run test
        result = runner.run_device_commands(test_device)
        
        # Verify results
        assert result['device_info']['connection_status'] == 'success'
        assert result['device_info']['hostname'] == 'test-switch'
        assert 'version' in result['raw_output']
        assert len(result['errors']) == 0
        
        # Verify SSH calls
        mock_ssh.connect_with_retry.assert_called_once_with(test_device)
        mock_ssh.disconnect.assert_called_once_with(mock_connection)

# Integration test with mock server
class TestCommandRunnerIntegration:
    def test_real_command_execution(self, mock_cisco_server):
        """Test real command execution against mock server"""
        host, port = mock_cisco_server
        device = NetworkDevice(
            hostname='mock-switch',
            ip_address=host,
            username='testuser',
            password='testpass',
            device_type='cisco_ios',
            port=port
        )
        
        runner = CommandRunner()
        result = runner.run_device_commands(device)
        
        # Verify successful execution
        assert result['device_info']['connection_status'] == 'success'
        assert 'version' in result['raw_output']
        assert 'Cisco IOS' in result['raw_output']['version']
        assert len(result['errors']) == 0
        
    def test_bulk_inventory_with_progress(self, mock_cisco_server):
        """Test bulk inventory with progress callback"""
        host, port = mock_cisco_server
        devices = [
            NetworkDevice(f'switch-{i}', host, 'test', 'test', 'cisco_ios', port)
            for i in range(3)
        ]
        
        progress_calls = []
        def progress_callback(current, total, device_name):
            progress_calls.append((current, total, device_name))
            
        runner = CommandRunner()
        results = runner.run_bulk_inventory(devices, progress_callback)
        
        assert len(results) == 3
        assert len(progress_calls) == 4  # 3 devices + 1 complete
        assert progress_calls[-1] == (3, 3, "Complete")