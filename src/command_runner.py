#!/usr/bin/env python3
"""
Enhanced Command Runner with proper config handling and Hirschmann support
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class DeviceCommand:
    """Structured command definition"""
    name: str
    command: str
    description: str
    timeout: int = 30
    parser_hints: Optional[Dict[str, Any]] = None

class CommandRunner:
    """
    Enhanced command runner with proper configuration management
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._get_default_config_path()
        self.device_commands: Dict[str, List[DeviceCommand]] = {}
        self._load_commands()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Try multiple possible locations for robustness
        possible_paths = [
            Path(__file__).parent.parent / 'configs' / 'command_configs.yaml',
            Path('src/configs/command_configs.yaml'),
            Path('configs/command_configs.yaml'),
        ]
        
        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Using config file: {path}")
                return str(path)
        
        # If none exist, use the preferred location
        default_path = Path(__file__).parent.parent / 'configs' / 'command_configs.yaml'
        self.logger.warning(f"Config file not found, will use: {default_path}")
        return str(default_path)
    
    def _load_commands(self):
        """Load device commands from configuration file"""
        try:
            config_path = Path(self.config_path)
            
            if not config_path.exists():
                self.logger.error(f"Command config file not found: {config_path}")
                self._create_default_config()
                return
            
            with open(config_path, 'r') as f:
                configs = yaml.safe_load(f)
            
            if not configs:
                self.logger.error("Empty configuration file")
                return
            
            # Convert to structured commands
            for device_type, commands in configs.items():
                self.device_commands[device_type] = []
                
                for cmd_config in commands:
                    if isinstance(cmd_config, dict):
                        command = DeviceCommand(
                            name=cmd_config.get('name', ''),
                            command=cmd_config.get('command', ''),
                            description=cmd_config.get('description', ''),
                            timeout=cmd_config.get('timeout', 30),
                            parser_hints=cmd_config.get('parser_hints')
                        )
                    else:
                        # Handle simple string commands for backward compatibility
                        command = DeviceCommand(
                            name=str(cmd_config).replace(' ', '_'),
                            command=str(cmd_config),
                            description=f"Execute {cmd_config}"
                        )
                    
                    self.device_commands[device_type].append(command)
            
            self.logger.info(f"Loaded commands for {len(self.device_commands)} device types")
            
        except Exception as e:
            self.logger.error(f"Failed to load command configurations: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file with all supported device types"""
        config_path = Path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            'cisco_ios': [
                {
                    'name': 'show_version',
                    'command': 'show version',
                    'description': 'Device version and hardware information',
                    'timeout': 30,
                    'parser_hints': {'serial_regex': r'System Serial Number\s+:\s+(\S+)'}
                },
                {
                    'name': 'show_interfaces_status',
                    'command': 'show interfaces status',
                    'description': 'Interface status information',
                    'timeout': 45
                },
                {
                    'name': 'show_ip_interface_brief',
                    'command': 'show ip interface brief',
                    'description': 'IP interface summary'
                },
                {
                    'name': 'show_running_config',
                    'command': 'show running-config',
                    'description': 'Current running configuration',
                    'timeout': 60
                },
                {
                    'name': 'show_cdp_neighbors',
                    'command': 'show cdp neighbors detail',
                    'description': 'CDP neighbor information'
                },
                {
                    'name': 'show_mac_address_table',
                    'command': 'show mac address-table',
                    'description': 'MAC address table'
                }
            ],
            'cisco_nxos': [
                {
                    'name': 'show_version',
                    'command': 'show version',
                    'description': 'Device version and hardware information'
                },
                {
                    'name': 'show_interface_brief',
                    'command': 'show interface brief',
                    'description': 'Interface brief information'
                },
                {
                    'name': 'show_mac_address_table',
                    'command': 'show mac address-table',
                    'description': 'MAC address table'
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
            ],
            'hirschmann_hios': [
                {
                    'name': 'show_version',
                    'command': 'show version',
                    'description': 'Device version and hardware information',
                    'timeout': 30,
                    'parser_hints': {
                        'version_regex': r'Software Version\s+:\s+(.+)',
                        'model_regex': r'Product\s+:\s+(.+)',
                        'serial_regex': r'Serial Number\s+:\s+(\S+)'
                    }
                },
                {
                    'name': 'show_system_information',
                    'command': 'show system information',
                    'description': 'System information including hostname and uptime',
                    'timeout': 30,
                    'parser_hints': {
                        'hostname_regex': r'System Name\s+:\s+(.+)',
                        'uptime_regex': r'System Up Time\s+:\s+(.+)'
                    }
                },
                {
                    'name': 'show_inventory',
                    'command': 'show inventory',
                    'description': 'Hardware inventory information',
                    'timeout': 45
                },
                {
                    'name': 'show_interfaces_brief',
                    'command': 'show interfaces brief',
                    'description': 'Interface brief information',
                    'timeout': 30,
                    'parser_hints': {'table_parser': 'whitespace_split'}
                },
                {
                    'name': 'show_mac_address_table',
                    'command': 'show mac-address-table',
                    'description': 'MAC address table',
                    'timeout': 30,
                    'parser_hints': {'table_parser': 'whitespace_split'}
                }
            ],
            'generic_ssh': [
                {
                    'name': 'show_version',
                    'command': 'show version',
                    'description': 'Device version information'
                },
                {
                    'name': 'show_interfaces',
                    'command': 'show interfaces',
                    'description': 'Interface information'
                }
            ]
        }
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created default configuration at: {config_path}")
            self.device_commands = {
                device_type: [DeviceCommand(**cmd) for cmd in commands]
                for device_type, commands in default_config.items()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
    
    def get_commands_for_device(self, device_type: str) -> List[DeviceCommand]:
        """Get commands for a specific device type"""
        commands = self.device_commands.get(device_type, [])
        
        if not commands and device_type != 'generic_ssh':
            self.logger.warning(f"No commands found for device type: {device_type}, falling back to generic_ssh")
            commands = self.device_commands.get('generic_ssh', [])
        
        return commands
    
    def get_supported_device_types(self) -> List[str]:
        """Get list of supported device types"""
        return list(self.device_commands.keys())
    
    def validate_device_type(self, device_type: str) -> bool:
        """Check if device type is supported"""
        return device_type in self.device_commands or device_type == 'generic_ssh'
    
    def run_device_commands(self, device: Dict[str, Any], connector) -> Dict[str, Any]:
        """
        Execute commands on a device using the provided connector
        
        Args:
            device: Device information dictionary
            connector: Connection object with execute_command method
            
        Returns:
            Dictionary of command results
        """
        device_type = device.get('device_type', 'generic_ssh')
        commands = self.get_commands_for_device(device_type)
        
        if not commands:
            raise ValueError(f"No commands available for device type: {device_type}")
        
        results = {}
        hostname = device.get('hostname', device.get('ip_address', 'unknown'))
        
        self.logger.info(f"Running {len(commands)} commands on {hostname}")
        
        for command in commands:
            try:
                self.logger.debug(f"Executing: {command.command}")
                
                output = connector.execute_command(
                    command.command,
                    timeout=command.timeout
                )
                
                results[command.name] = {
                    'command': command.command,
                    'output': output,
                    'success': True,
                    'description': command.description,
                    'parser_hints': command.parser_hints
                }
                
            except Exception as e:
                self.logger.error(f"Command '{command.command}' failed on {hostname}: {e}")
                results[command.name] = {
                    'command': command.command,
                    'output': '',
                    'success': False,
                    'error': str(e),
                    'description': command.description
                }
        
        return results
    
    def reload_configuration(self):
        """Reload configuration from file"""
        self._load_commands()
    
    def add_custom_command(self, device_type: str, command: DeviceCommand):
        """Add a custom command for a device type"""
        if device_type not in self.device_commands:
            self.device_commands[device_type] = []
        
        self.device_commands[device_type].append(command)
        self.logger.info(f"Added custom command '{command.name}' for {device_type}")