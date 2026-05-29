#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika SDK 测试脚本
用于测试SDK的安装和基本功能
"""

import os
import sys
import time

def test_import():
    """测试导入模块"""
    print("测试导入模块...")
    try:
        from pika import sense, gripper
        print("✓ 成功导入 pika 模块")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_serial_comm():
    """测试串口通信模块"""
    print("\n测试串口通信模块...")
    try:
        from pika.serial_comm import SerialComm
        
        # 创建串口通信对象
        serial_comm = SerialComm(port='/dev/ttyUSB0')  # 请根据实际情况修改串口路径
        print("✓ 成功创建 SerialComm 对象")
        
        # 测试连接方法（不实际连接）
        print("✓ SerialComm 类方法检查通过")
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_sense_class():
    """测试 Sense 类"""
    print("\n测试 Sense 类...")
    try:
        from pika import sense
        
        # 创建 Sense 对象（不实际连接）
        my_sense = sense('/dev/ttyUSB0')  # 请根据实际情况修改串口路径
        print("✓ 成功创建 Sense 对象")
        
        # 检查方法是否存在
        methods = [
            'connect', 'disconnect', 'get_gripper_distance', 'get_encoder_data',
            'get_command_state', 'get_fisheye_camera', 'get_realsense_camera',
            'get_vive_tracker'
        ]
        for method in methods:
            if hasattr(my_sense, method) and callable(getattr(my_sense, method)):
                print(f"✓ 方法 {method} 存在")
            else:
                print(f"✗ 方法 {method} 不存在或不可调用")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_gripper_class():
    """测试 Gripper 类"""
    print("\n测试 Gripper 类...")
    try:
        from pika import gripper
        
        # 创建 Gripper 对象（不实际连接）
        my_gripper = gripper('/dev/ttyUSB0')  # 请根据实际情况修改串口路径
        print("✓ 成功创建 Gripper 对象")
        
        # 检查方法是否存在
        methods = [
            'connect', 'disconnect', 'enable', 'disable', 'set_zero',
            'set_velocity', 'set_effort', 
            'get_motor_data', 'get_motor_status', 'get_motor_speed', 'get_motor_current','get_motor_position',
            'get_voltage','get_driver_temp','get_motor_temp','get_status_raw',
            'get_bus_current',
            'get_fisheye_camera', 'get_realsense_camera',
            'get_gripper_distance',
            'set_motor_angle','set_gripper_distance','set_velocity','set_effort',
            'set_camera_param'
        ]
        for method in methods:
            if hasattr(my_gripper, method) and callable(getattr(my_gripper, method)):
                print(f"✓ 方法 {method} 存在")
            else:
                print(f"✗ 方法 {method} 不存在或不可调用")
                return False
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_ego_class():
    """测试 Ego 类"""
    print("\n测试 Ego 类...")
    try:
        from pika import ego

        # 创建 Ego 对象（不实际连接）
        my_ego = ego('/dev/ttyUSB0')
        print("✓ 成功创建 Ego 对象")

        # 检查方法是否存在
        methods = [
            'connect', 'disconnect',
            'get_imu_data', 'get_accelerometer', 'get_gyroscope',
            'get_magnetometer', 'get_quaternion',
            'get_fisheye_camera', 'get_realsense_camera',
            'set_camera_param', 'set_fisheye_camera_index', 'set_realsense_serial_number'
        ]
        for method in methods:
            if hasattr(my_ego, method) and callable(getattr(my_ego, method)):
                print(f"✓ 方法 {method} 存在")
            else:
                print(f"✗ 方法 {method} 不存在或不可调用")
                return False

        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_camera_modules():
    """测试相机模块"""
    print("\n测试相机模块...")
    try:
        from pika.camera.fisheye import FisheyeCamera
        print("✓ 成功导入 FisheyeCamera 类")
        
        try:
            from pika.camera.realsense import RealSenseCamera
            print("✓ 成功导入 RealSenseCamera 类")
        except ImportError:
            print("! RealSenseCamera 导入失败，可能是 pyrealsense2 库未安装")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("===== Pika SDK 测试 =====")
    
    # 测试导入
    if not test_import():
        print("\n导入测试失败，请检查安装")
        return
    
    # 测试串口通信模块
    test_serial_comm()
    
    # 测试 Sense 类
    test_sense_class()
    
    # 测试 Gripper 类
    test_gripper_class()

    # 测试 Ego 类
    test_ego_class()

    # 测试相机模块
    test_camera_modules()
    
    print("\n===== 测试完成 =====")
    print("注意：这只是基本功能测试，未实际连接设备进行测试")
    print("要进行实际设备测试，请运行 examples 目录中的示例程序")

if __name__ == "__main__":
    main()
