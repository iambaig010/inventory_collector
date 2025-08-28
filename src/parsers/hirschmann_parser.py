#!/usr/bin/env python3
"""
Hirschmann HiOS Parser - Professional implementation with comprehensive error handling
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

@dataclass
class InterfaceInfo:
    """Structured interface information"""
    name: str
    status: str = "unknown"
    admin_status: str = "unknown"
    description: str = ""
    speed: str = ""
    duplex: str = ""
    vlan: str = ""
    type: str = ""

@dataclass
class MacEntry:
    """Structured MAC table entry"""
    mac_address: str
    vlan: str
    interface: str
    type: str = "dynamic"
    age: str = ""

@dataclass
class DeviceInfo:
    """Structured device information"""
    hostname: str = ""
    model: str = ""
    serial: str = ""
    version: str = ""
    uptime: str = ""
    base_mac: str = ""

class BaseHirschmannParser(ABC):
    """Base class for Hirschmann parsers with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse command output"""
        pass
    
    def _clean_output(self, output: str) -> str:
        """Clean and normalize output"""
        if not output:
            return ""
        
        # Remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', output)
        
        # Normalize line endings
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace but preserve structure
        lines = [line.rstrip() for line in cleaned.split('\n')]
        return '\n'.join(lines)
    
    def _extract_with_regex(self, output: str, pattern: str, group: int = 1, 
                           flags: int = re.IGNORECASE | re.MULTILINE) -> str:
        """Extract data using regex with error handling"""
        try:
            match = re.search(pattern, output, flags)
            if match and len(match.groups()) >= group:
                return match.group(group).strip()
        except Exception as e:
            self.logger.warning(f"Regex extraction failed for pattern '{pattern}': {e}")
        return ""

class HirschmannVersionParser(BaseHirschmannParser):
    """Parser for 'show version' command output"""
    
    # Comprehensive regex patterns for different HiOS versions
    PATTERNS = {
        'version': [
            r'Software Version\s*:\s*([^\r\n]+)',
            r'SW Version\s*:\s*([^\r\n]+)',
            r'Version\s*:\s*([^\r\n]+)',
            r'HiOS\s+Version\s*:\s*([^\r\n]+)'
        ],
        'model': [
            r'Product\s*:\s*([^\r\n]+)',
            r'Hardware\s*:\s*([^\r\n]+)',
            r'Model\s*:\s*([^\r\n]+)',
            r'Device Type\s*:\s*([^\r\n]+)'
        ],
        'serial': [
            r'Serial Number\s*:\s*(\S+)',
            r'S/N\s*:\s*(\S+)',
            r'Serial\s*:\s*(\S+)'
        ],
        'base_mac': [
            r'Base MAC Address\s*:\s*([0-9a-fA-F:.-]+)',
            r'MAC Address\s*:\s*([0-9a-fA-F:.-]+)',
            r'System MAC\s*:\s*([0-9a-fA-F:.-]+)'
        ]
    }
    
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse show version output"""
        cleaned_output = self._clean_output(output)
        result = {
            'version': '',
            'model': '',
            'serial': '',
            'base_mac': '',
            'raw_output': output
        }
        
        # Try multiple patterns for each field for maximum compatibility
        for field, patterns in self.PATTERNS.items():
            for pattern in patterns:
                value = self._extract_with_regex(cleaned_output, pattern)
                if value:
                    result[field] = value
                    self.logger.debug(f"Found {field}: {value}")
                    break
        
        # Additional parsing for specific formats
        self._parse_additional_info(cleaned_output, result)
        
        return result
    
    def _parse_additional_info(self, output: str, result: Dict[str, Any]):
        """Parse additional information from version output"""
        # Try to extract build date/time
        build_date = self._extract_with_regex(output, r'Build Date\s*:\s*([^\r\n]+)')
        if build_date:
            result['build_date'] = build_date
        
        # Try to extract firmware revision
        fw_revision = self._extract_with_regex(output, r'Firmware Revision\s*:\s*([^\r\n]+)')
        if fw_revision:
            result['firmware_revision'] = fw_revision

class HirschmannSystemParser(BaseHirschmannParser):
    """Parser for 'show system information' command output"""
    
    PATTERNS = {
        'hostname': [
            r'System Name\s*:\s*([^\r\n]+)',
            r'Hostname\s*:\s*([^\r\n]+)',
            r'Device Name\s*:\s*([^\r\n]+)'
        ],
        'uptime': [
            r'System Up Time\s*:\s*([^\r\n]+)',
            r'Uptime\s*:\s*([^\r\n]+)',
            r'Up Time\s*:\s*([^\r\n]+)'
        ]
    }
    
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse show system information output"""
        cleaned_output = self._clean_output(output)
        result = {
            'hostname': '',
            'uptime': '',
            'raw_output': output
        }
        
        for field, patterns in self.PATTERNS.items():
            for pattern in patterns:
                value = self._extract_with_regex(cleaned_output, pattern)
                if value:
                    result[field] = value
                    break
        
        return result

class HirschmannInterfaceParser(BaseHirschmannParser):
    """Parser for 'show interfaces brief' command output"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse show interfaces brief output"""
        cleaned_output = self._clean_output(output)
        interfaces = []
        
        # Split into lines and find the table
        lines = cleaned_output.split('\n')
        
        # Find header line (usually contains "Interface", "Status", etc.)
        header_idx = self._find_table_header(lines, ['interface', 'port', 'status'])
        
        if header_idx == -1:
            self.logger.warning("Could not find interface table header")
            return {'interfaces': [], 'raw_output': output}
        
        # Parse header to understand column positions
        header_line = lines[header_idx]
        columns = self._parse_header_columns(header_line)
        
        # Parse data rows
        for i in range(header_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue
            
            interface = self._parse_interface_line(line, columns)
            if interface:
                interfaces.append(asdict(interface))
        
        return {
            'interfaces': interfaces,
            'interface_count': len(interfaces),
            'raw_output': output
        }
    
    def _find_table_header(self, lines: List[str], keywords: List[str]) -> int:
        """Find the header line of the interface table"""
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                return i
        return -1
    
    def _parse_header_columns(self, header_line: str) -> Dict[str, int]:
        """Parse header line to determine column positions"""
        columns = {}
        header_lower = header_line.lower()
        
        # Common column mappings
        column_mappings = {
            'interface': ['interface', 'port', 'if'],
            'status': ['status', 'state'],
            'admin': ['admin', 'enabled'],
            'speed': ['speed', 'rate'],
            'duplex': ['duplex', 'dup'],
            'vlan': ['vlan', 'vid'],
            'description': ['description', 'desc', 'name']
        }
        
        for standard_name, variations in column_mappings.items():
            for variation in variations:
                pos = header_lower.find(variation)
                if pos != -1:
                    columns[standard_name] = pos
                    break
        
        return columns
    
    def _parse_interface_line(self, line: str, columns: Dict[str, int]) -> Optional[InterfaceInfo]:
        """Parse a single interface data line"""
        try:
            # Split on whitespace for basic parsing
            fields = line.split()
            if len(fields) < 2:
                return None
            
            interface = InterfaceInfo(name=fields[0])
            
            # Map fields based on common patterns
            if len(fields) >= 2:
                interface.status = fields[1] if fields[1].lower() in ['up', 'down', 'admin-down', 'testing'] else 'unknown'
            
            if len(fields) >= 3:
                # Could be admin status, speed, or vlan depending on format
                if fields[2].lower() in ['up', 'down', 'enabled', 'disabled']:
                    interface.admin_status = fields[2]
                elif fields[2].isdigit():
                    interface.vlan = fields[2]
                else:
                    interface.speed = fields[2]
            
            # Try to extract more fields based on position
            if len(fields) >= 4:
                interface.duplex = fields[3] if 'full' in fields[3].lower() or 'half' in fields[3].lower() else interface.duplex
            
            return interface
            
        except Exception as e:
            self.logger.warning(f"Failed to parse interface line '{line}': {e}")
            return None

class HirschmannMacTableParser(BaseHirschmannParser):
    """Parser for 'show mac-address-table' command output"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse MAC address table output"""
        cleaned_output = self._clean_output(output)
        mac_entries = []
        
        lines = cleaned_output.split('\n')
        
        # Find MAC table header
        header_idx = self._find_table_header(lines, ['mac', 'address', 'vlan', 'port'])
        
        if header_idx == -1:
            self.logger.warning("Could not find MAC table header")
            return {'mac_entries': [], 'raw_output': output}
        
        # Parse MAC entries
        for i in range(header_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('-') or line.startswith('='):
                continue
            
            mac_entry = self._parse_mac_line(line)
            if mac_entry:
                mac_entries.append(asdict(mac_entry))
        
        return {
            'mac_entries': mac_entries,
            'total_entries': len(mac_entries),
            'raw_output': output
        }
    
    def _find_table_header(self, lines: List[str], keywords: List[str]) -> int:
        """Find MAC table header line"""
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                return i
        return -1
    
    def _parse_mac_line(self, line: str) -> Optional[MacEntry]:
        """Parse a single MAC table entry line"""
        try:
            fields = line.split()
            if len(fields) < 3:
                return None
            
            # Look for MAC address pattern
            mac_pattern = r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}'
            mac_match = re.search(mac_pattern, line)
            
            if not mac_match:
                return None
            
            mac_address = mac_match.group(0)
            
            # Extract other fields
            vlan = ""
            interface = ""
            entry_type = "dynamic"
            
            # Find VLAN (usually a number)
            for field in fields:
                if field.isdigit() and 1 <= int(field) <= 4094:
                    vlan = field
                    break
            
            # Find interface (usually contains numbers/letters like Gi0/1, Port1, etc.)
            interface_pattern = r'[A-Za-z]+\d+[/\d]*|Port\d+|Ethernet\d+'
            for field in fields:
                if re.match(interface_pattern, field, re.IGNORECASE):
                    interface = field
                    break
            
            # Determine entry type
            if any(word in line.lower() for word in ['static', 'permanent']):
                entry_type = "static"
            
            return MacEntry(
                mac_address=mac_address,
                vlan=vlan,
                interface=interface,
                type=entry_type
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse MAC line '{line}': {e}")
            return None

class HirschmannParser:
    """Main Hirschmann parser that coordinates all sub-parsers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsers = {
            'show_version': HirschmannVersionParser(),
            'show_system_information': HirschmannSystemParser(),
            'show_interfaces_brief': HirschmannInterfaceParser(),
            'show_mac_address_table': HirschmannMacTableParser()
        }
    
    def parse_command_output(self, command_name: str, output: str) -> Dict[str, Any]:
        """Parse output for a specific command"""
        parser = self.parsers.get(command_name)
        
        if not parser:
            self.logger.warning(f"No parser available for command: {command_name}")
            return {'raw_output': output, 'parsed': False}
        
        try:
            result = parser.parse(output)
            result['parsed'] = True
            result['command'] = command_name
            return result
        except Exception as e:
            self.logger.error(f"Parsing failed for {command_name}: {e}")
            return {
                'raw_output': output,
                'parsed': False,
                'error': str(e),
                'command': command_name
            }
    
    def parse_device_inventory(self, command_outputs: Dict[str, str]) -> DeviceInfo:
        """Parse complete device inventory from multiple command outputs"""
        device_info = DeviceInfo()
        
        # Parse version information
        if 'show_version' in command_outputs:
            version_data = self.parse_command_output('show_version', command_outputs['show_version'])
            device_info.model = version_data.get('model', '')
            device_info.serial = version_data.get('serial', '')
            device_info.version = version_data.get('version', '')
            device_info.base_mac = version_data.get('base_mac', '')
        
        # Parse system information
        if 'show_system_information' in command_outputs:
            system_data = self.parse_command_output('show_system_information', command_outputs['show_system_information'])
            device_info.hostname = system_data.get('hostname', '')
            device_info.uptime = system_data.get('uptime', '')
        
        return device_info

# Register the parser with the main output parser system
def register_hirschmann_parser():
    """Register Hirschmann parser with the main parser system"""
    try:
        from src.parsers.output_parser import OutputParser
        parser_instance = HirschmannParser()
        OutputParser.parsers['hirschmann_hios'] = parser_instance
        logging.getLogger(__name__).info("Hirschmann parser registered successfully")
    except ImportError:
        logging.getLogger(__name__).warning("Could not register Hirschmann parser - OutputParser not found")

# Auto-register when module is imported
register_hirschmann_parser()