#!/usr/bin/env python3
"""
Updated Command Runner - Compatible with IP-only device approach
"""
import os
import re
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
                            time.sleep(2 ** attempt)
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
    """Enhanced command runner compatible with IP-only device loading"""
    
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
        """Create comprehensive default YAML config file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_yaml = {
            'cisco_ios': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_ip_interface_brief', 'command': 'show ip interface brief', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_interfaces_status', 'command': 'show interfaces status', 'description': 'Interface status', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45},
                {'name': 'show_switch_detail', 'command': 'show switch detail', 'description': 'Stack details', 'timeout': 45}
            ],
            'cisco_xe': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_ip_interface_brief', 'command': 'show ip interface brief', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_interfaces_status', 'command': 'show interfaces status', 'description': 'Interface status', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45},
                {'name': 'show_platform', 'command': 'show platform', 'description': 'Platform info', 'timeout': 30}
            ],
            'cisco_nxos': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_interface_brief', 'command': 'show interface brief', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45}
            ],
            'juniper_junos': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_interfaces_terse', 'command': 'show interfaces terse', 'description': 'Interface summary', 'timeout': 30},
                {'name': 'show_chassis_hardware', 'command': 'show chassis hardware', 'description': 'Hardware info', 'timeout': 45}
            ],
            'hirschmann_hios': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version and hardware info', 'timeout': 30},
                {'name': 'show_system_information', 'command': 'show system information', 'description': 'System info with hostname', 'timeout': 30},
                {'name': 'show_inventory', 'command': 'show inventory', 'description': 'Hardware inventory', 'timeout': 45},
                {'name': 'show_interfaces_brief', 'command': 'show interfaces brief', 'description': 'Interface information', 'timeout': 30},
                {'name': 'show_mac_address_table', 'command': 'show mac-address-table', 'description': 'MAC address table', 'timeout': 30}
            ],
            'generic_ssh': [
                {'name': 'show_version', 'command': 'show version', 'description': 'Device version info', 'timeout': 30},
                {'name': 'show_interfaces', 'command': 'show interfaces', 'description': 'Interface information', 'timeout': 30}
            ]
        }
        
        try:
            with open(config_path, 'w') as f:
                yaml.dump(default_yaml, f, default_flow_style=False, indent=2)
            self.logger.info(f"Created default config file: {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to create config file: {e}")
            
    def get_default_configs(self) -> Dict[str, Any]:
        """Enhanced default vendor configurations"""
        return {
            'cisco_ios': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show ip interface brief',
                    'inventory': 'show inventory',
                    'status': 'show interfaces status',
                    'switch_detail': 'show switch detail'
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
            },
            'cisco_nxos': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show interface brief',
                    'inventory': 'show inventory'
                },
                'timeout': 30,
                'delay_factor': 1
            },
            'juniper_junos': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show interfaces terse',
                    'chassis': 'show chassis hardware'
                },
                'timeout': 30,
                'delay_factor': 1
            },
            'hirschmann_hios': {
                'commands': {
                    'version': 'show version',
                    'system_info': 'show system information',
                    'inventory': 'show inventory',
                    'interfaces': 'show interfaces brief',
                    'mac_table': 'show mac-address-table'
                },
                'timeout': 30,
                'delay_factor': 1
            },
            'generic_ssh': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show interfaces'
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
            # Fallback to generic_ssh
            vendor_config = self.vendor_configs.get('generic_ssh', {})
            commands = vendor_config.get('commands', {})
        
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
        """Execute commands with retry mechanism and hostname extraction focus"""
        result = {
            'device_info': {
                'hostname': device.hostname,  # Initial hostname (may be IP-based)
                'ip_address': device.ip_address,
                'device_type': device.device_type,
                'connection_status': 'failed',
                'timestamp': None,
                'location': device.location,
                'description': device.description
            },
            'raw_output': {},
            'errors': []
        }
        
        connection = None
        try:
            # Establish connection
            self.logger.info(f"Processing device: {device.ip_address} (type: {device.device_type})")
            connection = self.ssh_connector.connect_with_retry(device)
            result['device_info']['connection_status'] = 'connected'
            result['device_info']['timestamp'] = time.time()
            
            # Get vendor-specific commands
            vendor_config = self.vendor_configs.get(device.device_type, {})
            commands = vendor_config.get('commands', {})
            
            if not commands:
                # Try generic fallback
                self.logger.warning(f"No commands for {device.device_type}, trying generic_ssh")
                vendor_config = self.vendor_configs.get('generic_ssh', {})
                commands = vendor_config.get('commands', {})
                
                if not commands:
                    raise ValueError(f"No commands available for device type: {device.device_type}")
            
            # Execute each command with priority on hostname discovery
            hostname_discovered = False
            
            # Prioritize commands that typically contain hostname information
            priority_commands = ['version', 'system_info', 'show_version', 'show_system_information']
            other_commands = [cmd for cmd in commands.keys() if cmd not in priority_commands]
            
            # Execute priority commands first
            for command_name in priority_commands:
                if command_name in commands:
                    command = commands[command_name]
                    try:
                        self.logger.info(f"Executing priority command '{command}' on {device.ip_address}")
                        output = self.execute_command(connection, command, vendor_config)
                        result['raw_output'][command_name] = output
                        
                        # Quick check for hostname in output
                        if not hostname_discovered and self._contains_hostname_info(output):
                            hostname_discovered = True
                            self.logger.debug(f"Hostname information found in '{command}' output")
                        
                    except Exception as e:
                        error_msg = f"Priority command '{command}' failed: {str(e)}"
                        self.logger.warning(f"{device.ip_address}: {error_msg}")
                        result['errors'].append(error_msg)
                        result['raw_output'][command_name] = f"ERROR: {str(e)}"
            
            # Execute remaining commands
            for command_name in other_commands:
                command = commands[command_name]
                try:
                    self.logger.info(f"Executing command '{command}' on {device.ip_address}")
                    output = self.execute_command(connection, command, vendor_config)
                    result['raw_output'][command_name] = output
                    
                except Exception as e:
                    error_msg = f"Command '{command}' failed: {str(e)}"
                    self.logger.warning(f"{device.ip_address}: {error_msg}")
                    result['errors'].append(error_msg)
                    result['raw_output'][command_name] = f"ERROR: {str(e)}"
            
            result['device_info']['connection_status'] = 'success'
            self.logger.info(f"Successfully collected data from {device.ip_address}")
            
        except Exception as e:
            error_msg = f"Failed to process device: {str(e)}"
            self.logger.error(f"{device.ip_address}: {error_msg}")
            result['device_info']['connection_status'] = 'failed'
            result['errors'].append(error_msg)
            
        finally:
            if connection:
                self.ssh_connector.disconnect(connection)
                
        return result
    
    def _contains_hostname_info(self, output: str) -> bool:
        """Quick check if output likely contains hostname information"""
        hostname_indicators = [
            r'hostname\s+\S+',
            r'system name\s*:\s*\S+',
            r'\S+\s+uptime',
            r'device name\s*:\s*\S+'
        ]
        
        for pattern in hostname_indicators:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False
    
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
        """
        Run inventory on multiple devices with enhanced progress reporting
        Compatible with IP-only device loading
        """
        results = []
        total_devices = len(devices)
        
        self.logger.info(f"Starting bulk inventory collection on {total_devices} devices")
        
        for idx, device in enumerate(devices):
            device_identifier = device.hostname if device.hostname else device.ip_address
            self.logger.info(f"Processing device {idx + 1}/{total_devices}: {device_identifier}")
            
            if progress_callback:
                progress_callback(idx, total_devices, device_identifier)
            
            try:
                result = self.run_device_commands(device)
                results.append(result)
                
                # Log connection status
                status = result['device_info']['connection_status']
                if status == 'success':
                    self.logger.info(f"✓ Successfully processed {device_identifier}")
                else:
                    self.logger.warning(f"✗ Failed to process {device_identifier}")
                    
            except Exception as e:
                # Create error result
                error_result = {
                    'device_info': {
                        'hostname': device.hostname,
                        'ip_address': device.ip_address,
                        'device_type': device.device_type,
                        'connection_status': 'failed',
                        'timestamp': time.time(),
                        'location': device.location,
                        'description': device.description
                    },
                    'raw_output': {},
                    'errors': [str(e)]
                }
                results.append(error_result)
                self.logger.error(f"✗ Exception processing {device_identifier}: {e}")
        
        if progress_callback:
            progress_callback(total_devices, total_devices, "Complete")
        
        # Summary logging
        successful = sum(1 for r in results if r['device_info']['connection_status'] == 'success')
        failed = total_devices - successful
        
        self.logger.info(f"Bulk inventory complete: {successful} successful, {failed} failed")
        
        return results
    
    def test_device_connection(self, device: NetworkDevice) -> Dict[str, Any]:
        """Test connection to a single device without running full inventory"""
        result = {
            'ip_address': device.ip_address,
            'device_type': device.device_type,
            'connection_successful': False,
            'hostname_discovered': 'Unknown',
            'error_message': '',
            'response_time': 0
        }
        
        connection = None
        start_time = time.time()
        
        try:
            # Test connection
            connection = self.ssh_connector.connect_with_retry(device)
            
            # Try to get hostname quickly
            try:
                version_output = self.execute_command(connection, 'show version', {'timeout': 15, 'delay_factor': 1})
                
                # Quick hostname extraction
                hostname_patterns = [
                    r'(\S+)\s+uptime',
                    r'hostname\s+(\S+)',
                    r'system name\s*:\s*(\S+)'
                ]
                
                for pattern in hostname_patterns:
                    match = re.search(pattern, version_output, re.IGNORECASE)
                    if match:
                        result['hostname_discovered'] = match.group(1)
                        break
                        
            except Exception as e:
                self.logger.debug(f"Could not extract hostname during test: {e}")
            
            result['connection_successful'] = True
            result['response_time'] = time.time() - start_time
            
        except Exception as e:
            result['error_message'] = str(e)
            result['response_time'] = time.time() - start_time
            
        finally:
            if connection:
                self.ssh_connector.disconnect(connection)
        
        return result
    
    def get_device_type_from_banner(self, device: NetworkDevice) -> str:
        """Attempt to auto-detect device type from SSH banner or initial response"""
        connection = None
        detected_type = device.device_type  # Default to provided type
        
        try:
            # Create a temporary connection to check banner
            connection_params = {
                'device_type': 'generic_ssh',  # Use generic first
                'host': device.ip_address,
                'username': device.username,
                'password': device.password,
                'port': device.port,
                'timeout': 10
            }
            
            from netmiko import ConnectHandler
            connection = ConnectHandler(**connection_params)
            
            # Get initial prompt/banner
            prompt = connection.find_prompt()
            
            # Try a version command to get more info
            try:
                version_output = connection.send_command('show version', read_timeout=10)
                
                # Detect device type based on version output
                if 'cisco ios' in version_output.lower():
                    if 'ios-xe' in version_output.lower():
                        detected_type = 'cisco_xe'
                    else:
                        detected_type = 'cisco_ios'
                elif 'nx-os' in version_output.lower():
                    detected_type = 'cisco_nxos'
                elif 'junos' in version_output.lower():
                    detected_type = 'juniper_junos'
                elif 'hios' in version_output.lower() or 'hirschmann' in version_output.lower():
                    detected_type = 'hirschmann_hios'
                    
            except Exception:
                # If version command fails, use prompt analysis
                if '>' in prompt or '#' in prompt:
                    # Likely Cisco-like
                    detected_type = 'cisco_ios'
                    
        except Exception as e:
            self.logger.debug(f"Auto-detection failed for {device.ip_address}: {e}")
            
        finally:
            if connection:
                try:
                    connection.disconnect()
                except:
                    pass
        
        if detected_type != device.device_type:
            self.logger.info(f"Auto-detected device type for {device.ip_address}: {detected_type}")
        
        return detected_type
    
    def update_device_commands(self, device_type: str, new_commands: Dict[str, str]):
        """Update commands for a specific device type"""
        if device_type not in self.vendor_configs:
            self.vendor_configs[device_type] = {
                'commands': {},
                'timeout': 30,
                'delay_factor': 1
            }
        
        self.vendor_configs[device_type]['commands'].update(new_commands)
        self.logger.info(f"Updated commands for {device_type}: {list(new_commands.keys())}")
    
    def get_command_statistics(self) -> Dict[str, Any]:
        """Get statistics about available commands per device type"""
        stats = {}
        
        for device_type, config in self.vendor_configs.items():
            commands = config.get('commands', {})
            stats[device_type] = {
                'command_count': len(commands),
                'commands': list(commands.keys()),
                'timeout': config.get('timeout', 30)
            }
        
        return stats
    
    def export_commands_config(self, output_file: str):
        """Export current command configuration to YAML file"""
        try:
            # Convert current config back to YAML format
            yaml_config = {}
            
            for device_type, config in self.vendor_configs.items():
                commands = config.get('commands', {})
                yaml_commands = []
                
                for cmd_name, cmd_string in commands.items():
                    yaml_commands.append({
                        'name': cmd_name,
                        'command': cmd_string,
                        'description': f"Execute {cmd_string}",
                        'timeout': config.get('timeout', 30)
                    })
                
                yaml_config[device_type] = yaml_commands
            
            with open(output_file, 'w') as f:
                yaml.dump(yaml_config, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Commands configuration exported to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export commands config: {e}")
            raise