import logging
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from device_manager import DeviceManager, NetworkDevice
from command_runner import CommandRunner
from excel_handler import ExcelHandler

logger = logging.getLogger(__name__)

class SwitchInventoryTool:
    """Main application class"""
    
    def __init__(self):
        self.device_manager = DeviceManager()
        self.command_runner = CommandRunner()
        self.excel_handler = ExcelHandler()
    
    def load_devices(self, excel_file):
        """Load devices from Excel file"""
        return self.device_manager.load_devices_from_excel(excel_file)
    
    def run_inventory(self, progress_callback=None):
        """Run inventory on all loaded devices"""
        devices = self.device_manager.devices
        if not devices:
            raise ValueError("No devices loaded")
        
        return self.command_runner.run_bulk_inventory(devices, progress_callback)
    
    def generate_report(self, results, output_file):
        """Generate Excel report from results"""
        return self.excel_handler.generate_report(results, output_file)

def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    tool = SwitchInventoryTool()
    
    # Example usage
    try:
        # Create template if needed
        template_file = "device_template.xlsx"
        if not Path(template_file).exists():
            tool.excel_handler.create_device_template(template_file)
            print(f"Created device template: {template_file}")
        
        print("Switch Inventory Tool ready!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
