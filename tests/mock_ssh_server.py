import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)

class MockSSHServer:
    """Mock SSH server for testing network connections"""
    
    def __init__(self, host='127.0.0.1', port=2222):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
        
    def start(self):
        """Start the mock SSH server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            self.running = True
            self.server_thread = threading.Thread(target=self._accept_connections)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Give server time to start
            time.sleep(0.1)
            logger.info(f"Mock SSH server started on {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error starting mock SSH server: {e}")
            raise
    
    def stop(self):
        """Stop the mock SSH server"""
        self.running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.server_thread:
            self.server_thread.join(timeout=2)
        
        logger.info("Mock SSH server stopped")
    
    def _accept_connections(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                continue  # Check if still running
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _handle_client(self, client_socket, addr):
        """Handle individual client connections"""
        try:
            # Send SSH banner
            banner = b"SSH-2.0-MockSSH\r\n"
            client_socket.send(banner)
            
            # Simple response loop
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Echo back a simple response
                    response = b"Mock SSH Response\r\n"
                    client_socket.send(response)
                    
                except socket.timeout:
                    continue
                except:
                    break
                    
        except Exception as e:
            logger.debug(f"Client handler error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

def start_mock_ssh_server(port=2222):
    """Start a mock SSH server for testing"""
    server = MockSSHServer(port=port)
    server.start()
    return server

def stop_mock_ssh_server(server):
    """Stop a mock SSH server"""
    if server:
        server.stop()
