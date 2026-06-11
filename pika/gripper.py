#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper device class, provides access interface for Pika Gripper devices
"""

import time
import math
import logging
import threading
import struct
from .serial_comm import SerialComm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.gripper')

# Command type enumeration
class CommandType:
    DISABLE = 10    
    ENABLE = 11
    SET_ZERO = 12
    CURRENT = 15
    EFFORT_CTRL = 20
    VELOCITY_CTRL = 21
    POSITION_CTRL = 22

class Gripper:
    """
    Pika Gripper device class, provides access interface for Pika Gripper devices
    
    Args:
        port (str): Serial port device path, default '/dev/ttyUSB0'
    """
    
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        json_pattern = r'\{\r\n"motor":\{\r\n"Speed":[^\r\n]*,\r\n"Current":[^\r\n]*,\r\n"Position":[^\r\n]*\r\n\}\r\n,\r\n"motorstatus":\{\r\n"Voltage":[^\r\n]*,\r\n"DriverTemp":[^\r\n]*,\r\n"MotorTemp":[^\r\n]*,\r\n"Status":[^\r\n]*,\r\n"BusCurrent":[^\r\n]*\r\n\}\r\n\r\n\}'
        self.serial_comm = SerialComm(port=port)
        self.is_connected = False
        self.data_lock = threading.Lock()
        self.motor_data = {
            'Speed': 0.0,  # Motor current speed (rad/s)
            'Current': 0,    # Motor current phase current (mA)
            'Position': 0.0  # Motor current position (rad)
        }
        self.motor_status = {
            'Voltage': 0.0,  # Motor driver voltage (V)
            'DriverTemp': 0,  # Motor driver temperature (°C)
            'MotorTemp': 0,   # Motor temperature (°C)
            'Status': "0x00",  # Motor driver status
            'BusCurrent': 0    # Bus current (mA)
        }
        
        
        # Fisheye camera index
        self.fisheye_camera_index = 0
        
        # RealSense camera serial number
        self.realsense_serial_number = None
        
        # Camera resolution and frame rate
        self.camera_width=1280
        self.camera_height=720
        self.camera_fps=30
        self.fisheye_thread_fps=100
        self.device_id=0
        
        # Camera objects, lazy initialization
        self._fisheye_camera = None
        self._realsense_camera = None
        
        self.rad = None
    
    def connect(self):
        """
        Connect to Pika Gripper device
        
        Returns:
            bool: Whether the connection succeeded
        """
        if self.is_connected:
            logger.warning("Device is already connected")
            return True
        
        # Connect serial port
        if not self.serial_comm.connect():
            logger.error("Failed to connect to device")
            return False
        
        # Start data reading thread
        self.serial_comm.start_reading_thread(callback=self._data_callback)
        self.is_connected = True
        logger.info(f"Successfully connected to Pika Gripper device: {self.port}")
        
        # Wait for initial data
        time.sleep(0.5)
        return True
    
    def disconnect(self):
        """
        Disconnect from Pika Gripper device
        """
        if not self.is_connected:
            return
        
        # Disconnect serial port
        self.serial_comm.disconnect()
        self.is_connected = False
        logger.info(f"Disconnected from Pika Gripper device: {self.port}")
        
        # Disconnect cameras
        if self._fisheye_camera:
            try:
                self._fisheye_camera.disconnect()
            except:
                pass
        
        if self._realsense_camera:
            try:
                self._realsense_camera.disconnect()
            except:
                pass
    
    def _data_callback(self, data):
        """
        Data callback function, processes received JSON data
        
        Args:
            data (dict): Received JSON data
        """
        try:
            with self.data_lock:
                # Process motor data
                if 'motor' in data:
                    motor = data['motor']
                    self.motor_data = {
                        'Speed': motor.get('Speed', 0.0),
                        'Current': motor.get('Current', 0),
                        'Position': motor.get('Position', 0.0)
                    }
                
                # Process motor status
                if 'motorstatus' in data:
                    status = data['motorstatus']
                    self.motor_status = {
                        'Voltage': status.get('Voltage', 0.0),
                        'DriverTemp': status.get('DriverTemp', 0),
                        'MotorTemp': status.get('MotorTemp', 0),
                        'Status': status.get('Status', "0x00"),
                        'BusCurrent': status.get('BusCurrent', 0)
                    }
                
                # Process version information
                if 'Version' in data:
                    logger.info(f"Device version info: {data['Version']}")
                    
        except Exception as e:
            logger.error(f"Exception in data callback: {e}")
    
    def get_motor_data(self):
        """
        Get complete motor data
        
        Returns:
            dict: Motor data, containing Speed, Current, Position fields
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor data")
            return {'Speed': 0.0, 'Current': 0, 'Position': 0.0}
        
        with self.data_lock:
            return self.motor_data.copy()
    
    def get_motor_status(self):
        """
        Get motor status
        
        Returns:
            dict: Motor status, containing Voltage, DriverTemp, MotorTemp, Status, BusCurrent fields
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor status")
            return {'Voltage': 0.0, 'DriverTemp': 0, 'MotorTemp': 0, 'Status': "0x00", 'BusCurrent': 0}
        
        with self.data_lock:
            return self.motor_status.copy()

    def get_motor_speed(self):
        """
        Get motor current speed (rad/s)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor speed")
            return self.motor_data.get('Speed', 0.0)
        with self.data_lock:
            return self.motor_data['Speed']

    def get_motor_current(self):
        """
        Get motor current phase current (mA)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor current")
            return self.motor_data.get('Current', 0)
        with self.data_lock:
            return self.motor_data['Current']

    def get_motor_position(self):
        """
        Get motor current position (rad)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor position")
            return self.motor_data.get('Position', 0.0)
        with self.data_lock:
            return self.motor_data['Position']

    def get_distance(self,angle):
        angle = (180.0 - 43.99) / 180.0 * math.pi - angle
        height = 0.0325 * math.sin(angle)
        width_d = 0.0325 * math.cos(angle)
        width = math.sqrt(0.058**2 - (height - 0.01456)**2) + width_d
        # Convert units from m to mm
        return width*1000
    def get_gripper_distance(self):
        """
        Get current gripper position (mm)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor position")
        with self.data_lock:
            angle = self.motor_data['Position']
            distance = (self.get_distance(angle) - self.get_distance(0)) * 2   #default
            # distance = (self.get_distance(angle) - 81.7) * 2
            return distance
            
    def get_voltage(self):
        """
        Get motor driver voltage (V)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default voltage")
            return self.motor_status.get('Voltage', 0.0)
        with self.data_lock:
            return self.motor_status['Voltage']

    def get_driver_temp(self):
        """
        Get motor driver temperature (°C)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default driver temperature")
            return self.motor_status.get('DriverTemp', 0)
        with self.data_lock:
            return self.motor_status['DriverTemp']

    def get_motor_temp(self):
        """
        Get motor temperature (°C)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default motor temperature")
            return self.motor_status.get('MotorTemp', 0)
        with self.data_lock:
            return self.motor_status['MotorTemp']
    
    def get_status_raw(self):
        """
        Get motor driver status (raw string)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default status")
            return self.motor_status.get('Status', "0x00")
        with self.data_lock:
            return self.motor_status['Status']

    def get_bus_current(self):
        """
        Get bus current (mA)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default bus current")
            return self.motor_status.get('BusCurrent', 0)
        with self.data_lock:
            return self.motor_status['BusCurrent']
    
    def enable(self):
        """
        Enable motor
        
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to enable motor")
            return False
        
        return self.serial_comm.send_command(CommandType.ENABLE)
    
    def disable(self):
        """
        Disable motor
        
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to disable motor")
            return False
        
        return self.serial_comm.send_command(CommandType.DISABLE)
    
    def set_zero(self):
        """
        Set zero point
        
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to set zero point")
            return False
        
        return self.serial_comm.send_command(CommandType.SET_ZERO)
    
    # def set_motor_angle(self,rad):
    #     """
    #     Set motor rotation angle based on current value, intended to output constant control force
    #     
    #     Args:
    #         rad: Angle in radians
    #     
    #     Returns:
    #         bool: Whether the operation succeeded
    #     """
    #     if not self.is_connected:
    #         logger.error("Device not connected, unable to set motor angle")
    #         return False
    #     
    #     # Ensure angle is non-negative
    #     if rad < 0:
    #         rad = 0
    #         logger.warning("Motor angle cannot be negative, set to 0")
    #     
    #     # If current value is above -600, control normally
    #     if self.motor_data['Current'] > -600:
    #         self.rad = rad
    #         self.serial_comm.send_command(CommandType.POSITION_CTRL, rad)
    #     
    #     # If instantaneous current exceeds -2300, slowly open the gripper
    #     elif self.motor_data['Current'] < -2300:
    #         self.rad += 0.05 
    #         logger.warning("Overcurrent, current motor angle:", self.rad)
    #         self.serial_comm.send_command(CommandType.POSITION_CTRL, self.rad)
    #     
    #     # If current value is below -10000, raise error
    #     elif self.motor_data['Current'] < -10000:
    #        logger.error("Motor overcurrent, protection activated, please check gripper motor status; if red light is on, power cycle required")

    #     # Gripper opening normally
    #     else:
    #         if rad > self.rad:
    #             self.serial_comm.send_command(CommandType.POSITION_CTRL, rad)
        
    def set_motor_angle(self, rad):
        """
        Set motor rotation angle
        
        Args:
            rad (float): Target angle in radians
            
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to set motor angle")
            return False
        
        # Ensure angle is non-negative
        if rad < 0:
            rad = 0
            logger.warning("Motor angle cannot be negative, set to 0")
        
        return self.serial_comm.send_command(CommandType.POSITION_CTRL, rad)
    
    def set_motor_torque(self, current):
        """
        Set motor current to adjust motor torque
        
        Args:
            current (float): Current value in A
            Range: 0~2A
            
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to set current")
            return False
        
        # Ensure current is non-negative
        if current < 0:
            current = 0
            logger.warning("Motor current cannot be negative, set to 0")
        
        return self.serial_comm.send_command(CommandType.CURRENT, current)
    
    def set_gripper_distance(self, target_gripper_distance_mm):
        """
        Set gripper opening distance (mm)
        
        Args:
            target_gripper_distance_mm (float): Target gripper opening distance (mm)
            Range: 0-90mm
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.warning("Device not connected, unable to set gripper distance")
            return False

        # 1. Derive target get_distance(angle) value from target gripper travel distance
        # get_gripper_distance = (get_distance(angle) - get_distance(0)) * 2
        # target_gripper_distance_mm / 2 = get_distance(angle) - get_distance(0)
        # get_distance(angle) = target_gripper_distance_mm / 2 + get_distance(0)
        
        # Calculate get_distance(0) once
        get_distance_0 = self.get_distance(0) 
        target_width_mm = target_gripper_distance_mm / 2 + get_distance_0

        # 2. Find corresponding motor angle via numerical method
        # We need to find an 'angle' such that self.get_distance(angle) is as close as possible to target_width_mm
        
        # Define search range and precision
        # Assume motor angle is between 0 and (180.0 - 43.99) / 180.0 * math.pi radians
        low_angle = 0.0
        high_angle = (180.0 - 43.99) / 180.0 * math.pi # Approximately 1.99 radians
        
        # Add a check to ensure target distance is within valid gripper range
        # Minimum gripper distance (angle = low_angle)
        min_gripper_distance_at_low_angle = (self.get_distance(low_angle) - get_distance_0) * 2
        # Maximum gripper distance (angle = high_angle)
        max_gripper_distance_at_high_angle = (self.get_distance(high_angle) - get_distance_0) * 2

        # Ensure target_gripper_distance_mm is within the valid range
        if not (min_gripper_distance_at_low_angle <= target_gripper_distance_mm <= max_gripper_distance_at_high_angle):
            logger.error(f"Target gripper distance {target_gripper_distance_mm:.2f} mm out of valid range [{min_gripper_distance_at_low_angle:.2f}, {max_gripper_distance_at_high_angle:.2f}] mm")
            return False

        tolerance = 0.01 # Gripper distance tolerance (mm)
        angle_tolerance = 0.00001 # Angle tolerance (rad)
        max_iterations = 1000

        found_angle = None

        for i in range(max_iterations):
            mid_angle = (low_angle + high_angle) / 2
            current_width_mm = self.get_distance(mid_angle)
            
            # Check if the current_width_mm is close enough to target_width_mm
            if abs(current_width_mm - target_width_mm) < tolerance:
                found_angle = mid_angle
                break
            
            # Since get_distance(angle) increases with angle:
            if current_width_mm < target_width_mm:
                low_angle = mid_angle
            else:
                high_angle = mid_angle
            
            # If the angle range becomes too small, stop
            if (high_angle - low_angle) < angle_tolerance:
                found_angle = mid_angle # Use the midpoint as the best approximation
                break

        if found_angle is not None:
            self.set_motor_angle(found_angle)
            logger.info(f"Gripper set to target distance {target_gripper_distance_mm} mm, corresponding motor angle {found_angle:.4f} rad")
            return True
        else:
            logger.error(f"Failed to find motor angle for target gripper distance {target_gripper_distance_mm} mm")
            return False
    def set_velocity(self, velocity):
        """
        Set motor velocity
        
        Args:
            velocity (float): Target velocity
            
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to set velocity")
            return False
        
        return self.serial_comm.send_command(CommandType.VELOCITY_CTRL, velocity)
    
    def set_effort(self, effort):
        """
        Set motor effort
        
        Args:
            effort (float): Target effort
            
        Returns:
            bool: Whether the operation succeeded
        """
        if not self.is_connected:
            logger.error("Device not connected, unable to set effort")
            return False
        
        return self.serial_comm.send_command(CommandType.EFFORT_CTRL, effort)
    
    def set_camera_param(self,camera_width,camera_height,camera_fps,fisheye_thread_fps=100):
        '''
        Set camera resolution and frame rate
        
        Args:
            camera_width (int): Camera width
            camera_height (int): Camera height
            camera_fps (int): Camera frame rate
        '''
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera_fps = camera_fps
        self.fisheye_thread_fps = fisheye_thread_fps
        
    def set_fisheye_camera_index(self,index):
        '''
        Set fisheye camera index
        
        Args:
            index (int): Fisheye camera index
        '''
        self.fisheye_camera_index = index
        
    def set_realsense_serial_number(self,serial_number):
        '''
        Set RealSense camera serial number
        
        Args:
            serial_number (str): RealSense camera serial number
        '''
        self.realsense_serial_number = serial_number
        
    def get_fisheye_camera(self):
        """
        Get fisheye camera object
        
        Returns:
            FisheyeCamera: Fisheye camera object
        """
        if not self.is_connected:
            logger.warning("Device not connected, unable to get fisheye camera")
            return None
        
        # Lazy import to avoid circular imports
        if self._fisheye_camera is None:
            try:
                from .camera.fisheye import FisheyeCamera
                self._fisheye_camera = FisheyeCamera(self.camera_width,self.camera_height,self.camera_fps,self.fisheye_camera_index,self.fisheye_thread_fps)
                self._fisheye_camera.connect()
            except Exception as e:
                logger.error(f"Failed to initialize fisheye camera: {e}")
                return None
        
        return self._fisheye_camera
    
    def get_realsense_camera(self):
        """
        Get RealSense camera object
        
        Returns:
            RealSenseCamera: RealSense camera object
        """
        if not self.is_connected:
            logger.warning("Device not connected, unable to get RealSense camera")
            return None
        
        # Lazy import to avoid circular imports
        if self._realsense_camera is None:
            try:
                from .camera.realsense import RealSenseCamera
                self._realsense_camera = RealSenseCamera(self.camera_width,self.camera_height,self.camera_fps,self.realsense_serial_number)
                self._realsense_camera.connect()
            except Exception as e:
                logger.error(f"Failed to initialize RealSense camera: {e}")
                return None
        
        return self._realsense_camera
    
    def get_version(self):
        """
        Get Gripper version information
        
        Returns:
            tuple: Tuple containing version information
        """
        return self.serial_comm.get_device_info_command()
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()

