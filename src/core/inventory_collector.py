#!/usr/bin/env python3
"""
Updated Inventory Collector - Extract hostname from device parsing
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from .device_manager import DeviceManager, NetworkDevice
from .command_runner import CommandRunner
from .output_parser import OutputParser
import asyncio
from concurrent.futures import ThreadPoolExecutor

class InventoryCollector:
    """Main orchestrator for the inventory collection process"""
    
    def __init__(self, max_workers: int = 10, config_path: str = "src/configs/command_configs.yaml"):
        self.device_manager = DeviceManager()
        self.command_runner = CommandRunner(config_path)
        self.output_parser = OutputParser()
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def collect_inventory_from_ips(self, 
                                  devices_file: str,
                                  username: str,
                                  password: str,
                                  device_type: str = "cisco_ios",
                                  port: int = 22,
                                  progress_callback: Optional[Callable] = None,
                                  error_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        Complete inventory collection workflow with IP-only Excel input
        
        Args:
            devices_file: Path to Excel file containing IP addresses
            username: SSH username (from GUI)
            password: SSH password (from GUI) 
            device_type: Default device type (from GUI)
            port: Default SSH port
            progress_callback: Progress reporting callback
            error_callback: Error reporting callback
            
        Returns:
            List of inventory results with hostnames extracted from devices
        """
        
        self.logger.info(f"Starting inventory collection from {devices_file}")
        
        try:
            # Step 1: Load and validate devices (IP addresses only)
            self.logger.info("Loading IP addresses from Excel file...")
            devices = self.device_manager.load_from_excel(
                devices_file, username, password, device_type, port
            )
            self.logger.info(f"Loaded {len(devices)} devices")
            
            if progress_callback:
                progress_callback("loaded_devices", len(devices), 0, "IP addresses loaded")
                
        except Exception as e:
            error_msg = f"Failed to load devices: {str(e)}"
            self.logger.error(error_msg)
            if error_callback:
                error_callback("load_error", error_msg)
            raise
            
        # Step 2: Collect raw data from devices
        self.logger.info("Starting device data collection...")
        
        def device_progress(current, total, device_name):
            if progress_callback:
                progress_callback("collecting", total, current, 
                                f"Collecting from {device_name}")
                                
        raw_results = self.command_runner.run_bulk_inventory(
            devices, device_progress
        )
        
        # Step 3: Parse outputs and extract hostnames
        self.logger.info("Parsing device outputs and extracting hostnames...")
        parsed_results = []
        
        for i, raw_result in enumerate(raw_results):
            if progress_callback:
                progress_callback("parsing", len(raw_results), i, 
                                f"Parsing {raw_result['device_info']['ip_address']}")
                                
            try:
                # Parse the raw output
                device_type = raw_result['device_info']['device_type']
                parsed_data = self.output_parser.parse_device_output(
                    device_type, raw_result['raw_output']
                )
                
                # Extract hostname from parsed data
                extracted_hostname = parsed_data.get('hostname', 'Unknown')
                if extracted_hostname and extracted_hostname != 'Unknown':
                    # Update the device hostname
                    ip_address = raw_result['device_info']['ip_address']
                    self.device_manager.update_device_hostname(ip_address, extracted_hostname)
                    # Update the result
                    raw_result['device_info']['hostname'] = extracted_hostname
                else:
                    # Use IP as fallback hostname
                    ip_addr = raw_result['device_info']['ip_address']
                    fallback_hostname = f"device-{ip_addr.replace('.', '-')}"
                    raw_result['device_info']['hostname'] = fallback_hostname
                    parsed_data['hostname'] = fallback_hostname
                
                # Combine everything into final result
                final_result = {
                    'device_info': raw_result['device_info'],
                    'parsed_data': parsed_data,
                    'errors': raw_result.get('errors', []),
                    'collection_time': datetime.now().isoformat()
                }
                
                parsed_results.append(final_result)
                
            except Exception as e:
                error_msg = f"Failed to parse output for {raw_result['device_info']['ip_address']}: {str(e)}"
                self.logger.error(error_msg)
                
                # Create error result with fallback hostname
                ip_addr = raw_result['device_info']['ip_address']
                fallback_hostname = f"device-{ip_addr.replace('.', '-')}"
                raw_result['device_info']['hostname'] = fallback_hostname
                
                error_result = {
                    'device_info': raw_result['device_info'],
                    'parsed_data': self.output_parser.generic_parse({}, device_type),
                    'errors': raw_result.get('errors', []) + [error_msg],
                    'collection_time': datetime.now().isoformat()
                }
                error_result['parsed_data']['hostname'] = fallback_hostname
                parsed_results.append(error_result)
                
        if progress_callback:
            progress_callback("complete", len(parsed_results), len(parsed_results), 
                            "Collection complete")
            
        self.logger.info(f"Inventory collection complete. Processed {len(parsed_results)} devices")
        return parsed_results
    
    def validate_excel_file(self, file_path: str) -> Dict[str, Any]:
        """Validate Excel file for IP-only format"""
        return self.device_manager.validate_excel_file(file_path)
    
    def create_ip_template(self, output_file: str):
        """Create Excel template for IP addresses only"""
        self.device_manager.create_device_template(output_file)
        
    async def collect_inventory_async(self, 
                                    devices_file: str,
                                    username: str,
                                    password: str,
                                    device_type: str = "cisco_ios",
                                    port: int = 22,
                                    progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Asynchronous inventory collection with IP-only input"""
        
        devices = self.device_manager.load_from_excel(
            devices_file, username, password, device_type, port
        )
        
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(self.executor, self.collect_device_data, device)
            for device in devices
        ]
        
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            
            # Extract hostname and update device info
            if result['parsed_data'].get('hostname'):
                result['device_info']['hostname'] = result['parsed_data']['hostname']
            
            results.append(result)
            
            if progress_callback:
                progress_callback("collecting", len(devices), i + 1, 
                                f"Collected {result['device_info']['hostname']}")
                
        return results

    def collect_device_data(self, device: NetworkDevice) -> Dict[str, Any]:
        """Collect data from a single device"""
        try:
            # Run commands on device
            raw_result = self.command_runner.run_device_commands(device)
            
            # Parse the output
            parsed_data = self.output_parser.parse_device_output(
                device.device_type, raw_result['raw_output']
            )
            
            # Extract and update hostname
            extracted_hostname = parsed_data.get('hostname', 'Unknown')
            if extracted_hostname and extracted_hostname != 'Unknown':
                device.update_hostname(extracted_hostname)
                raw_result['device_info']['hostname'] = extracted_hostname
            
            return {
                'device_info': raw_result['device_info'],
                'parsed_data': parsed_data,
                'errors': raw_result.get('errors', []),
                'collection_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect data from {device.ip_address}: {e}")
            return {
                'device_info': {
                    'hostname': f"device-{device.ip_address.replace('.', '-')}",
                    'ip_address': device.ip_address,
                    'device_type': device.device_type,
                    'connection_status': 'failed'
                },
                'parsed_data': {},
                'errors': [str(e)],
                'collection_time': datetime.now().isoformat()
            }

    def get_collection_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from collection results"""
        total_devices = len(results)
        successful = sum(1 for r in results if r['device_info']['connection_status'] == 'success')
        failed = total_devices - successful
        
        # Count by device type
        device_types = {}
        for result in results:
            dtype = result['device_info']['device_type']
            device_types[dtype] = device_types.get(dtype, 0) + 1
            
        # Count by status
        status_counts = {}
        for result in results:
            status = result['device_info']['connection_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Collect discovered hostnames
        discovered_hostnames = []
        for result in results:
            hostname = result['device_info'].get('hostname', '')
            ip = result['device_info'].get('ip_address', '')
            if hostname and not hostname.startswith('device-'):
                discovered_hostnames.append(f"{hostname} ({ip})")
            
        return {
            'total_devices': total_devices,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_devices * 100) if total_devices > 0 else 0,
            'device_types': device_types,
            'status_counts': status_counts,
            'discovered_hostnames': discovered_hostnames,
            'hostname_discovery_rate': (len(discovered_hostnames) / total_devices * 100) if total_devices > 0 else 0,
            'collection_time': datetime.now().isoformat()
        }