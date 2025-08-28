# tests/test_inventory_collector.py
import pytest
import tempfile
import pandas as pd
from src.core.inventory_collector import InventoryCollector

class TestInventoryCollector:
    @pytest.fixture
    def collector(self):
        return InventoryCollector()
        
    @pytest.fixture
    def devices_excel_file(self, mock_cisco_server):
        """Create Excel file with mock server devices"""
        host, port = mock_cisco_server
        
        data = [{
            'hostname': f'test-switch-{i}',
            'ip_address': host,
            'username': 'testuser',
            'password': 'testpass',
            'device_type': 'cisco_ios',
            'port': port
        } for i in range(2)]
        
        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        return temp_file.name
        
    def test_complete_workflow(self, collector, devices_excel_file):
        """Test end-to-end inventory collection"""
        progress_calls = []
        error_calls = []
        
        def progress_callback(phase, total, current, message):
            progress_calls.append((phase, total, current, message))
            
        def error_callback(error_type, message):
            error_calls.append((error_type, message))
            
        # Run complete collection
        results = collector.collect_inventory(
            devices_excel_file,
            progress_callback=progress_callback,
            error_callback=error_callback
        )
        
        # Verify results
        assert len(results) == 2
        assert len(error_calls) == 0  # No errors
        assert len(progress_calls) > 0  # Progress was reported
        
        # Verify data structure
        for result in results:
            assert 'device_info' in result
            assert 'parsed_data' in result
            assert 'errors' in result
            assert 'collection_time' in result
            
            # Verify parsed data
            assert result['parsed_data']['serial_number'] == 'FOC1932X0K1'
            assert 'Cisco' in result['parsed_data']['model']
            
    def test_collection_summary(self, collector):
        """Test summary generation"""
        mock_results = [
            {
                'device_info': {'connection_status': 'success', 'device_type': 'cisco_ios'},
                'parsed_data': {},
                'errors': []
            },
            {
                'device_info': {'connection_status': 'failed', 'device_type': 'cisco_ios'},
                'parsed_data': {},
                'errors': ['Connection timeout']
            }
        ]
        
        summary = collector.get_collection_summary(mock_results)
        
        assert summary['total_devices'] == 2
        assert summary['successful'] == 1
        assert summary['failed'] == 1
        assert summary['success_rate'] == 50.0
        assert summary['device_types']['cisco_ios'] == 2