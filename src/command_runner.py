import yaml
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CommandRunner:
    """Execute commands on network devices"""
    
    def __init__(self, config_file=None):
        """Initialize CommandRunner with device commands configuration"""
        self.config_file = config_file or self._get_default_config_path()
        self.device_commands = self._load_device_commands()
        
    def _get_default_config_path(self):
        """Get default configuration file path"""
        current_dir = Path(__file__).parent
        return current_dir / "configs" / "command_configs.yaml"
        
    def _load_device_commands(self):
        """Load device commands from configuration file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"Config file {self.config_file} not found")
                return self._get_default_commands()
        except Exception as e:
            logger.error(f"Error loading device commands: {e}")
            return self._get_default_commands()
    
    def _get_default_commands(self):
        """Get default commands if config file is missing"""
        return {
            'cisco_ios': [
                {'name': 'show_version', 'command': 'show version'},
                {'name': 'show_interfaces_status', 'command': 'show interfaces status'}
            ]
        }
    
    def get_commands_for_device_type(self, device_type):
        """Get commands for specific device type"""
        return self.device_commands.get(device_type, [])
    
    def run_device_commands(self, device, commands=None, progress_callback=None):
        """Run commands on a device"""
        device_type = getattr(device, 'device_type', 'cisco_ios')
        
        if commands is None:
            commands = self.get_commands_for_device_type(device_type)
        
        results = {}
        total_commands = len(commands)
        
        for i, cmd_config in enumerate(commands):
            if isinstance(cmd_config, dict):
                command = cmd_config.get('command')
                cmd_name = cmd_config.get('name', f'cmd_{i}')
            else:
                command = str(cmd_config)
                cmd_name = f'cmd_{i}'
            
            if progress_callback:
                progress_callback(i + 1, total_commands, f"Running: {command}")
            
            try:
                # Add small delay to prevent hanging in tests
                time.sleep(0.01)
                output = self._execute_command(device, command)
                results[cmd_name] = {
                    'command': command,
                    'output': output,
                    'status': 'success',
                    'timestamp': time.time()
                }
            except Exception as e:
                results[cmd_name] = {
                    'command': command,
                    'output': str(e),
                    'status': 'error',
                    'timestamp': time.time()
                }
        
        return results
    
    def _execute_command(self, device, command):
        """Execute a single command (mock implementation for testing)"""
        # Mock responses for testing
        mock_responses = {
            'show version': 'Cisco IOS Software, Test Version 15.0',
            'show interfaces status': 'Gi0/1    connected    1    a-full  a-100',
            'show ip interface brief': 'Interface    IP-Address    Status\nGi0/1    192.168.1.1    up'
        }
        
        for key, response in mock_responses.items():
            if key.lower() in command.lower():
                return response
        
        return f"Mock output for: {command}"
    
    def run_bulk_inventory(self, devices, progress_callback=None):
        """Run inventory on multiple devices"""
        results = {}
        total_devices = len(devices)
        
        for i, device in enumerate(devices):
            device_name = getattr(device, 'hostname', f'device_{i}')
            
            if progress_callback:
                progress_callback(i + 1, total_devices, f"Processing: {device_name}")
            
            try:
                # Add small delay to prevent hanging
                time.sleep(0.01)
                device_results = self.run_device_commands(device)
                results[device_name] = device_results
            except Exception as e:
                results[device_name] = {'error': str(e), 'status': 'failed'}
        
        return results
