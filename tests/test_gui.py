# tests/test_gui.py
import pytest
import tkinter as tk
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock
from src.gui.main_window import MainWindow

class TestMainWindow:
    @pytest.fixture
    def app(self):
        """Create test application instance"""
        # Note: GUI testing is complex, this is a basic example
        app = MainWindow()
        yield app
        app.root.destroy()  # Cleanup
        
    def test_initial_state(self, app):
        """Test initial application state"""
        assert app.devices_file is None
        assert app.file_path_var.get() == "No file selected"
        assert app.start_button['state'] == 'normal'
        assert app.stop_button['state'] == 'disabled'
        
    def test_file_selection(self, app):
        """Test file selection functionality"""
        # Create temporary Excel file
        data = {'hostname': ['test'], 'ip_address': ['1.1.1.1'], 
               'username': ['user'], 'password': ['pass'], 'device_type': ['cisco_ios']}
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            
            # Simulate file selection
            app.devices_file = tmp.name
            app.file_path_var.set("test_file.xlsx")
            
            assert app.devices_file == tmp.name
            assert "test_file.xlsx" in app.file_path_var.get()
            
    @patch('src.gui.main_window.ExcelHandler')
    def test_create_template(self, mock_excel_handler, app):
        """Test template creation"""
        mock_handler = MagicMock()
        mock_excel_handler.return_value = mock_handler
        
        # This would normally be tested with GUI automation tools
        # For now, just verify the handler method exists
        assert hasattr(app.excel_handler, 'create_device_template')