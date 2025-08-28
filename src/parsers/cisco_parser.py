# src/parsers/cisco_parser.py
from .base_parser import BaseParser
import re
from typing import Dict, Any, List


class CiscoParser(BaseParser):
    def get_patterns(self) -> Dict[str, str]:
        return {
           'serial_number': r'Processor board ID (\w+)',
        'model': r'cisco (\S+) \(',
        'version': r'Version (\S+)',
        'hostname': r'(\S+) uptime',
        'uptime': r'uptime is (.+?)(?=\n|\r)',
        }
        
    def parse_version(self, output: str) -> Dict[str, Any]:
        result = {}
        
        for field, pattern in self.patterns.items():
            result[field] = self.extract_with_pattern(output, pattern)
            
        return result
        
    def parse_interfaces(self, output: str) -> List[Dict[str, str]]:
        """Parse show ip interface brief output"""
        interfaces = []
        lines = output.split('\n')
        
        for line in lines:
            # Skip header lines
            if 'Interface' in line or '---' in line or not line.strip():
                continue
                
            # Parse interface line
            parts = line.split()
            if len(parts) >= 6:
                interfaces.append({
                    'name': parts[0],
                    'ip': parts[1],
                    'ok': parts[2],
                    'method': parts[3],
                    'status': parts[4],
                    'protocol': parts[5]
                })
                
        return interfaces