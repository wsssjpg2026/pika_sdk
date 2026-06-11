#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fisheye camera module - provides access to the fisheye camera on Pika devices
"""

import cv2
import logging
import numpy as np
import threading
import time
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.camera.fisheye')

class FisheyeCamera:
    """
    Fisheye camera class, provides access to the fisheye camera on Pika devices
    
    Attributes:
        camera_width (int): Camera width, default 1280
        camera_height (int): Camera height, default 720
        camera_fps (int): Camera frame rate, default 30
        device_id (int): Camera device ID, default 0
        is_connected (bool): Whether the device is connected, default False
    """
    
    def __init__(self, camera_width=1280, camera_height=720, camera_fps=30, device_id=0, fisheye_thread_fps=100):
        # fps use to open a high fps thread to get image
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera_fps = camera_fps
        self.device_id = device_id
        self.fisheye_thread_fps = fisheye_thread_fps
        self.cap = None
        self.is_connected = False
        
        self.reading_thread = None
        self.stop_thread = False
        self.last_image_flag = False
        self.last_image = None
        self.last_image_lock = threading.Lock()
    
    def connect(self):
        """
        Connect to the fisheye camera
        
        Returns:
            bool: Whether the connection succeeded
        """
        try:
            # OpenCV 4.13.0 does not have setLogLevel
            if hasattr(cv2, 'setLogLevel'):
                cv2.setLogLevel(0)
            # Use V4L2 backend to prevent FFMPEG auto-downgrade causing device index mismatch
            self.cap = cv2.VideoCapture(self.device_id, cv2.CAP_V4L2)

            # Check
            backend_name = self.cap.getBackendName()
            if "v4l2" not in backend_name.lower():
                logger.error(f"Camera backend error: expected V4L2, got {backend_name}, device ID: {self.device_id}")
                self.cap.release()
                return False

            self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.cap.set(cv2.CAP_PROP_FOURCC, self.fourcc)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_fps) # This setting seems to have no effect
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open fisheye camera, device ID: {self.device_id}")
                return False
            
            self.is_connected = True
            logger.info(f"Successfully connected to fisheye camera, device ID: {self.device_id}")
            self.start_reading_thread()
            
            return True
        except Exception as e:
            logger.error(f"Exception connecting to fisheye camera: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnect from the fisheye camera
        """
        self.stop_reading_thread()
        if self.cap and self.is_connected:
            self.cap.release()
            self.is_connected = False
            logger.info(f"Disconnected from fisheye camera, device ID: {self.device_id}")
    
    def start_reading_thread(self):
        """
        Start the reading thread
        
        Args:
            callback (callable): Data callback function, receives parsed JSON objects
        """
        if self.reading_thread and self.reading_thread.is_alive():
            logger.warning("Reading thread is already running")
            return
        self.stop_thread = False
        self.reading_thread = threading.Thread(target=self._reading_thread_func)
        self.reading_thread.daemon = True
        self.reading_thread.start()
        
    def stop_reading_thread(self):
        """
        Stop the reading thread
        """
        self.stop_thread = True
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=1.0)
            logger.info("Reading thread stopped")
    
    def _reading_thread_func(self):
        
        logger.info("Starting fisheye camera high-frequency reading thread")
        time_interval = 1 / self.fisheye_thread_fps
        while not self.stop_thread:
            try:
                ret, frame = self.cap.read() # Very high frequency, at least 200Hz, so no need to compute wait time
                
                if not ret:
                    logger.warning("Failed to read image")
                    break
                
                with self.last_image_lock:
                    self.last_image_flag = True
                    self.last_image = frame
                
                time.sleep(time_interval)
                
            except Exception as e:
                logger.error(f"Exception getting image: {e}")
                break
        
        logger.info("Fisheye camera high-frequency reading thread stopped")
        
    def get_frame(self):
        return self.last_image_flag, self.last_image
    
    def get_camera_info(self):
        """
        Get camera information
        
        Returns:
            dict: Camera information
        """
        if not self.is_connected or not self.cap:
            logger.warning("Camera not connected, unable to get information")
            return {}
        
        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            return {
                'width': width,
                'height': height,
                'fps': fps,
                'device_id': self.device_id
            }
        except Exception as e:
            logger.error(f"Exception getting camera information: {e}")
            return {}
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()
