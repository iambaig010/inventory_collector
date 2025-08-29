# src/utils/excel_handler.py
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import logging
from typing import List, Dict, Any

class ExcelHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_report(self, inventory_results: List[Dict[str, Any]], 
                        output_path: str, summary: Dict[str, Any] = None):
        """Generate comprehensive Excel report"""
        self.logger.info(f"Generating Excel report: {output_path}")
        
        wb = Workbook()
        wb.remove(wb.active)  # Remove default empty sheet
        
        # Main sheets
        self.create_inventory_sheet(wb, inventory_results)
        if summary:
            self.create_summary_sheet(wb, summary)
        self.create_error_sheet(wb, inventory_results)
        
        wb.save(output_path)
        self.logger.info(f"Excel report saved: {output_path}")
        
    def create_inventory_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create enhanced main inventory data sheet"""
        ws = wb.create_sheet("Device Inventory", 0)
        
        rows = []
        for result in results:
            device_info = result['device_info']
            parsed_data = result['parsed_data']
            
            stack_info = parsed_data.get('stack_details', [])
            stack_count = len(stack_info) if stack_info else 1
            
            row = {
                'Hostname': device_info.get('hostname', 'Unknown'),
                'IP Address': device_info.get('ip_address', 'Unknown'),
                'Device Type': device_info.get('device_type', 'Unknown'),
                'Model': parsed_data.get('model', 'Unknown'),
                'Chassis Serial': parsed_data.get('serial_number', 'Unknown'),
                'System Serial': parsed_data.get('system_serial', parsed_data.get('serial_number', 'Unknown')),
                'Software Version': parsed_data.get('version', 'Unknown'),
                'IOS Version': parsed_data.get('ios_version', parsed_data.get('version', 'Unknown')),
                'System Image': parsed_data.get('system_image', 'Unknown'),
                'Base MAC': parsed_data.get('base_mac', 'Unknown'),
                'Uptime': parsed_data.get('uptime', 'Unknown'),
                'Stack Count': stack_count,
                'Module Count': parsed_data.get('module_count', 0),
                'Hardware Modules': parsed_data.get('total_modules', 0),
                'Connection Status': device_info.get('connection_status', 'Unknown'),
                'Interface Count': len(parsed_data.get('interfaces', [])),
                'Has Errors': 'Yes' if result.get('errors') else 'No',
                'Collection Time': result.get('collection_time', 'Unknown')
            }
            rows.append(row)
            
        df = pd.DataFrame(rows)
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
            
        # Format the sheet
        self.format_inventory_sheet(ws)
        
        # Extra detail sheets
        self.create_hardware_modules_sheet(wb, results)
        self.create_stack_details_sheet(wb, results)
    
    def format_inventory_sheet(self, ws):
        """Format the main inventory sheet"""
        # Bold headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max((len(str(cell.value)) for cell in column if cell.value), default=0)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 35)

    def create_hardware_modules_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create hardware modules detail sheet"""
        ws = wb.create_sheet("Hardware Modules")
        
        # Headers
        headers = ["Hostname", "IP Address", "Module Name", "Description", "Product ID", "Version ID", "Serial Number"]
        ws.append(headers)
        
        # Data rows
        for result in results:
            device_info = result['device_info']
            parsed_data = result['parsed_data']
            
            hostname = device_info.get('hostname', 'Unknown')
            ip_address = device_info.get('ip_address', 'Unknown')
            
            # Get hardware modules
            hardware_modules = parsed_data.get('hardware_modules', [])
            if not hardware_modules:
                # Add a row even if no modules found
                ws.append([hostname, ip_address, 'No modules found', '', '', '', ''])
            else:
                for module in hardware_modules:
                    ws.append([
                        hostname,
                        ip_address,
                        module.get('name', 'Unknown'),
                        module.get('description', 'Unknown'),
                        module.get('product_id', 'Unknown'),
                        module.get('version_id', 'Unknown'),
                        module.get('serial_number', 'Unknown')
                    ])
        
        # Format headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    def create_stack_details_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create stack details sheet"""
        ws = wb.create_sheet("Stack Details")
        
        # Headers
        headers = ["Hostname", "IP Address", "Stack Member", "Role", "MAC Address", "Priority", "Hardware", "State"]
        ws.append(headers)
        
        # Data rows
        for result in results:
            device_info = result['device_info']
            parsed_data = result['parsed_data']
            
            hostname = device_info.get('hostname', 'Unknown')
            ip_address = device_info.get('ip_address', 'Unknown')
            
            # Get stack details
            stack_details = parsed_data.get('stack_details', [])
            if not stack_details:
                # Add a row even if no stack found
                ws.append([hostname, ip_address, 'N/A', 'Standalone', '', '', '', ''])
            else:
                for member in stack_details:
                    ws.append([
                        hostname,
                        ip_address,
                        member.get('member', 'Unknown'),
                        member.get('role', 'Unknown'),
                        member.get('mac_address', 'Unknown'),
                        member.get('priority', 'Unknown'),
                        member.get('hardware', 'Unknown'),
                        member.get('state', 'Unknown')
                    ])
        
        # Format headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D5E8D4", end_color="D5E8D4", fill_type="solid")

    def create_summary_sheet(self, wb: Workbook, summary: Dict[str, Any]):
        """Create summary sheet with proper handling of complex data types"""
        ws = wb.create_sheet("Summary")
        
        # Headers
        ws.append(["Metric", "Value"])
        
        # Process summary data safely
        for key, value in summary.items():
            # Handle different value types
            if isinstance(value, dict):
                # For dictionary values, create multiple rows
                ws.append([f"{key} (breakdown)", ""])
                for sub_key, sub_value in value.items():
                    ws.append([f"  {sub_key}", str(sub_value)])
            elif isinstance(value, list):
                # For list values, join them as a string
                ws.append([key, ", ".join(str(item) for item in value)])
            elif value is None:
                ws.append([key, "N/A"])
            else:
                # For simple values, convert to string
                ws.append([key, str(value)])
        
        # Format headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max((len(str(cell.value)) for cell in column if cell.value), default=0)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

    def create_error_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create error sheet"""
        ws = wb.create_sheet("Errors")
        
        # Headers
        ws.append(["Hostname", "IP Address", "Error Type", "Error Message"])
        
        has_errors = False
        for result in results:
            device_info = result['device_info']
            hostname = device_info.get('hostname', 'Unknown')
            ip_address = device_info.get('ip_address', 'Unknown')
            
            if errors := result.get('errors'):
                has_errors = True
                for err in errors:
                    # Handle different error formats
                    if isinstance(err, dict):
                        error_type = err.get('type', 'Unknown')
                        error_msg = err.get('message', str(err))
                    else:
                        error_type = 'General'
                        error_msg = str(err)
                    
                    ws.append([hostname, ip_address, error_type, error_msg])
        
        # If no errors found, add a note
        if not has_errors:
            ws.append(["No errors", "All devices processed successfully", "", ""])
        
        # Format headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFEBEE", end_color="FFEBEE", fill_type="solid")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = max((len(str(cell.value)) for cell in column if cell.value), default=0)
            ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)