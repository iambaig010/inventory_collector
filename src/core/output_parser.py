# src/core/output_parser.py
import logging
from typing import Dict, Any, Optional
from ..parsers.cisco_parser import CiscoParser
from ..parsers.base_parser import BaseParser

class OutputParser:
    def __init__(self):
        self.parsers = {
            'cisco_ios': CiscoParser(),
            'cisco_xe': CiscoParser(),  # Same as IOS for now
            'cisco_asa': CiscoParser(),
            # Add more parsers as needed
        }
        self.logger = logging.getLogger(__name__)
        
    def parse_device_output(self, device_type: str, raw_output: Dict[str, str]) -> Dict[str, Any]:
        """Parse raw command output using appropriate vendor parser"""
        parser = self.parsers.get(device_type)
        
        if not parser:
            self.logger.warning(f"No parser found for device type: {device_type}")
            return self.generic_parse(raw_output, device_type)
            
        try:
            self.logger.debug(f"Parsing output using {device_type} parser")
            return parser.parse_all(raw_output)
        except Exception as e:
            self.logger.error(f"Parser failed for {device_type}: {str(e)}")
            return self.generic_parse(raw_output, device_type)
    
    def generic_parse(self, raw_output: Dict[str, str], device_type: str) -> Dict[str, Any]:
        """Fallback parser for unsupported vendors"""
        self.logger.info(f"Using generic parser for {device_type}")
        
        # Try to extract basic info from any version command
        version_output = raw_output.get('version', '')
        
        return {
            'serial_number': 'Unknown',
            'model': 'Unknown',
            'version': 'Unknown',
            'hostname': 'Unknown',
            'interfaces': [],
            'uptime': 'Unknown',
            'device_type': device_type,
            'parsed_with': 'generic_parser',
            'raw_available': list(raw_output.keys())
        }
        
    def get_supported_device_types(self) -> list:
        """Return list of supported device types"""
        return list(self.parsers.keys())
        
    def add_parser(self, device_type: str, parser: BaseParser):
        """Add or replace parser for device type"""
        self.parsers[device_type] = parser
        self.logger.info(f"Added parser for device type: {device_type}")