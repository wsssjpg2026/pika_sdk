#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Ego 设备相机和IMU测试示例
同时打开鱼眼相机、RealSense彩色/深度相机，并在终端输出IMU数据
"""

import cv2
import math
import time
import sys
import threading
from collections import deque

# 添加 SDK 路径
sys.path.insert(0, '../..')

from pika import ego


def quaternion_to_euler(w, x, y, z):
    """
    四元数转欧拉角 (roll, pitch, yaw)
    输入: w, x, y, z - 四元数分量
    输出: roll, pitch, yaw - 欧拉角 (rad)
    """
    # 归一化四元数
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if norm < 1e-6:
        return 0.0, 0.0, 0.0

    w /= norm
    x /= norm
    y /= norm
    z /= norm

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def print_imu_data(my_ego, stop_flag):
    """在终端输出IMU数据"""
    print("\n===== IMU 数据输出 =====")
    print("格式: 加速度 | 角速度 | 磁力计 | 欧拉角(计算) | 四元数")
    print("=" * 150)

    # 用于控制输出频率
    last_print_time = time.time()
    print_interval = 0.1  # 10Hz 输出

    while not stop_flag[0]:
        current_time = time.time()
        if current_time - last_print_time >= print_interval:
            acc = my_ego.get_accelerometer()
            gyr = my_ego.get_gyroscope()
            mag = my_ego.get_magnetometer()
            quat = my_ego.get_quaternion()

            # 从四元数计算欧拉角
            w, x, y, z = quat
            roll, pitch, yaw = quaternion_to_euler(w, x, y, z)
            euler_str = f"Euler(计算): [R:{roll:7.3f}, P:{pitch:7.3f}, Y:{yaw:7.3f}]"
            quat_str = f"Quat: [w:{w:6.3f}, x:{x:6.3f}, y:{y:6.3f}, z:{z:6.3f}]"

            print(
                f"\rAcc: [{acc[0]:7.3f}, {acc[1]:7.3f}, {acc[2]:7.3f}] | "
                f"Gyr: [{gyr[0]:7.3f}, {gyr[1]:7.3f}, {gyr[2]:7.3f}] | "
                f"Mag: [{mag[0]:7.1f}, {mag[1]:7.1f}, {mag[2]:7.1f}] | "
                f"{euler_str} | "
                f"{quat_str}",
                end='',
                flush=True
            )
            last_print_time = current_time
        time.sleep(0.001)


def main():
    print("===== Pika Ego 相机和IMU测试 =====")

    # 创建 Ego 设备对象
    # 注意：请根据实际情况修改串口设备路径和相机索引
    my_ego = ego('/dev/ttyUSB81')

    # 设置鱼眼相机索引
    my_ego.set_fisheye_camera_index(81)

    # 设置 RealSense 相机序列号
    my_ego.set_realsense_serial_number('260422273747')

    # 连接设备
    print("\n正在连接设备...")
    if not my_ego.connect():
        print("连接设备失败，请检查串口路径和设备连接")
        return

    print("设备连接成功！")

    # 获取鱼眼相机
    print("\n正在初始化鱼眼相机...")
    fisheye_camera = my_ego.get_fisheye_camera()
    if not fisheye_camera:
        print("警告: 无法初始化鱼眼相机")

    # 获取 RealSense 相机
    print("正在初始化 RealSense 相机...")
    realsense_camera = my_ego.get_realsense_camera()
    if not realsense_camera:
        print("警告: 无法初始化 RealSense 相机")

    # 启动 IMU 输出线程
    stop_flag = [False]
    imu_thread = threading.Thread(target=print_imu_data, args=(my_ego, stop_flag))
    imu_thread.daemon = True
    imu_thread.start()

    print("\n相机窗口已打开，按 'q' 退出")
    print("=" * 80)

    try:
        while True:
            # 显示鱼眼相机画面
            if fisheye_camera:
                success, fisheye_frame = fisheye_camera.get_frame()
                if success and fisheye_frame is not None:
                    cv2.imshow('Fisheye Camera', fisheye_frame)

            # 显示 RealSense 画面
            if realsense_camera:
                success, color_frame, depth_frame = realsense_camera.get_frames()
                if success and color_frame is not None:
                    cv2.imshow('RealSense Color', color_frame)

                    if depth_frame is not None:
                        # 将深度图归一化以便显示
                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_frame, alpha=0.03),
                            cv2.COLORMAP_JET
                        )
                        cv2.imshow('RealSense Depth', depth_colormap)

            # 检测按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n运行异常: {e}")
    finally:
        # 停止 IMU 输出线程
        stop_flag[0] = True
        time.sleep(0.2)

        # 关闭所有 OpenCV 窗口
        cv2.destroyAllWindows()

        # 断开连接
        print("\n\n正在断开设备连接...")
        my_ego.disconnect()
        print("设备已断开")

    print("\n===== 测试结束 =====")


if __name__ == "__main__":
    main()
