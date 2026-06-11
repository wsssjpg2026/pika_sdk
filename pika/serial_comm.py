#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Serial communication module for communicating with Pika series devices
"""

import threading
import time
import json
import serial
import logging
import re # Import re module for regular expressions
import struct # Import struct module

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pika.serial_comm")

class SerialComm:
    """
    Serial communication class, responsible for serial communication with devices
    
    Args:
        port (str): Serial port device path, default '/dev/ttyUSB0'
        baudrate (int): Baud rate, default 460800
        timeout (float): Timeout in seconds, default 1.0
    """
    def __init__(self, port=r"/dev/ttyUSB0", baudrate=460800, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.is_connected = False
        self.reading_thread = None
        self.stop_thread = False
        self.buffer = ""
        self.callback = None
        self.data_lock = threading.Lock()
        self.latest_data = {}
    
    def connect(self):
        """
        Connect to serial port device
        
        Returns:
            bool: Whether the connection succeeded
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.is_connected = True
            logger.info(f"Successfully connected to serial port device: {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to serial port device: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """
        Disconnect serial port
        """
        self.stop_reading_thread()
        if self.serial and self.is_connected:
            self.serial.close()
            self.is_connected = False
            logger.info(f"Disconnected from serial port device: {self.port}")
    
    def send_data(self, data):
        """
        Send data to serial port
        
        Args:
            data (bytes): Data to send
            
        Returns:
            bool: Whether sending succeeded
        """
        if not self.is_connected or not self.serial:
            logger.error("Serial port not connected, unable to send data")
            return False
        
        try:
            self.serial.write(data)
            self.serial.flush()
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to send data: {e}")
            return False
    
    def send_command(self, command_type, value=0, big_endian=False):
        """
        Send command to device
        
        Args:
            command_type (int): Command type
            value (float): Command value, default 0.0
            big_endian (bool): Whether to use big-endian, default False (little-endian)
            
        Returns:
            bool: Whether sending succeeded
        """ 
        try:
            # Build command data
            data = bytearray()
            data.append(command_type)  # Command type
            
            if big_endian:
                value_bytes = bytearray(struct.pack('>i', value))  # Big-endian
            else:
                value_bytes = bytearray(struct.pack('<f', value))  # Little-endian
            
            data.extend(value_bytes)
            
            # Add terminator \r\n
            data.extend(b'\r\n')
            
            return self.send_data(data)
        except Exception as e:
            logger.error(f"Failed to build command data: {e}")
            return False
        
    def get_device_info_command(self):
        """
        Send GET_INFO\r\n command to device
        
        Returns:
            bool: Whether sending succeeded
        """
        try:
            # Build GET_INFO command data
            command = 'GET_INFO\r\n'
            data = command.encode('utf-8')
            
            return self.send_data(data)
        except Exception as e:
            logger.error(f"Failed to send GET_INFO command: {e}")
            return False
        
    def read_data(self):
        """
        Read data from serial port
        
        Returns:
            bytes: Data read
        """
        if not self.is_connected or not self.serial:
            logger.error("Serial port not connected, unable to read data")
            return b''
        
        try:
            if self.serial.in_waiting > 0:
                return self.serial.read(self.serial.in_waiting)
            return b''
        except serial.SerialException as e:
            logger.error(f"Failed to read data: {e}")
            return b''
    
    def _reading_thread_func(self):
        """
        Reading thread function, continuously reads data from serial port and parses it
        """
        logger.info("Starting serial port reading thread")
        while not self.stop_thread:
            if not self.is_connected:
                time.sleep(0.1)
                continue
            
            try:
                # Read data
                data = self.read_data()
                if data:
                    # Append read data to buffer
                    self.buffer += data.decode('utf-8', errors='ignore')
                    
                    # Find complete JSON objects
                    json_data = self._find_json()
                    if json_data:
                        # If callback is set, invoke it
                        if self.callback:
                            self.callback(json_data)
                        
                        # Update latest data
                        with self.data_lock:
                            self.latest_data = json_data
                    # Clear buffer if data length exceeds 2000 bytes
                    else:
                        if len(self.buffer) > 2000:
                            self.buffer = ""
                
                # Brief sleep to avoid high CPU usage
                time.sleep(0.001)
            except Exception as e:
                logger.error(f"Reading thread exception: {e}")
                time.sleep(0.1)
        
        logger.info("Serial port reading thread stopped")
    
    def _find_json(self):
        """
        Find complete JSON objects in the buffer
        
        Returns:
            dict: Parsed JSON object, or None if not found
        """
        try:
            # Find start and end positions of JSON object
            start = self.buffer.find('{')
            if start == -1:
                self.buffer = ""
                return None
            
            # Use stack to match braces
            stack = []
            for i in range(start, len(self.buffer)):
                if self.buffer[i] == '{':
                    stack.append(i)
                elif self.buffer[i] == '}':
                    if stack:
                        stack.pop()
                        if not stack:  # Found complete JSON object
                            json_str = self.buffer[start:i+1]
                            self.buffer = self.buffer[i+1:]
                            
                            # --- Key fix: handle trailing commas ---
                            cleaned_json_str = re.sub(r',\s*}', '}', json_str)
                            cleaned_json_str = re.sub(r',\s*\]', ']', cleaned_json_str)
                            
                            return json.loads(cleaned_json_str)
            
            # If no complete JSON object found, keep buffer
            return None
        except json.JSONDecodeError as e:
            # logger.error(f"JSON parse error: {e}")
            self.buffer = ""  # Skip erroneous start position
            return None
        except Exception as e:
            logger.error(f"Communication JSON exception: {e}")
            self.buffer = ""
            return None
    
    def start_reading_thread(self, callback=None):
        """
        Start reading thread
        
        Args:
            callback (callable): Data callback function, receives parsed JSON objects
        """
        if self.reading_thread and self.reading_thread.is_alive():
            logger.warning("Reading thread is already running")
            return
        
        self.callback = callback
        self.stop_thread = False
        self.reading_thread = threading.Thread(target=self._reading_thread_func)
        self.reading_thread.daemon = True
        self.reading_thread.start()
    
    def stop_reading_thread(self):
        """
        Stop reading thread
        """
        self.stop_thread = True
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=1.0)
            logger.info("Reading thread stopped")
    
    def get_latest_data(self):
        """
        Get latest data
        
        Returns:
            dict: Latest data
        """
        with self.data_lock:
            return self.latest_data.copy()
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()

