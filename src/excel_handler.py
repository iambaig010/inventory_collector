import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Handle Excel operations for device inventory"""
    
    def __init__(self):
        pass
    
    def generate_report(self, devices_data, output_file):
        """Generate Excel report from devices data"""
        try:
            # Prepare data for DataFrame
            report_data = []
            
            for device_name, device_results in devices_data.items():
                if isinstance(device_results, dict) and 'error' not in device_results:
                    for cmd_name, cmd_result in device_results.items():
                        if isinstance(cmd_result, dict):
                            report_data.append({
                                'Device': device_name,
                                'Command': cmd_result.get('command', cmd_name),
                                'Status': cmd_result.get('status', 'unknown'),
                                'Output': cmd_result.get('output', '')[:500],  # Truncate long output
                                'Timestamp': datetime.fromtimestamp(
                                    cmd_result.get('timestamp', 0)
                                ).strftime('%Y-%m-%d %H:%M:%S') if cmd_result.get('timestamp') else ''
                            })
                else:
                    # Handle error cases
                    report_data.append({
                        'Device': device_name,
                        'Command': 'ERROR',
                        'Status': 'failed',
                        'Output': str(device_results.get('error', 'Unknown error')),
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # Create DataFrame
            if report_data:
                df = pd.DataFrame(report_data)
            else:
                # Create empty DataFrame with proper columns
                df = pd.DataFrame(columns=['Device', 'Command', 'Status', 'Output', 'Timestamp'])
            
            # Write to Excel
            df.to_excel(output_file, index=False, sheet_name='Device_Inventory')
            logger.info(f"Report generated: {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def create_device_template(self, output_file):
        """Create device template Excel file"""
        try:
            template_data = {
                'hostname': ['switch-01', 'router-01', 'firewall-01'],
                'ip_address': ['192.168.1.10', '192.168.1.1', '192.168.1.254'],
                'username': ['admin', 'admin', 'admin'],
                'password': ['password123', 'password123', 'password123'],
                'device_type': ['cisco_ios', 'cisco_ios', 'cisco_asa'],
                'port': [22, 22, 22],
                'location': ['Server Room', 'Network Closet', 'DMZ'],
                'description': ['Core Switch', 'Main Router', 'Perimeter Firewall']
            }
            
            df = pd.DataFrame(template_data)
            df.to_excel(output_file, index=False, sheet_name='Device_Template')
            logger.info(f"Template created: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
