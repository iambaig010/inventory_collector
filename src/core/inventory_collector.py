# src/core/inventory_collector.py
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
    
    def __init__(self, max_workers: int = 10):
        self.device_manager = DeviceManager()
        self.command_runner = CommandRunner()
        self.output_parser = OutputParser()
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def collect_inventory(self, 
                         devices_file: str, 
                         progress_callback: Optional[Callable] = None,
                         error_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Complete inventory collection workflow"""
        
        self.logger.info(f"Starting inventory collection from {devices_file}")
        
        try:
            # Step 1: Load and validate devices
            self.logger.info("Loading devices from Excel file...")
            devices = self.device_manager.load_from_excel(devices_file)
            self.logger.info(f"Loaded {len(devices)} devices")
            
            if progress_callback:
                progress_callback("loaded_devices", len(devices), 0, "Devices loaded")
                
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
        
        # Step 3: Parse outputs
        self.logger.info("Parsing device outputs...")
        parsed_results = []
        
        for i, raw_result in enumerate(raw_results):
            if progress_callback:
                progress_callback("parsing", len(raw_results), i, 
                                f"Parsing {raw_result['device_info']['hostname']}")
                                
            try:
                # Parse the raw output
                device_type = raw_result['device_info']['device_type']
                parsed_data = self.output_parser.parse_device_output(
                    device_type, raw_result['raw_output']
                )
                
                # Combine everything into final result
                final_result = {
                    'device_info': raw_result['device_info'],
                    'parsed_data': parsed_data,
                    'errors': raw_result.get('errors', []),
                    'collection_time': datetime.now().isoformat()
                }
                
                parsed_results.append(final_result)
                
            except Exception as e:
                error_msg = f"Failed to parse output for {raw_result['device_info']['hostname']}: {str(e)}"
                self.logger.error(error_msg)
                
                # Create error result
                error_result = {
                    'device_info': raw_result['device_info'],
                    'parsed_data': self.output_parser.generic_parse({}, device_type),
                    'errors': raw_result.get('errors', []) + [error_msg],
                    'collection_time': datetime.now().isoformat()
                }
                parsed_results.append(error_result)
                
        if progress_callback:
            progress_callback("complete", len(parsed_results), len(parsed_results), 
                            "Collection complete")
            
        self.logger.info(f"Inventory collection complete. Processed {len(parsed_results)} devices")
        return parsed_results
        
    async def collect_inventory_async(self, devices_file: str,
                                    progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Asynchronous inventory collection"""
        devices = self.device_manager.load_from_excel(devices_file)
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(self.executor, self.collect_device_data, device)
            for device in devices
        ]
        
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)
            if progress_callback:
                progress_callback("collecting", len(devices), i + 1, 
                                f"Collected {result['device_info']['hostname']}")
                
        return results

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
            
        return {
            'total_devices': total_devices,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_devices * 100) if total_devices > 0 else 0,
            'device_types': device_types,
            'status_counts': status_counts,
            'collection_time': datetime.now().isoformat()
        }