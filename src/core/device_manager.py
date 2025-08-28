# src/core/device_manager.py
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import ipaddress
import re

@dataclass
class NetworkDevice:
    hostname: str
    ip_address: str
    username: str
    password: str
    device_type: str
    port: int = 22
    
    def __post_init__(self):
        self.validate()
        
    def validate(self):
        """Validate device data"""
        # Validate IP address
        try:
            ipaddress.ip_address(self.ip_address)
        except ValueError:
            raise ValueError(f"Invalid IP address: {self.ip_address}")
            
        # Validate hostname
        if not re.match(r'^[a-zA-Z0-9-_.]+$', self.hostname):
            raise ValueError(f"Invalid hostname: {self.hostname}")
            
        # Check required fields
        if not all([self.username, self.password, self.device_type]):
            raise ValueError("Username, password, and device_type are required")
            
        # Validate port
        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}")

class DeviceManager:
    def __init__(self):
        self.devices: List[NetworkDevice] = []
        
    def load_from_excel(self, file_path: str) -> List[NetworkDevice]:
        """Load devices from Excel with comprehensive validation"""
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise Exception(f"Cannot read Excel file: {str(e)}")
            
        # Check required columns
        required_cols = {'hostname', 'ip_address', 'username', 'password', 'device_type'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
            
        # Validate data
        devices = []
        errors = []
        
        for idx, row in df.iterrows():
            try:
                device = NetworkDevice(
                    hostname=str(row['hostname']).strip(),
                    ip_address=str(row['ip_address']).strip(),
                    username=str(row['username']).strip(),
                    password=str(row['password']).strip(),
                    device_type=str(row['device_type']).strip(),
                    port=int(row.get('port', 22))
                )
                devices.append(device)
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                
        if errors:
            raise ValueError("Validation errors:\n" + "\n".join(errors))
            
        self.devices = devices
        return devices