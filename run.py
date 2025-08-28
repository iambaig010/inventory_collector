#!/usr/bin/env python3
"""
Network Inventory Tool Launcher
Run with: python run.py
"""

import sys
import os
import logging
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def setup_logging():
    """Setup application logging"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'inventory_tool.log'),
            logging.StreamHandler()
        ]
    )

def run_gui():
    """Run the GUI version"""
    try:
        from gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    except ImportError as e:
        print(f"GUI not available: {e}")
        print("Please install tkinter or run in CLI mode")

def run_cli():
    """Run the CLI version"""
    from main import main
    return main()

if __name__ == "__main__":
    setup_logging()
    
    # Create output directory
    (project_root / 'output').mkdir(exist_ok=True)
    
    print("Network Inventory Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        print("Running in CLI mode...")
        sys.exit(run_cli())
    else:
        print("Starting GUI...")
        run_gui()