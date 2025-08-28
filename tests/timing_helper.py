
import time
import socket
import threading
from contextlib import contextmanager

@contextmanager
def wait_for_server(host='127.0.0.1', port=2222, timeout=10):
    """Context manager that waits for server to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                yield True
                return
        except:
            pass
        
        time.sleep(0.1)
    
    raise TimeoutError(f"Server on {host}:{port} not ready within {timeout}s")

def ensure_server_stopped(port=2222):
    """Ensure no server is running on the given port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            print(f"Warning: Server already running on port {port}")
            time.sleep(2)  # Give it time to cleanup
    except:
        pass
