#!/usr/bin/env python3
"""
Enhanced Command Runner with proper config handling
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import wraps
import time

# Try to import backoff, create fallback if not available
try:
    import backoff
    def retry_with_backoff(retries=3):
        return backoff.on_exception(backoff.expo, Exception, max_tries=retries)
except ImportError:
    # Fallback decorator if backoff is not installed
    def retry_with_backoff(retries=3):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < retries - 1:
                            time.sleep(2 ** attempt)  # Simple exponential backoff
                if last_exception:
                    raise last_exception
            return wrapper
        return decorator

from .ssh_connector import SSHConnector
from .device_manager import NetworkDevice

@dataclass
class DeviceCommand:
    """Structured command definition"""
    name: str
    command: str
    description: str
    timeout: int = 30
    parser_hints: Optional[Dict[str, Any]] = None

class CommandRunner:
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.ssh_connector = SSHConnector()
        self.config_path = config_path or self._get_default_config_path()
        self.vendor_configs = self.load_vendor_configs(self.config_path)
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        possible_paths = [
            Path(__file__).parent.parent / 'configs' / 'command_configs.yaml',
            Path(__file__).parent / 'configs' / 'command_configs.yaml',
            Path('src/configs/command_configs.yaml'),
            Path('configs/command_configs.yaml'),
        ]
        
        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Using config file: {path}")
                return str(path)
        
        # Return a default path even if file doesn't exist
        default_path = Path(__file__).parent.parent / 'configs' / 'command_configs.yaml'
        self.logger.warning(f"Config file not found, will create: {default_path}")
        return str(default_path)
        
    def load_vendor_configs(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load vendor configurations from YAML file"""
        if not config_path:
            self.logger.warning("No config path provided, using defaults")
            return self.get_default_configs()
            
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.warning(f"Config file not found: {config_path}, creating defaults")
                self._create_default_yaml_file(config_file)
                return self.get_default_configs()
                
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
                
            if not config:
                self.logger.warning("Empty config file, using defaults")
                return self.get_default_configs()
                
            # Handle both old and new YAML structures
            if 'vendors' in config:
                return config['vendors']
            else:
                # Convert YAML list format to command dict format
                converted_config = {}
                for device_type, commands in config.items():
                    if isinstance(commands, list):
                        # Convert list of command dicts to simple command dict
                        cmd_dict = {}
                        for cmd in commands:
                            if isinstance(cmd, dict) and 'name' in cmd and 'command' in cmd:
                                cmd_dict[cmd['name']] = cmd['command']
                        converted_config[device_type] = {
                            'commands': cmd_dict,
                            'timeout': 30,
                            'delay_factor': 1
                        }
                return converted_config
                
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self.get_default_configs()
    
    def _create_default_yaml_file(self, config_path: Path):
        """Create default YAML config file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_yaml = {
            'cisco_ios': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_ip_interface_brief', 'command': 'show ip interface brief', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_interfaces_status', 'command': 'show interfaces status', 'description': 'Interface status', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45}
            ],
            'cisco_xe': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_ip_interface_brief', 'command': 'show ip interface brief', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_interfaces_status', 'command': 'show interfaces status', 'description': 'Interface status', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45},
                {'name': 'show_platform', 'command': 'show platform', 'description': 'Platform info', 'timeout': 30}
            ]
        }
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_yaml, f, default_flow_style=False, indent=2)
            self.logger.info(f"Created default config file: {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to create config file: {e}")
            
    def get_default_configs(self) -> Dict[str, Any]:
        """Default vendor configurations"""
        return {
            'cisco_ios': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show ip interface brief',
                    'inventory': 'show inventory',
                    'status': 'show interfaces status'
                },
                'timeout': 30,
                'delay_factor': 1
            },
            'cisco_xe': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show ip interface brief',
                    'inventory': 'show inventory',
                    'platform': 'show platform',
                    'status': 'show interfaces status'
                },
                'timeout': 30,
                'delay_factor': 1
            }
        }
        
    def get_commands_for_device(self, device_type: str) -> List[DeviceCommand]:
        """Get commands for a specific device type"""
        vendor_config = self.vendor_configs.get(device_type, {})
        commands = vendor_config.get('commands', {})
        
        if not commands:
            self.logger.warning(f"No commands found for device type: {device_type}")
            return []
        
        # Convert dict commands to DeviceCommand objects
        device_commands = []
        for cmd_name, cmd_string in commands.items():
            command = DeviceCommand(
                name=cmd_name,
                command=cmd_string,
                description=f"Execute {cmd_string}",
                timeout=vendor_config.get('timeout', 30)
            )
            device_commands.append(command)
        
        return device_commands
    
    def get_supported_device_types(self) -> List[str]:
        """Get list of supported device types"""
        return list(self.vendor_configs.keys())
    
    def validate_device_type(self, device_type: str) -> bool:
        """Check if device type is supported"""
        return device_type in self.vendor_configs
        
    @retry_with_backoff(retries=3)
    def run_device_commands(self, device: NetworkDevice) -> Dict[str, Any]:
        """Execute commands with retry mechanism"""
        result = {
            'device_info': {
                'hostname': device.hostname,
                'ip_address': device.ip_address,
                'device_type': device.device_type,
                'connection_status': 'failed',
                'timestamp': None
            },
            'raw_output': {},
            'errors': []
        }
        
        connection = None
        try:
            # Establish connection
            self.logger.info(f"Processing device: {device.hostname} ({device.ip_address})")
            connection = self.ssh_connector.connect_with_retry(device)
            result['device_info']['connection_status'] = 'connected'
            
            # Get vendor-specific commands
            vendor_config = self.vendor_configs.get(device.device_type, {})
            commands = vendor_config.get('commands', {})
            
            if not commands:
                raise ValueError(f"No commands defined for device type: {device.device_type}")
            
            # Execute each command
            for command_name, command in commands.items():
                try:
                    self.logger.info(f"Executing command '{command}' on {device.hostname}")
                    output = self.execute_command(connection, command, vendor_config)
                    result['raw_output'][command_name] = output
                    self.logger.debug(f"Command '{command}' completed successfully")
                    
                except Exception as e:
                    error_msg = f"Command '{command}' failed: {str(e)}"
                    self.logger.warning(f"{device.hostname}: {error_msg}")
                    result['errors'].append(error_msg)
                    result['raw_output'][command_name] = f"ERROR: {str(e)}"
            
            result['device_info']['connection_status'] = 'success'
            
        except Exception as e:
            error_msg = f"Failed to process device: {str(e)}"
            self.logger.error(f"{device.hostname}: {error_msg}")
            result['device_info']['connection_status'] = 'failed'
            result['errors'].append(error_msg)
            
        finally:
            if connection:
                self.ssh_connector.disconnect(connection)
                
        return result
    
    def execute_command(self, connection, command: str, vendor_config: Dict[str, Any]) -> str:
        """Execute single command with vendor-specific settings"""
        delay_factor = vendor_config.get('delay_factor', 1)
        timeout = vendor_config.get('timeout', 30)
        
        return connection.send_command(
            command,
            delay_factor=delay_factor,
            max_loops=500,
            cmd_verify=False,
            read_timeout=timeout
        )
        
    def run_bulk_inventory(self, devices: List[NetworkDevice], 
                          progress_callback=None) -> List[Dict[str, Any]]:
        """Run inventory on multiple devices with progress reporting"""
        results = []
        total_devices = len(devices)
        
        for idx, device in enumerate(devices):
            self.logger.info(f"Processing device {idx + 1}/{total_devices}: {device.hostname}")
            
            if progress_callback:
                progress_callback(idx, total_devices, device.hostname)
                
            result = self.run_device_commands(device)
            results.append(result)
            
        if progress_callback:
            progress_callback(total_devices, total_devices, "Complete")
            
        return results