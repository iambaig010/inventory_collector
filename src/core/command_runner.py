# src/core/command_runner.py
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import logging
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

class CommandRunner:
    def __init__(self, config_path: Optional[str] = None):
        self.ssh_connector = SSHConnector()
        self.vendor_configs = self.load_vendor_configs(config_path)
        self.logger = logging.getLogger(__name__)
        
    def load_vendor_configs(self, config_path: str) -> Dict[str, Any]:
        """Load vendor configurations from YAML file"""
        try:
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config.get('vendors', {})
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self.get_default_configs()
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return self.get_default_configs()
            
    def get_default_configs(self) -> Dict[str, Any]:
        """Default vendor configurations"""
        return {
            'cisco_ios': {
                'commands': {
                    'version': 'show version',
                    'interfaces': 'show ip interface brief',
                    'inventory': 'show inventory'
                },
                'timeout': 30,
                'delay_factor': 1
            }
        }
        
    @retry_with_backoff(retries=3)  # Replace backoff.on_exception with our decorator
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
                    self.logger.debug(f"Executing command '{command}' on {device.hostname}")
                    output = self.execute_command(connection, command, vendor_config)
                    result['raw_output'][command_name] = output
                    
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
            cmd_verify=False
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