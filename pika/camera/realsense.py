#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RealSense camera module - provides access to the RealSense D405 camera on Pika devices
"""

import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.camera.realsense')

class RealSenseCamera:
    """
    RealSense camera class, provides access to the RealSense D405 camera on Pika devices
    Args:
        camera_width: Camera width, default 1280
        camera_height: Camera height, default 720
        camera_fps: Camera frame rate, default 30
        serial_number: Camera serial number, default None
    """
    
    def __init__(self, camera_width=1280, camera_height=720, camera_fps=30, serial_number=None):
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera_fps = camera_fps
        self.serial_number = serial_number
        
        self.pipeline = None
        self.config = None
        self.is_connected = False
        
        # Try to import pyrealsense2 library
        try:
            import pyrealsense2 as rs
            self.rs = rs
        except ImportError:
            logger.warning("pyrealsense2 library not found, please install: pip install pyrealsense2")
            self.rs = None
    
    def connect(self):
        """
        Connect to the RealSense camera
        
        Returns:
            bool: Whether the connection succeeded
        """
        if self.rs is None:
            logger.error("pyrealsense2 library not found, unable to connect to RealSense camera")
            return False
        
        try:    
            self.pipeline = self.rs.pipeline()
            self.config = self.rs.config()
            
            # Configure streams
            self.config.enable_device(self.serial_number)
            self.config.enable_stream(self.rs.stream.depth, self.camera_width, self.camera_height, self.rs.format.z16, self.camera_fps)
            self.config.enable_stream(self.rs.stream.color, self.camera_width, self.camera_height, self.rs.format.bgr8, self.camera_fps)
            
            # Start pipeline
            self.pipeline.start(self.config)
            
            self.is_connected = True
            logger.info(f"Successfully connected to RealSense camera, device serial number: {self.serial_number}")
            return True
        except Exception as e:
            logger.error(f"Exception connecting to RealSense camera: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnect from the RealSense camera
        """
        if self.pipeline and self.is_connected:
            try:
                self.pipeline.stop()
                self.is_connected = False
                logger.info(f"Disconnected from RealSense camera, device serial number: {self.serial_number}")
            except Exception as e:
                logger.error(f"Exception disconnecting from RealSense camera: {e}")
    
    def get_frames(self):
        """
        Get a set of frames (color and depth)
        
        Returns:
            tuple: (success flag, color image, depth image)
        """
        if not self.is_connected or not self.pipeline or self.rs is None:
            logger.warning("Camera not connected, unable to get images")
            return False, None, None
        
        try:
            # Wait for a coherent set of frames
            frames = self.pipeline.wait_for_frames()
            
            # Get color and depth frames
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                logger.warning("Failed to get frames")
                return False, None, None
            
            # Convert frames to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            return True, color_image, depth_image
        except Exception as e:
            logger.error(f"Exception getting frames: {e}")
            return False, None, None
    
    def get_color_frame(self):
        """
        Get color image
        
        Returns:
            tuple: (success flag, color image)
        """
        success, color_image, _ = self.get_frames()
        return success, color_image
    
    def get_depth_frame(self):
        """
        Get depth image
        
        Returns:
            tuple: (success flag, depth image)
        """
        success, _, depth_image = self.get_frames()
        return success, depth_image
    
    def get_camera_info(self):
        """
        Get camera information
        
        Returns:
            dict: Camera information
        """
        if not self.is_connected or not self.pipeline or self.rs is None:
            logger.warning("Camera not connected, unable to get information")
            return {}
        
        try:
            # Get camera intrinsics
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            color_profile = color_frame.get_profile()
            depth_profile = depth_frame.get_profile()
            
            color_intrinsics = color_profile.as_video_stream_profile().get_intrinsics()
            depth_intrinsics = depth_profile.as_video_stream_profile().get_intrinsics()
            
            return {
                'color_width': color_intrinsics.width,
                'color_height': color_intrinsics.height,
                'color_fx': color_intrinsics.fx,
                'color_fy': color_intrinsics.fy,
                'color_ppx': color_intrinsics.ppx,
                'color_ppy': color_intrinsics.ppy,
                'depth_width': depth_intrinsics.width,
                'depth_height': depth_intrinsics.height,
                'depth_fx': depth_intrinsics.fx,
                'depth_fy': depth_intrinsics.fy,
                'depth_ppx': depth_intrinsics.ppx,
                'depth_ppy': depth_intrinsics.ppy,
                'serial_number': self.serial_number
            }
        except Exception as e:
            logger.error(f"Exception getting camera information: {e}")
            return {}
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()
