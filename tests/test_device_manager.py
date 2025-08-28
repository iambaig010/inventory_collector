# tests/test_device_manager.py
import pytest
import pandas as pd
import tempfile
from src.core.device_manager import DeviceManager, NetworkDevice

class TestNetworkDevice:
    def test_valid_device_creation(self):
        device = NetworkDevice(
            hostname='test-switch',
            ip_address='192.168.1.1',
            username='admin',
            password='password',
            device_type='cisco_ios'
        )
        assert device.hostname == 'test-switch'
        assert device.port == 22  # default
        
    def test_invalid_ip_address(self):
        with pytest.raises(ValueError, match="Invalid IP address"):
            NetworkDevice(
                hostname='test',
                ip_address='invalid-ip',
                username='admin',
                password='password',
                device_type='cisco_ios'
            )
            
    def test_invalid_hostname(self):
        with pytest.raises(ValueError, match="Invalid hostname"):
            NetworkDevice(
                hostname='test switch!',  # spaces and special chars
                ip_address='192.168.1.1',
                username='admin',
                password='password',
                device_type='cisco_ios'
            )

class TestDeviceManager:
    def test_load_valid_excel(self, temp_excel_file):
        manager = DeviceManager()
        devices = manager.load_from_excel(temp_excel_file)
        assert len(devices) == 1
        assert devices[0].hostname == 'test-switch'
        
    def test_load_missing_columns(self):
        # Create Excel with missing columns
        data = {'hostname': ['test']}  # Missing other required columns
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        
        manager = DeviceManager()
        with pytest.raises(ValueError, match="Missing required columns"):
            manager.load_from_excel(temp_file.name)