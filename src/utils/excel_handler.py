# src/utils/excel_handler.py
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from datetime import datetime
import logging
from typing import List, Dict, Any

class ExcelHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def generate_report(self, inventory_results: List[Dict[str, Any]], 
                       output_path: str, summary: Dict[str, Any] = None):
        """Generate comprehensive Excel report"""
        
        self.logger.info(f"Generating Excel report: {output_path}")
        
        # Create workbook
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create data sheet
        self.create_inventory_sheet(wb, inventory_results)
        
        # Create summary sheet
        if summary:
            self.create_summary_sheet(wb, summary)
            
        # Create error report sheet
        self.create_error_sheet(wb, inventory_results)
        
        # Save workbook
        wb.save(output_path)
        self.logger.info(f"Excel report saved: {output_path}")
        
    def create_inventory_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create main inventory data sheet"""
        ws = wb.create_sheet("Device Inventory", 0)
        
        # Prepare data for DataFrame
        rows = []
        for result in results:
            device_info = result['device_info']
            parsed_data = result['parsed_data']
            
            row = {
                'Hostname': device_info.get('hostname', 'Unknown'),
                'IP Address': device_info.get('ip_address', 'Unknown'),
                'Device Type': device_info.get('device_type', 'Unknown'),
                'Model': parsed_data.get('model', 'Unknown'),
                'Serial Number': parsed_data.get('serial_number', 'Unknown'),
                'Software Version': parsed_data.get('version', 'Unknown'),
                'Uptime': parsed_data.get('uptime', 'Unknown'),
                'Connection Status': device_info.get('connection_status', 'Unknown'),
                'Interface Count': len(parsed_data.get('interfaces', [])),
                'Has Errors': 'Yes' if result.get('errors') else 'No',
                'Collection Time': result.get('collection_time', 'Unknown')
            }
            rows.append(row)
            
        # Create DataFrame and add to worksheet
        df = pd.DataFrame(rows)
        
        # Add headers
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
            
        # Apply formatting
        self.format_inventory_sheet(ws, len(rows))
        
    def format_inventory_sheet(self, ws, data_rows: int):
        """Apply formatting to inventory sheet"""
        
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Apply header formatting
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            
        # Column widths
        column_widths = {
            'A': 20,  # Hostname
            'B': 15,  # IP Address
            'C': 15,  # Device Type
            'D': 25,  # Model
            'E': 20,  # Serial Number
            'F': 15,  # Software Version
            'G': 20,  # Uptime
            'H': 15,  # Connection Status
            'I': 12,  # Interface Count
            'J': 10,  # Has Errors
            'K': 20   # Collection Time
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
            
        # Add borders and alternating colors
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        
        alternate_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        
        for row in range(1, data_rows + 2):  # +1 for header, +1 for range
            for col in range(1, 12):  # 11 columns
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
                
                # Alternating row colors (skip header)
                if row > 1 and row % 2 == 0:
                    cell.fill = alternate_fill
                    
        # Status-based conditional formatting
        for row in range(2, data_rows + 2):  # Skip header
            status_cell = ws.cell(row=row, column=8)  # Connection Status column
            error_cell = ws.cell(row=row, column=10)   # Has Errors column
            
            # Color code connection status
            if status_cell.value == 'success':
                status_cell.fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
            elif status_cell.value == 'failed':
                status_cell.fill = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
                
            # Color code error status
            if error_cell.value == 'Yes':
                error_cell.fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
                
        # Freeze header row
        ws.freeze_panes = "A2"
        
        # Create table for better formatting
        table_ref = f"A1:K{data_rows + 1}"
        table = Table(displayName="DeviceInventory", ref=table_ref)
        style = TableStyleInfo(
            name="TableStyleMedium9", showFirstColumn=False,
            showLastColumn=False, showRowStripes=True, showColumnStripes=True
        )
        table.tableStyleInfo = style
        ws.add_table(table)
        
    def create_summary_sheet(self, wb: Workbook, summary: Dict[str, Any]):
        """Create summary statistics sheet"""
        ws = wb.create_sheet("Summary")
        
        # Collection Summary
        ws.append(["Collection Summary"])
        ws.append(["Total Devices", summary['total_devices']])
        ws.append(["Successful", summary['successful']])
        ws.append(["Failed", summary['failed']])
        ws.append(["Success Rate", f"{summary['success_rate']:.1f}%"])
        ws.append(["Collection Time", summary['collection_time']])
        ws.append([])  # Empty row
        
        # Device Types
        ws.append(["Device Types"])
        for device_type, count in summary['device_types'].items():
            ws.append([device_type, count])
        ws.append([])  # Empty row
        
        # Status Breakdown
        ws.append(["Status Breakdown"])
        for status, count in summary['status_counts'].items():
            ws.append([status, count])
            
        # Format summary sheet
        self.format_summary_sheet(ws)
        
    def format_summary_sheet(self, ws):
        """Format summary sheet"""
        # Make headers bold
        for row in ws.iter_rows():
            for cell in row:
                if cell.column == 1 and cell.value in ['Collection Summary', 'Device Types', 'Status Breakdown']:
                    cell.font = Font(bold=True, size=14)
                    
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2
            
    def create_error_sheet(self, wb: Workbook, results: List[Dict[str, Any]]):
        """Create sheet with detailed error information"""
        ws = wb.create_sheet("Errors")
        
        # Headers
        ws.append(["Hostname", "IP Address", "Error Type", "Error Message", "Timestamp"])
        
        # Collect all errors
        for result in results:
            device_info = result['device_info']
            errors = result.get('errors', [])
            
            if errors:
                for error in errors:
                    ws.append([
                        device_info.get('hostname', 'Unknown'),
                        device_info.get('ip_address', 'Unknown'),
                        "Connection/Command Error",
                        error,
                        result.get('collection_time', 'Unknown')
                    ])
            elif device_info.get('connection_status') == 'failed':
                # Add row for failed devices even without specific error messages
                ws.append([
                    device_info.get('hostname', 'Unknown'),
                    device_info.get('ip_address', 'Unknown'),
                    "Connection Failure",
                    "Device connection failed",
                    result.get('collection_time', 'Unknown')
                ])
                
        # Format error sheet
        self.format_error_sheet(ws)
        
    def format_error_sheet(self, ws):
        """Format error sheet"""
        if ws.max_row <= 1:  # Only header row
            ws.append(["No errors encountered during collection"])
            return
            
        # Header formatting
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
            
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)  # Cap at 50
            
    def create_device_template(self, output_path: str):
        """Create Excel template for device input"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Device List"
        
        # Headers
        headers = [
            "hostname", "ip_address", "username", "password", 
            "device_type", "port", "location", "description"
        ]
        ws.append(headers)
        
        # Sample data
        sample_data = [
            ["CORP-CORE-SW01", "192.168.1.1", "netadmin", "password123", "cisco_ios", 22, "Data Center", "Core Switch"],
            ["CORP-ACCESS-SW02", "192.168.1.2", "netadmin", "password123", "cisco_ios", 22, "Floor 2 IDF", "Access Switch"],
            ["HP-EDGE-SW01", "192.168.1.3", "admin", "password123", "hp_procurve", 22, "Floor 1 IDF", "Edge Switch"]
        ]
        
        for row in sample_data:
            ws.append(row)
            
        # Format template
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
            
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column_letter].width = max_length + 2
            
        # Add instructions sheet
        instructions_ws = wb.create_sheet("Instructions")
        instructions = [
            "Device List Template Instructions",
            "",
            "Required Columns:",
            "- hostname: Device hostname or name",
            "- ip_address: IP address to connect to",
            "- username: SSH username",
            "- password: SSH password", 
            "- device_type: Type (cisco_ios, hp_procurve, etc.)",
            "",
            "Optional Columns:",
            "- port: SSH port (default: 22)",
            "- location: Physical location",
            "- description: Device description",
            "",
            "Supported Device Types:",
            "- cisco_ios: Cisco IOS switches/routers",
            "- cisco_xe: Cisco IOS XE devices",
            "- hp_procurve: HP ProCurve switches",
            "",
            "Notes:",
            "- Remove sample data before using",
            "- Ensure all required fields are filled",
            "- Test with a few devices first"
        ]
        
        for instruction in instructions:
            instructions_ws.append([instruction])
            
        wb.save(output_path)