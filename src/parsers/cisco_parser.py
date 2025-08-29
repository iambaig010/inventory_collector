#!/usr/bin/env python3
"""
Enhanced Cisco Parser with comprehensive hardware and interface inventory support
"""
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
            'base_mac': r'Base ethernet MAC Address\s*:\s*([0-9a-fA-F:.-]+)',
            'system_serial': r'System Serial Number\s*:\s*(\S+)',
            'chassis_serial': r'Chassis Serial Number\s*:\s*(\S+)'
        }
        
    def parse_version(self, output: str) -> Dict[str, Any]:
        """Enhanced version parsing"""
        result = {}
        
        for field, pattern in self.patterns.items():
            result[field] = self.extract_with_pattern(output, pattern)
        
        # Additional version info for certain Cisco models
        ios_version = self.extract_with_pattern(output, r'Cisco IOS Software.*Version (\S+)', 'Unknown')
        if ios_version != 'Unknown':
            result['ios_version'] = ios_version
            
        system_image = self.extract_with_pattern(output, r'System image file is "([^"]+)"', 'Unknown')
        if system_image != 'Unknown':
            result['system_image'] = system_image
            
        return result
        
    def parse_inventory(self, output: str) -> Dict[str, Any]:
        """Parse show inventory output for hardware details"""
        hardware_modules = []
        lines = output.split('\n')
        current_module = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_module:
                    hardware_modules.append(current_module.copy())
                    current_module = {}
                continue
            
            name_match = re.match(r'NAME:\s*"([^"]*)"', line)
            if name_match:
                if current_module:
                    hardware_modules.append(current_module.copy())
                current_module = {'name': name_match.group(1)}
                continue
            
            descr_match = re.match(r'DESCR:\s*"([^"]*)"', line)
            if descr_match:
                current_module['description'] = descr_match.group(1)
                continue
            
            pid_match = re.match(r'PID:\s*(\S+)', line)
            if pid_match:
                current_module['product_id'] = pid_match.group(1)
                continue
            
            vid_match = re.match(r'VID:\s*(\S+)', line)
            if vid_match:
                current_module['version_id'] = vid_match.group(1)
                continue
            
            sn_match = re.match(r'SN:\s*(\S+)', line)
            if sn_match:
                current_module['serial_number'] = sn_match.group(1)
                continue
        
        if current_module:
            hardware_modules.append(current_module)
        
        return {
            'hardware_modules': hardware_modules,
            'total_modules': len(hardware_modules)
        }
    
    def parse_platform(self, output: str) -> Dict[str, Any]:
        """Parse show platform output for stack info"""
        switches = []
        lines = output.split('\n')
        
        for line in lines:
            switch_match = re.match(r'(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
            if switch_match:
                switches.append({
                    'switch_number': switch_match.group(1),
                    'type': switch_match.group(2),
                    'hw_version': switch_match.group(3),
                    'sw_version': switch_match.group(4),
                    'status': switch_match.group(5)
                })
        
        return {
            'stack_switches': switches,
            'stack_count': len(switches)
        }
    
    def parse_switch_detail(self, output: str) -> Dict[str, Any]:
        """Parse show switch detail for stack member details"""
        stack_details = []
        current_switch = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            switch_match = re.match(r'Switch/Stack (\d+)', line)
            if switch_match:
                if current_switch:
                    stack_details.append(current_switch.copy())
                current_switch = {'switch_number': switch_match.group(1)}
                continue
            
            mac_match = re.search(r'MAC Address\s*:\s*([0-9a-fA-F:.]+)', line)
            if mac_match:
                current_switch['mac_address'] = mac_match.group(1)
                continue
            
            model_match = re.search(r'Model\s*:\s*(\S+)', line)
            if model_match:
                current_switch['model'] = model_match.group(1)
                continue
            
            serial_match = re.search(r'Serial Number\s*:\s*(\S+)', line)
            if serial_match:
                current_switch['serial_number'] = serial_match.group(1)
                continue
        
        if current_switch:
            stack_details.append(current_switch)
        
        return {'stack_details': stack_details}
    
    def parse_modules(self, output: str) -> Dict[str, Any]:
        """Parse show module output"""
        modules = []
        lines = output.split('\n')
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 4 and parts[0].isdigit():
                modules.append({
                    'module_number': parts[0],
                    'ports': parts[1],
                    'card_type': ' '.join(parts[2:-2]) if len(parts) > 4 else parts[2],
                    'model': parts[-2] if len(parts) > 3 else '',
                    'serial': parts[-1] if len(parts) > 3 else ''
                })
        
        return {
            'modules': modules,
            'module_count': len(modules)
        }
    
    def parse_interfaces(self, output: str) -> List[Dict[str, str]]:
        """Parse show ip interface brief output"""
        interfaces = []
        lines = output.split('\n')
        
        for line in lines:
            if 'Interface' in line or '---' in line or not line.strip():
                continue
                
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
    
    def parse_all(self, raw_output: Dict[str, str]) -> Dict[str, Any]:
        """Parse all command outputs"""
        result = {
            'serial_number': 'Unknown',
            'model': 'Unknown',
            'version': 'Unknown',
            'hostname': 'Unknown',
            'interfaces': [],
            'uptime': 'Unknown',
            'base_mac': 'Unknown',
            'hardware_modules': [],
            'stack_info': {},
            'power_info': {}
        }
        
        if 'version' in raw_output:
            result.update(self.parse_version(raw_output['version']))
        
        if 'inventory' in raw_output:
            result.update(self.parse_inventory(raw_output['inventory']))
        
        if 'platform' in raw_output:
            result.update(self.parse_platform(raw_output['platform']))
        
        if 'switch_detail' in raw_output:
            result.update(self.parse_switch_detail(raw_output['switch_detail']))
        
        if 'modules' in raw_output:
            result.update(self.parse_modules(raw_output['modules']))
        
        if 'interfaces' in raw_output:
            result['interfaces'] = self.parse_interfaces(raw_output['interfaces'])
        
        return result
