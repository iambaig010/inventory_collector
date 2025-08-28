#!/usr/bin/env python3
"""
Demo preparation and validation script
"""
import os
import sys
import logging
import tempfile
import pandas as pd
from pathlib import Path

# Add both src and project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from tests.mock_ssh_server import start_mock_ssh_server
from src.core.inventory_collector import InventoryCollector
from src.utils.excel_handler import ExcelHandler

class DemoPreparation:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for demo prep"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def create_demo_files(self):
        """Create all necessary demo files"""
        demo_dir = Path("demo")
        demo_dir.mkdir(exist_ok=True)
        
        # Create device template
        self.logger.info("Creating device template...")
        excel_handler = ExcelHandler()
        template_path = demo_dir / "device_template.xlsx"
        excel_handler.create_device_template(str(template_path))
        
        # Create demo device file
        self.logger.info("Creating demo device file...")
        demo_devices = [
            {
                'hostname': 'DEMO-CORE-SW01',
                'ip_address': '127.0.0.1',
                'username': 'demo',
                'password': 'demo',
                'device_type': 'cisco_ios',
                'port': 2221,
                'location': 'Demo Data Center',
                'description': 'Core Demo Switch'
            },
            {
                'hostname': 'DEMO-ACCESS-SW02',
                'ip_address': '127.0.0.1',
                'username': 'demo',
                'password': 'demo',
                'device_type': 'cisco_ios',
                'port': 2221,
                'location': 'Demo IDF',
                'description': 'Access Demo Switch'
            },
            {
                'hostname': 'DEMO-EDGE-SW03',
                'ip_address': '127.0.0.1',
                'username': 'demo',
                'password': 'demo',
                'device_type': 'cisco_ios',
                'port': 2221,
                'location': 'Demo Edge',
                'description': 'Edge Demo Switch'
            }
        ]
        
        df = pd.DataFrame(demo_devices)
        demo_file_path = demo_dir / "demo_devices.xlsx"
        df.to_excel(demo_file_path, index=False)
        
        self.logger.info(f"Demo files created in {demo_dir}")
        return demo_file_path
        
    def start_demo_servers(self):
        """Start mock SSH servers for demo"""
        self.logger.info("Starting demo SSH servers...")
        
        # Start Cisco mock server
        cisco_thread = start_mock_ssh_server(2221, 'cisco_ios')
        
        self.logger.info("Demo servers started:")
        self.logger.info("  - Cisco IOS server on port 2221")
        
        return cisco_thread
        
    def run_demo(self):
        """Run complete demo setup"""
        try:
            # Create demo files
            demo_file_path = self.create_demo_files()
            
            # Start servers
            server_thread = self.start_demo_servers()
            
            self.logger.info("Demo preparation complete!")
            self.logger.info(f"Demo devices file: {demo_file_path}")
            self.logger.info("You can now run the inventory collection.")
            
            return demo_file_path, server_thread
            
        except Exception as e:
            self.logger.error(f"Demo preparation failed: {e}")
            raise

if __name__ == "__main__":
    demo_prep = DemoPreparation()
    demo_prep.run_demo()