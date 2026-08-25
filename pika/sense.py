#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Sense device class, provides access interface for Pika Sense devices
"""

import time
import math
import logging
import threading
from .serial_comm import SerialComm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.sense')

class CommandType:
    LIGHT_CTRL = 50
    VIBRATE_CTRL = 51
    
class Sense:
    """
    Pika Sense device class, provides access interface for Pika Sense devices
    
    Args:
        port (str): Serial port device path, default '/dev/ttyUSB0'
    """
    
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        json_pattern = r'\{\r\n"Command":[0-1],\r\n"AS5047":\{\r\n"angle":[^\r\n]*,\r\n"rad":[^\r\n]*\r\n\},\r\n\r\n"IMU":\{\r\n"acc":\[[^\r\n]*\],\r\n"gyr":\[[^\r\n]*\],\r\n"pitch":[^\r\n]*,\r\n"roll":[^\r\n]*,\r\n"yaw":[^\r\n]*\r\n\}\r\n\r\n\}'
        self.serial_comm = SerialComm(port=port)
        self.is_connected = False
        self.data_lock = threading.Lock()
        
        # Encoder data
        self.encoder_data = {
            'angle': 0.0,
            'rad': 0.0
        }
        
        # Command state
        self.command_state = 0
        
        # Fisheye camera index
        self.fisheye_camera_index = 0
        
        # RealSense camera serial number
        self.realsense_serial_number = None
        
        # Camera resolution and frame rate
        self.camera_width=1280
        self.camera_height=720
        self.camera_fps=30
        self.fisheye_thread_fps=100
        
        # Camera objects, lazy initialization
        self._fisheye_camera = None
        self._realsense_camera = None
        
        # Vive Tracker object, lazy initialization
        self._vive_tracker = None
        self._vive_tracker_config = None
        self._vive_tracker_lh = None
        self._vive_tracker_args = None
        self._vive_tracker_lock = threading.RLock()
    
    def connect(self):
        """
        Connect to Pika Sense device
        
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
        logger.info(f"Successfully connected to Pika Sense device: {self.port}")
        
        # Wait for initial data
        time.sleep(0.5)
        return True
    
    def disconnect(self):
        """
        Disconnect from Pika Sense device
        """
        if not self.is_connected:
            return
        
        # Disconnect serial port
        self.serial_comm.disconnect()
        self.is_connected = False
        logger.info(f"Disconnected from Pika Sense device: {self.port}")
        
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
                
        # Disconnect Vive Tracker
        if self._vive_tracker:
            with self._vive_tracker_lock:
                try:
                    self._vive_tracker.disconnect()
                except:
                    pass
                self._vive_tracker = None
    
    def _data_callback(self, data):
        """
        Data callback function, processes received JSON data
        
        Args:
            data (dict): Received JSON data
        """
        try:
            with self.data_lock:

                # Process encoder data
                if 'AS5047' in data:
                    encoder = data['AS5047']
                    self.encoder_data = {
                        'angle': encoder.get('angle', 0.0),
                        'rad': encoder.get('rad', 0.0)
                    }
                
                # Process command state
                if 'Command' in data:
                    self.command_state = data['Command']
                
                # Process version information
                if 'Version' in data:
                    logger.info(f"Device version info: {data['Version']}")
                    
        except Exception as e:
            logger.error(f"Exception in data callback: {e}")
            
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
            angle = self.encoder_data['rad']
            distance = (self.get_distance(angle) - self.get_distance(0)) * 2   #default
            return distance
        
        
    def get_encoder_data(self):
        """
        Get encoder data
        
        Returns:
            dict: Encoder data, containing angle, rad fields
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default encoder data")
        
        with self.data_lock:
            return self.encoder_data.copy()
    
    def get_command_state(self):
        """
        Get command state
        
        Returns:
            int: Command state, 0 or 1
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default command state")
        
        with self.data_lock:
            return self.command_state
    
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
    
    def set_vive_tracker_config(self, config_path=None, lh_config=None, args=None):
        '''
        Set Vive Tracker configuration
        
        Args:
            config_path (str, optional): Configuration file path
            lh_config (str, optional): Lighthouse configuration
            args (list, optional): Additional pysurvive arguments
        '''
        self._vive_tracker_config = config_path
        self._vive_tracker_lh = lh_config
        self._vive_tracker_args = args
        
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
    
    def get_vive_tracker(self):
        """
        Get Vive Tracker object
        
        Returns:
            ViveTracker: Vive Tracker object
        """
        # Lazy import to avoid circular imports
        with self._vive_tracker_lock:
            if self._vive_tracker is None:
                try:
                    from .tracker.vive_tracker import ViveTracker
                    tracker = ViveTracker(
                        config_path=self._vive_tracker_config,
                        lh_config=self._vive_tracker_lh,
                        args=self._vive_tracker_args
                    )
                    if not tracker.connect():
                        return None
                    self._vive_tracker = tracker
                except Exception as e:
                    logger.error(f"Failed to initialize Vive Tracker: {e}")
                    return None

        return self._vive_tracker

    def restart_vive_tracker(self):
        """Rebuild the libsurvive context while leaving Pika serial connected."""
        with self._vive_tracker_lock:
            old_tracker = self._vive_tracker
            if old_tracker is not None:
                try:
                    if old_tracker.disconnect() is False:
                        logger.error(
                            "Refusing Vive Tracker restart because the old "
                            "libsurvive context did not close cleanly"
                        )
                        return False
                except Exception as e:
                    logger.error(f"Failed to stop Vive Tracker for restart: {e}")
                    return False
                # Detach only after the old tracker proves that all Python
                # workers and the native context have stopped.  Keeping the
                # owner on failure prevents an unreachable live C context.
                self._vive_tracker = None
            try:
                from .tracker.vive_tracker import ViveTracker
                tracker = ViveTracker(
                    config_path=self._vive_tracker_config,
                    lh_config=self._vive_tracker_lh,
                    args=self._vive_tracker_args,
                    product='sense'
                )
                if not tracker.connect():
                    return False
                self._vive_tracker = tracker
                logger.warning("Vive Tracker decoder context restarted")
                return True
            except Exception as e:
                logger.error(f"Failed to restart Vive Tracker: {e}")
                return False
    
    def get_pose(self, device_name=None):
        """
        Get Vive Tracker pose data
        
        Args:
            device_name (str, optional): Device name; if None, returns pose data for all devices
        
        Returns:
            PoseData or dict: If device_name is specified, returns that device's PoseData object;
                          otherwise returns a dict of all device poses {device_name: PoseData}
        """
        tracker = self.get_vive_tracker()
        if tracker:
            return tracker.get_pose(device_name)
        else:
            logger.warning("Vive Tracker not initialized, unable to get pose data")
            return None if device_name else {}
    
    def get_tracker_devices(self):
        """
        Get list of all detected Vive Tracker devices
        
        Returns:
            list: Device name list
        """
        tracker = self.get_vive_tracker()
        if tracker:
            return tracker.get_devices()
        else:
            logger.warning("Vive Tracker not initialized, unable to get device list")
        return []

    def get_tracker_health(self, device_name=None):
        """Return native optical/global-scene facts for the Vive Tracker."""
        tracker = self.get_vive_tracker()
        if tracker:
            return tracker.get_tracking_health(device_name)
        return {
            "bridge_available": False,
            "bridge_error": "Vive Tracker is unavailable",
            "context_epoch": 0,
            "global_scene_generation": 0,
            "global_scene_count": 0,
            "cached_map_lighthouses": (),
            "lighthouses": {},
            "discovered_lighthouses": (),
        }

    def lock_tracker_global_scene(self):
        """Freeze the active Lighthouse map until the tracker context restarts."""
        tracker = self.get_vive_tracker()
        return bool(tracker and tracker.lock_global_scene())
    
    def light_ctrl(self, light_id):
        """
        Set Vive Tracker light control mode
        
        Args:
            light_id (int): Light control, 0=white on, 1=red on, 2=green on, 3=blue on, 4=yellow on
        """
        return self.serial_comm.send_command(CommandType.LIGHT_CTRL, light_id, big_endian=True)
    
    
    def vibrate_ctrl(self, mode):
        """
        Set Vive Tracker vibration mode
        
        Args:
            mode (int): Vibration mode, 0=off, 1=on
        """
        return self.serial_comm.send_command(CommandType.VIBRATE_CTRL, mode, big_endian=True)
        
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
