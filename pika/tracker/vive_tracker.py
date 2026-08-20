#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vive Tracker module - based on pysurvive library
Provides access interface for Vive Tracker device pose data
"""

import sys
import time
import os
import signal
import math
import threading
import queue
import logging
import numpy as np 
from .pose_utils import xyzQuaternion2matrix, xyzrpy2Mat, matrixToXYZQuaternion

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.vive_tracker')

# Product-specific pose transforms applied after the raw tracker pose.
# Sense: rotate then translate to gripper center.
# Ego: translation only (+X 33.27 mm, -Z 39 mm).
PRODUCT_TRANSFORMS = {
    'sense': {
        'apply_rotation': True,
        'translation': (0.172, 0.0, -0.076),
    },
    'ego': {
        'apply_rotation': False,
        'translation': (0.03327, 0.0, -0.039),
    },
}

# Import pysurvive library
try:
    import pysurvive
except ImportError:
    logger.error("pysurvive library not found, please ensure it is properly installed")
    raise ImportError("pysurvive library not found, please ensure it is properly installed")

class PoseData:
    """Pose data structure for storing and formatting pose information"""
    def __init__(self, device_name, timestamp, position, rotation):
        self.device_name = device_name
        self.timestamp = timestamp
        self.position = position  # [x, y, z]
        self.rotation = rotation  # [x, y, z, w] quaternion

    def __str__(self):
        """Format and output pose information"""
        return f"{self.device_name}: T: {self.timestamp:.6f} P: {self.position[0]:9.6f}, {self.position[1]:9.6f}, {self.position[2]:9.6f} R: {self.rotation[0]:9.6f}, {self.rotation[1]:9.6f}, {self.rotation[2]:9.6f}, {self.rotation[3]:9.6f}"

class ViveTracker:
    """
    Vive Tracker device class, provides access interface for Vive Tracker device pose data
    
    Args:
        config_path (str, optional): Configuration file path
        lh_config (str, optional): Lighthouse configuration
        args (list, optional): Additional pysurvive arguments
        product (str, optional): Product transform to apply, 'sense' or 'ego'. Default 'sense'
    """
    
    def __init__(self, config_path=None, lh_config=None, args=None, product='sense'):
        self.config_path = config_path
        self.lh_config = lh_config
        self.args = args if args else []
        
        if product not in PRODUCT_TRANSFORMS:
            raise ValueError(
                f"Unsupported product '{product}', expected one of: {list(PRODUCT_TRANSFORMS.keys())}"
            )
        self.product = product
        self._product_transform = PRODUCT_TRANSFORMS[product]
        tx, ty, tz = self._product_transform['translation']
        self._transform_matrix = xyzrpy2Mat(tx, ty, tz, 0, 0, 0)
        self._rotate_matrix = None
        if self._product_transform['apply_rotation']:
            # Initial rotation correction: rotate -20 degrees around X axis (roll)
            initial_rotation = xyzrpy2Mat(0, 0, 0, -(20.0 / 180.0 * math.pi), 0, 0)
            # Alignment rotation: -90 degrees around X axis, -90 degrees around Y axis
            alignment_rotation = xyzrpy2Mat(0, 0, 0, -90 / 180 * math.pi, -90 / 180 * math.pi, 0)
            self._rotate_matrix = np.dot(initial_rotation, alignment_rotation)
        
        # Initialize state variables
        self.running = False
        self.context = None
        self.pose_queue = queue.Queue(maxsize=100)  # Queue for storing latest poses
        self.devices_info = {}  # Dictionary for storing device information
        self.data_lock = threading.Lock()
        self.latest_poses = {}  # Store latest pose for each device
        
        # Thread objects
        self.collector_thread = None
        self.processor_thread = None
        self.device_monitor_thread = None
    
    def connect(self):
        """
        Initialize and connect to Vive Tracker devices
        
        Returns:
            bool: Whether the connection succeeded
        """
        if self.running:
            logger.warning("Vive Tracker is already connected")
            return True
        
        try:
            logger.info("Initializing pysurvive...")
            
            # Build pysurvive arguments
            survive_args = sys.argv[:1]  # Keep program name
            
            # Add configuration file arguments
            if self.config_path:
                survive_args.extend(['--config', self.config_path])
            
            # Add lighthouse configuration arguments
            if self.lh_config:
                survive_args.extend(['--lh', self.lh_config])
            
            # Add other arguments
            survive_args.extend(self.args)
            
            # Initialize pysurvive context
            self.context = pysurvive.SimpleContext(survive_args)
            if not self.context:
                logger.error("Error: Failed to initialize pysurvive context")
                return False
            
            logger.info("pysurvive initialized successfully")
            logger.info(f"Using '{self.product}' pose transform")
            
            # Mark as running
            self.running = True
            
            # Create and start pose collection thread
            self.collector_thread = threading.Thread(target=self._pose_collector)
            self.collector_thread.daemon = True
            self.collector_thread.start()
            
            # Create and start pose processing thread
            self.processor_thread = threading.Thread(target=self._pose_processor)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            
            # Create and start device monitor thread
            self.device_monitor_thread = threading.Thread(target=self._device_monitor)
            self.device_monitor_thread.daemon = True
            self.device_monitor_thread.start()
            
            logger.info("Vive Tracker pose tracking started")
            
            # Wait for initial data
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Vive Tracker: {e}")
            self.running = False
            return False
    
    def disconnect(self):
        """
        Disconnect from Vive Tracker devices
        """
        if not self.running:
            return
        
        logger.info("Stopping Vive Tracker pose tracking...")
        self.running = False
        
        # Wait for threads to finish
        if self.collector_thread:
            self.collector_thread.join(timeout=2.0)
        
        if self.processor_thread:
            self.processor_thread.join(timeout=2.0)
            
        if self.device_monitor_thread:
            self.device_monitor_thread.join(timeout=2.0)
        
        # Clean up resources
        self.context = None
        self.pose_queue = queue.Queue(maxsize=100)
        
        # Print statistics
        logger.info("Device statistics:")
        for device_name, info in self.devices_info.items():
            logger.info(f"  - {device_name}: update count {info['updates']}")
        
        logger.info("Vive Tracker disconnected")
    
    def _device_monitor(self):
        """
        Device monitor thread function
        Periodically checks for new devices and updates device list
        """
        logger.info("Device monitor thread started")
        
        # Initialize device list
        self._update_device_list()
        
        # Periodically check for new devices
        while self.running and self.context.Running():
            # Update device list
            self._update_device_list()
            
            # Check once per second
            time.sleep(1.0)
    
    def _update_device_list(self):
        """
        Update device list
        """
        try:
            # Get all current devices
            devices = list(self.context.Objects())
            
            # Update device info dictionary
            with self.data_lock:
                for device in devices:
                    device_name = str(device.Name(), 'utf-8')
                    if device_name not in self.devices_info:
                        logger.info(f"Detected new device: {device_name}")
                        self.devices_info[device_name] = {"updates": 0, "last_update": 0}
        except Exception as e:
            logger.error(f"Error updating device list: {e}")
    
    def _pose_collector(self):
        """
        Pose collection thread function
        Continuously gets latest pose data from pysurvive and puts it in the queue
        """
        logger.info("Pose collection thread started")
        
        # Get and print all available devices
        devices = list(self.context.Objects())
        if not devices:
            logger.warning("Warning: No devices detected")
        else:
            logger.info(f"Detected {len(devices)} device(s):")
            for device in devices:
                device_name = str(device.Name(), 'utf-8')
                logger.info(f"  - {device_name}")
                self.devices_info[device_name] = {"updates": 0, "last_update": 0}
        
        # Continuously get latest poses
        while self.running and self.context.Running():
            updated = self.context.NextUpdated()
            if updated:
                # Get device name
                device_name = str(updated.Name(), 'utf-8')
                
                # If new device, add to device info dictionary
                with self.data_lock:
                    if device_name not in self.devices_info:
                        logger.info(f"Detected new device update: {device_name}")
                        self.devices_info[device_name] = {"updates": 0, "last_update": 0}
                
                # Get pose data
                pose_obj = updated.Pose()
                pose_data = pose_obj[0]  # Pose data
                timestamp = pose_obj[1]  # Timestamp
                
                # Convert pose data to matrix
                # Note: quaternion order from pysurvive is [w,x,y,z]; converted to [x,y,z,w] below
                origin_mat = xyzQuaternion2matrix(
                                pose_data.Pos[0], pose_data.Pos[1], pose_data.Pos[2],
                                pose_data.Rot[1], pose_data.Rot[2], pose_data.Rot[3], pose_data.Rot[0]
                            )
                
                # Apply product-specific pose transform:
                # Sense: rotation then translation to gripper center
                # Ego: translation only
                if self._rotate_matrix is not None:
                    result_mat = np.matmul(np.matmul(origin_mat, self._rotate_matrix), self._transform_matrix)
                else:
                    result_mat = np.matmul(origin_mat, self._transform_matrix)
                # Extract position and quaternion from result matrix
                x, y, z, qx, qy, qz, qw = matrixToXYZQuaternion(result_mat)
                
                # Extract position and rotation information
                position = [x, y, z]
                rotation = [qx, qy, qz, qw]
                    
                # Create pose data object
                pose = PoseData(device_name, timestamp, position, rotation)
                
                # Update device info
                with self.data_lock:
                    if device_name in self.devices_info:
                        self.devices_info[device_name]["updates"] += 1
                        self.devices_info[device_name]["last_update"] = time.time()
                
                # Put pose data in queue; discard old data if queue is full
                try:
                    self.pose_queue.put_nowait(pose)
                except queue.Full:
                    try:
                        self.pose_queue.get_nowait()  # Discard oldest data
                        self.pose_queue.put_nowait(pose)
                    except:
                        pass  # Ignore possible errors
    
    def _pose_processor(self):
        """
        Pose processing thread function
        Gets and processes pose data from queue, updates latest pose dictionary
        """
        logger.info("Pose processing thread started")
        
        while self.running:
            try:
                # Try to get pose data from queue with timeout to periodically check running state
                pose = self.pose_queue.get(timeout=0.1)
                
                # Update latest pose dictionary
                with self.data_lock:
                    self.latest_poses[pose.device_name] = pose
                
                # Custom pose processing logic can be added here
                # e.g.: send to other applications, log to file, perform analysis, etc.
                
            except queue.Empty:
                # Queue empty, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing pose data: {e}")
    
    def get_pose(self, device_name=None):
        """
        Get latest pose data for specified device
        
        Args:
            device_name (str, optional): Device name; if None, returns pose data for all devices
        
        Returns: 
            PoseData or dict: If device_name is specified, returns that device's PoseData object;
                          otherwise returns a dict of all device poses {device_name: PoseData}
        """
        if not self.running:
            logger.warning("Vive Tracker not connected, returning empty pose data")
            return None if device_name else {}
        
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            if device_name:
                return self.latest_poses.get(device_name)
            else:
                return self.latest_poses.copy()
    
    def get_devices(self):
        """
        Get list of all detected devices
        
        Returns:
            list: Device name list
        """
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            return list(self.devices_info.keys())
    
    def get_device_info(self, device_name=None):
        """
        Get device information
        
        Args:
            device_name (str, optional): Device name; if None, returns info for all devices
        
        Returns:
            dict: Device information dictionary
        """
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            if device_name:
                return self.devices_info.get(device_name)
            else:
                return self.devices_info.copy()
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()
