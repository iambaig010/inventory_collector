# src/parsers/base_parser.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import re

class BaseParser(ABC):
    """Base class for all vendor parsers"""
    
    def __init__(self):
        self.patterns = self.get_patterns()
        
    @abstractmethod
    def get_patterns(self) -> Dict[str, str]:
        """Return regex patterns for this vendor"""
        pass
        
    @abstractmethod
    def parse_version(self, output: str) -> Dict[str, Any]:
        """Parse version command output"""
        pass
        
    def parse_all(self, raw_output: Dict[str, str]) -> Dict[str, Any]:
        """Parse all command outputs"""
        result = {
            'serial_number': 'Unknown',
            'model': 'Unknown',
            'version': 'Unknown',
            'hostname': 'Unknown',
            'interfaces': [],
            'uptime': 'Unknown'
        }
        
        if 'version' in raw_output:
            version_data = self.parse_version(raw_output['version'])
            result.update(version_data)
            
        return result
        
    def extract_with_pattern(self, text: str, pattern: str, default: str = 'Unknown') -> str:
        """Helper method to extract data using regex"""
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else default

