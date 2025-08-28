import pandas as pd
import ipaddress
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class NetworkDevice:
    """Represents a network device"""
    
    def __init__(self, hostname, ip_address, username, password, device_type, 
                 port=22, location='', description=''):
        self.hostname = self._validate_hostname(hostname)
        self.ip_address = self._validate_ip_address(ip_address)
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = int(port) if port else 22
        self.location = location or ''
        self.description = description or ''
    
    def _validate_hostname(self, hostname):
        """Validate hostname format"""
        if not hostname or not isinstance(hostname, str):
            raise ValueError("Hostname must be a non-empty string")
        
        if len(hostname) > 253:
            raise ValueError("Hostname too long")
        
        if not re.match(r'^[a-zA-Z0-9-._]+$', hostname):
            raise ValueError(f"Invalid hostname format: {hostname}")
        
        return hostname
    
    def _validate_ip_address(self, ip_address):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return ip_address
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip_address}")
    
    def __str__(self):
        return f"NetworkDevice({self.hostname}, {self.ip_address}, {self.device_type})"

class DeviceManager:
    """Manages network devices"""
    
    def __init__(self):
        self.devices = []
    
    def add_device(self, device):
        """Add a device"""
        if not isinstance(device, NetworkDevice):
            raise ValueError("Device must be a NetworkDevice instance")
        self.devices.append(device)
    
    def load_devices_from_excel(self, excel_file):
        """Load devices from Excel file"""
        try:
            if not Path(excel_file).exists():
                raise FileNotFoundError(f"Excel file not found: {excel_file}")
            
            df = pd.read_excel(excel_file)
            
            if df.empty:
                raise ValueError("Excel file is empty")
            
            # Check required columns
            required_columns = ['hostname', 'ip_address', 'username', 'password', 'device_type']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Clear existing devices and load new ones
            self.devices = []
            loaded_devices = []
            
            for index, row in df.iterrows():
                try:
                    device = NetworkDevice(
                        hostname=row['hostname'],
                        ip_address=row['ip_address'],
                        username=row['username'],
                        password=row['password'],
                        device_type=row['device_type'],
                        port=row.get('port', 22),
                        location=row.get('location', ''),
                        description=row.get('description', '')
                    )
                    loaded_devices.append(device)
                    self.add_device(device)
                except Exception as e:
                    logger.warning(f"Error loading device at row {index + 2}: {e}")
            
            logger.info(f"Loaded {len(loaded_devices)} devices from {excel_file}")
            return loaded_devices
            
        except Exception as e:
            logger.error(f"Error loading devices from Excel: {e}")
            raise
    
    def get_device_by_hostname(self, hostname):
        """Get device by hostname"""
        for device in self.devices:
            if device.hostname == hostname:
                return device
        return None
    
    def get_devices_by_type(self, device_type):
        """Get devices by type"""
        return [device for device in self.devices if device.device_type == device_type]
