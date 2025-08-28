# src/core/ssh_connector.py
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor
import queue
import time
import logging
from typing import Optional

class SSHConnectionPool:
    def __init__(self, max_connections=10):
        self.pool = queue.Queue(maxsize=max_connections)
        self.logger = logging.getLogger(__name__)

class SSHConnector:
    def __init__(self, max_retries=3, pool_size=10):
        self.pool = SSHConnectionPool(max_connections=pool_size)
        self.executor = ThreadPoolExecutor(max_workers=pool_size)
        self.max_retries = max_retries
        self.base_delay = 1
        self.logger = logging.getLogger(__name__)

    def connect_with_retry(self, device) -> ConnectHandler:
        """Connect to device with exponential backoff retry"""
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                connection_params = {
                    'device_type': device.device_type,
                    'host': device.ip_address,
                    'username': device.username,
                    'password': device.password,
                    'port': device.port,
                    'timeout': 30,
                    'global_delay_factor': 1,
                    'fast_cli': True
                }

                self.logger.info(f"Connecting to {device.ip_address} (attempt {attempt + 1})")
                connection = ConnectHandler(**connection_params)

                # Test connection with simple command
                connection.send_command('show clock', expect_string=r'#')
                self.logger.info(f"Successfully connected to {device.ip_address}")
                return connection

            except NetmikoAuthenticationException as e:
                # Don't retry auth failures
                self.logger.error(f"Authentication failed for {device.ip_address}")
                raise e

            except NetmikoTimeoutException as e:
                last_exception = e
                self.logger.warning(f"Timeout connecting to {device.ip_address} (attempt {attempt + 1})")

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Connection failed to {device.ip_address}: {str(e)}")

            # Exponential backoff (don't wait on last attempt)
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                self.logger.info(f"Waiting {delay} seconds before retry...")
                time.sleep(delay)

        # All attempts failed
        self.logger.error(f"Failed to connect to {device.ip_address} after {self.max_retries} attempts")
        raise last_exception or Exception(f"Connection failed to {device.ip_address}")

    def disconnect(self, connection: ConnectHandler):
        """Safely disconnect from device"""
        try:
            if connection:
                connection.disconnect()
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {str(e)}")

    def execute_command(self, connection, command: str, timeout: int = 30,
                       expect_string: str = '#') -> str:
        """Execute command with proper error handling"""
        try:
            output = connection.send_command(
                command,
                expect_string=expect_string,
                strip_prompt=True,
                strip_command=True,
                read_timeout=timeout
            )
            return output
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            raise