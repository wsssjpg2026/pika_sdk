#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Ego 设备类，提供对Pika Ego设备的访问接口
包含鱼眼相机、RealSense相机和IMU功能
"""

import time
import logging
import threading
from .serial_comm import SerialComm

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.ego')


class Ego:
    """
    Pika Ego设备类，提供对Pika Ego设备的访问接口

    参数:
        port (str): 串口设备路径，默认为'/dev/ttyUSB0'
    """

    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.serial_comm = SerialComm(port=port)
        self.is_connected = False
        self.data_lock = threading.Lock()

        # IMU数据
        self.imu_data = {
            'acc': [0.0, 0.0, 0.0],   # 加速度计数据 (m/s^2)
            'gyr': [0.0, 0.0, 0.0],   # 陀螺仪数据 (rad/s)
            'mag': [0.0, 0.0, 0.0],   # 磁力计数据 (uT)
            'quat': [1.0, 0.0, 0.0, 0.0]   # 四元数 [w, x, y, z]
        }

        # 鱼眼相机索引
        self.fisheye_camera_index = 0

        # RealSense相机序列号
        self.realsense_serial_number = None

        # 相机分辨率和帧率
        self.camera_width = 1280
        self.camera_height = 720
        self.camera_fps = 30
        self.fisheye_thread_fps = 100

        # 相机对象，延迟初始化
        self._fisheye_camera = None
        self._realsense_camera = None

    def connect(self):
        """
        连接Pika Ego设备

        返回:
            bool: 连接是否成功
        """
        if self.is_connected:
            logger.warning("设备已经连接")
            return True

        # 连接串口
        if not self.serial_comm.connect():
            logger.error("连接设备失败")
            return False

        # 启动数据读取线程
        self.serial_comm.start_reading_thread(callback=self._data_callback)
        self.is_connected = True
        logger.info(f"成功连接到Pika Ego设备: {self.port}")

        # 等待初始数据
        time.sleep(0.5)
        return True

    def disconnect(self):
        """
        断开Pika Ego设备连接
        """
        if not self.is_connected:
            return

        # 断开串口连接
        self.serial_comm.disconnect()
        self.is_connected = False
        logger.info(f"已断开Pika Ego设备连接: {self.port}")

        # 断开相机连接
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
        数据回调函数，处理接收到的JSON数据

        参数:
            data (dict): 接收到的JSON数据
        """
        try:
            with self.data_lock:
                # 处理IMU数据
                if 'IMU' in data:
                    imu = data['IMU']

                    # 解析加速度计数据 (m/s^2)
                    if 'acc' in imu and isinstance(imu['acc'], list) and len(imu['acc']) >= 3:
                        self.imu_data['acc'] = [
                            float(imu['acc'][0]),
                            float(imu['acc'][1]),
                            float(imu['acc'][2])
                        ]

                    # 解析陀螺仪数据 (rad/s)
                    if 'gyr' in imu and isinstance(imu['gyr'], list) and len(imu['gyr']) >= 3:
                        self.imu_data['gyr'] = [
                            float(imu['gyr'][0]),
                            float(imu['gyr'][1]),
                            float(imu['gyr'][2])
                        ]

                    # 解析磁力计数据 (uT)
                    if 'mag' in imu and isinstance(imu['mag'], list) and len(imu['mag']) >= 3:
                        self.imu_data['mag'] = [
                            float(imu['mag'][0]),
                            float(imu['mag'][1]),
                            float(imu['mag'][2])
                        ]

                    # 解析四元数 [w, x, y, z]
                    if 'quat' in imu and isinstance(imu['quat'], list) and len(imu['quat']) >= 4:
                        self.imu_data['quat'] = [
                            float(imu['quat'][0]),
                            float(imu['quat'][1]),
                            float(imu['quat'][2]),
                            float(imu['quat'][3])
                        ]

                # 处理版本信息
                if 'Version' in data:
                    logger.info(f"设备版本信息: {data['Version']}")

        except Exception as e:
            logger.error(f"处理数据回调异常: {e}")

    def get_imu_data(self):
        """
        获取IMU原始数据

        返回:
            dict: IMU数据，包含acc、gyr、mag、quat字段
        """
        if not self.is_connected:
            logger.warning("设备未连接，返回默认IMU数据")

        with self.data_lock:
            return self.imu_data.copy()

    def get_accelerometer(self):
        """
        获取加速度计数据

        返回:
            list: [x, y, z] 加速度数据 (m/s^2)
        """
        if not self.is_connected:
            logger.warning("设备未连接，返回默认加速度计数据")

        with self.data_lock:
            return self.imu_data['acc'].copy()

    def get_gyroscope(self):
        """
        获取陀螺仪数据

        返回:
            list: [x, y, z] 角速度数据 (rad/s)
        """
        if not self.is_connected:
            logger.warning("设备未连接，返回默认陀螺仪数据")

        with self.data_lock:
            return self.imu_data['gyr'].copy()

    def get_magnetometer(self):
        """
        获取磁力计数据

        返回:
            list: [x, y, z] 磁力计数据 (uT)
        """
        if not self.is_connected:
            logger.warning("设备未连接，返回默认磁力计数据")

        with self.data_lock:
            return self.imu_data['mag'].copy()

    def get_quaternion(self):
        """
        获取四元数数据

        返回:
            list: [w, x, y, z] 四元数
        """
        if not self.is_connected:
            logger.warning("设备未连接，返回默认四元数数据")

        with self.data_lock:
            return self.imu_data['quat'].copy()

    def set_camera_param(self, camera_width, camera_height, camera_fps, fisheye_thread_fps=100):
        """
        设置相机分辨率和帧率

        参数:
            camera_width (int): 相机宽度
            camera_height (int): 相机高度
            camera_fps (int): 相机帧率
            fisheye_thread_fps (int): 鱼眼相机读取线程帧率，默认为100
        """
        self.camera_width = camera_width
        self.camera_height = camera_height
        self.camera_fps = camera_fps
        self.fisheye_thread_fps = fisheye_thread_fps

    def set_fisheye_camera_index(self, index):
        """
        设置鱼眼相机的索引

        参数:
            index (int): 鱼眼相机索引
        """
        self.fisheye_camera_index = index

    def set_realsense_serial_number(self, serial_number):
        """
        设置RealSense相机序列号

        参数:
            serial_number (str): RealSense相机序列号
        """
        self.realsense_serial_number = serial_number

    def get_fisheye_camera(self):
        """
        获取鱼眼相机对象

        返回:
            FisheyeCamera: 鱼眼相机对象
        """
        if not self.is_connected:
            logger.warning("设备未连接，无法获取鱼眼相机")
            return None

        # 延迟导入，避免循环导入
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
                logger.error(f"初始化鱼眼相机失败: {e}")
                return None

        return self._fisheye_camera

    def get_realsense_camera(self):
        """
        获取RealSense相机对象

        返回:
            RealSenseCamera: RealSense相机对象
        """
        if not self.is_connected:
            logger.warning("设备未连接，无法获取RealSense相机")
            return None

        # 延迟导入，避免循环导入
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
                logger.error(f"初始化RealSense相机失败: {e}")
                return None

        return self._realsense_camera

    def get_version(self):
        """
        获取Ego的版本信息

        返回:
            tuple: 包含版本信息的元组
        """
        return self.serial_comm.get_device_info_command()

    def __del__(self):
        """
        析构函数，确保资源被正确释放
        """
        self.disconnect()
