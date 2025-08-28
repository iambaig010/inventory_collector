# tests/test_parsers.py
import pytest
from src.parsers.cisco_parser import CiscoParser

class TestCiscoParser:
    @pytest.fixture
    def parser(self):
        return CiscoParser()
        
    def test_parse_version(self, parser, sample_cisco_output):
        result = parser.parse_version(sample_cisco_output)
        
        assert result['serial_number'] == 'FOC1932X0K1'
        assert result['model'] == 'WS-C2960X-24TS-L'
        assert result['version'] == '15.2(4)E10'
        assert result['hostname'] == 'test-switch'
        
    def test_parse_malformed_output(self, parser):
        malformed = "This is not valid switch output"
        result = parser.parse_version(malformed)
        
        # Should gracefully handle bad input
        assert result['serial_number'] == 'Unknown'
        assert result['model'] == 'Unknown'
        
    def test_parse_interfaces(self, parser):
        interface_output = """
        Interface                  IP-Address      OK? Method Status                Protocol
        GigabitEthernet0/1         unassigned      YES unset  up                    up      
        GigabitEthernet0/2         192.168.1.10    YES manual up                    up      
        Vlan1                      192.168.1.1     YES NVRAM  up                    up      
        """
        
        interfaces = parser.parse_interfaces(interface_output)
        assert len(interfaces) == 3
        assert interfaces[0]['name'] == 'GigabitEthernet0/1'
        assert interfaces[1]['ip'] == '192.168.1.10'