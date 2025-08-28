#!/usr/bin/env python3
"""
Mock SSH Server Runner
Usage: python run_mock_server.py [--port PORT] [--device-type TYPE]
"""
import argparse
import time
import signal
import sys
from tests.mock_ssh_server import start_mock_ssh_server

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down server...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Run Mock SSH Server')
    parser.add_argument('--port', '-p', type=int, default=2222, 
                       help='Port to listen on (default: 2222)')
    parser.add_argument('--device-type', '-d', type=str, default='cisco_ios',
                       choices=['cisco_ios'],
                       help='Device type to emulate (default: cisco_ios)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"Starting Mock SSH Server...")
    print(f"Device Type: {args.device_type}")
    print(f"Port: {args.port}")
    print(f"Connect with: ssh anyuser@127.0.0.1 -p {args.port}")
    print("Use any username/password combination")
    print("-" * 50)
    
    # Start server
    try:
        server = start_mock_ssh_server(port=args.port, device_type=args.device_type)
        print("✓ Server started successfully!")
        print("Press Ctrl+C to stop the server")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        if 'server' in locals():
            server.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()