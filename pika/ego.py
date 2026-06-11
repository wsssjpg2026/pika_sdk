#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Ego device class, provides access interface for Pika Ego devices
Includes fisheye camera, RealSense camera, and IMU functionality
"""

import time
import logging
import threading
from .serial_comm import SerialComm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.ego')


class Ego:
    """
    Pika Ego device class, provides access interface for Pika Ego devices

    Args:
        port (str): Serial port device path, default '/dev/ttyUSB0'
    """

    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.serial_comm = SerialComm(port=port)
        self.is_connected = False
        self.data_lock = threading.Lock()

        # IMU data
        self.imu_data = {
            'acc': [0.0, 0.0, 0.0],   # Accelerometer data (m/s^2)
            'gyr': [0.0, 0.0, 0.0],   # Gyroscope data (rad/s)
            'mag': [0.0, 0.0, 0.0],   # Magnetometer data (uT)
            'quat': [1.0, 0.0, 0.0, 0.0]   # Quaternion [w, x, y, z]
        }

        # Fisheye camera index
        self.fisheye_camera_index = 0

        # RealSense camera serial number
        self.realsense_serial_number = None

        # Camera resolution and frame rate
        self.camera_width = 1280
        self.camera_height = 720
        self.camera_fps = 30
        self.fisheye_thread_fps = 100

        # Camera objects, lazy initialization
        self._fisheye_camera = None
        self._realsense_camera = None

    def connect(self):
        """
        Connect to Pika Ego device

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
        logger.info(f"Successfully connected to Pika Ego device: {self.port}")

        # Wait for initial data
        time.sleep(0.5)
        return True

    def disconnect(self):
        """
        Disconnect from Pika Ego device
        """
        if not self.is_connected:
            return

        # Disconnect serial port
        self.serial_comm.disconnect()
        self.is_connected = False
        logger.info(f"Disconnected from Pika Ego device: {self.port}")

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
                # Process IMU data
                if 'IMU' in data:
                    imu = data['IMU']

                    # Parse accelerometer data (m/s^2)
                    if 'acc' in imu and isinstance(imu['acc'], list) and len(imu['acc']) >= 3:
                        self.imu_data['acc'] = [
                            float(imu['acc'][0]),
                            float(imu['acc'][1]),
                            float(imu['acc'][2])
                        ]

                    # Parse gyroscope data (rad/s)
                    if 'gyr' in imu and isinstance(imu['gyr'], list) and len(imu['gyr']) >= 3:
                        self.imu_data['gyr'] = [
                            float(imu['gyr'][0]),
                            float(imu['gyr'][1]),
                            float(imu['gyr'][2])
                        ]

                    # Parse magnetometer data (uT)
                    if 'mag' in imu and isinstance(imu['mag'], list) and len(imu['mag']) >= 3:
                        self.imu_data['mag'] = [
                            float(imu['mag'][0]),
                            float(imu['mag'][1]),
                            float(imu['mag'][2])
                        ]

                    # Parse quaternion [w, x, y, z]
                    if 'quat' in imu and isinstance(imu['quat'], list) and len(imu['quat']) >= 4:
                        self.imu_data['quat'] = [
                            float(imu['quat'][0]),
                            float(imu['quat'][1]),
                            float(imu['quat'][2]),
                            float(imu['quat'][3])
                        ]

                # Process version information
                if 'Version' in data:
                    logger.info(f"Device version info: {data['Version']}")

        except Exception as e:
            logger.error(f"Exception in data callback: {e}")

    def get_imu_data(self):
        """
        Get raw IMU data

        Returns:
            dict: IMU data, containing acc, gyr, mag, quat fields
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default IMU data")

        with self.data_lock:
            return self.imu_data.copy()

    def get_accelerometer(self):
        """
        Get accelerometer data

        Returns:
            list: [x, y, z] acceleration data (m/s^2)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default accelerometer data")

        with self.data_lock:
            return self.imu_data['acc'].copy()

    def get_gyroscope(self):
        """
        Get gyroscope data

        Returns:
            list: [x, y, z] angular velocity data (rad/s)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default gyroscope data")

        with self.data_lock:
            return self.imu_data['gyr'].copy()

    def get_magnetometer(self):
        """
        Get magnetometer data

        Returns:
            list: [x, y, z] magnetometer data (uT)
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default magnetometer data")

        with self.data_lock:
            return self.imu_data['mag'].copy()

    def get_quaternion(self):
        """
        Get quaternion data

        Returns:
            list: [w, x, y, z] quaternion
        """
        if not self.is_connected:
            logger.warning("Device not connected, returning default quaternion data")

        with self.data_lock:
            return self.imu_data['quat'].copy()

    def set_camera_param(self, camera_width, camera_height, camera_fps, fisheye_thread_fps=100):
        """
        Set camera resolution and frame rate

        Args:
            camera_width (int): Camera width
            camera_height (int): Camera height
            camera_fps (int): Camera frame rate
            fisheye_thread_fps (int): Fisheye camera reading thread frame rate, default 100
        """
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera_fps = camera_fps
        self.fisheye_thread_fps = fisheye_thread_fps

    def set_fisheye_camera_index(self, index):
        """
        Set fisheye camera index

        Args:
            index (int): Fisheye camera index
        """
        self.fisheye_camera_index = index

    def set_realsense_serial_number(self, serial_number):
        """
        Set RealSense camera serial number

        Args:
            serial_number (str): RealSense camera serial number
        """
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
                self._fisheye_camera = FisheyeCamera(
                    self.camera_width,
                    self.camera_height,
                    self.camera_fps,
                    self.fisheye_camera_index,
                    self.fisheye_thread_fps
                )
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
                self._realsense_camera = RealSenseCamera(
                    self.camera_width,
                    self.camera_height,
                    self.camera_fps,
                    self.realsense_serial_number
                )
                self._realsense_camera.connect()
            except Exception as e:
                logger.error(f"Failed to initialize RealSense camera: {e}")
                return None

        return self._realsense_camera

    def get_version(self):
        """
        Get Ego version information

        Returns:
            tuple: Tuple containing version information
        """
        return self.serial_comm.get_device_info_command()

    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()
