#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Ego camera and IMU test example.
Opens fisheye camera, RealSense color/depth cameras, and prints IMU data to the terminal.
"""

import cv2
import math
import time
import sys
import threading
from collections import deque

# Add SDK path
sys.path.insert(0, '../..')

from pika import ego


def quaternion_to_euler(w, x, y, z):
    """
    Convert quaternion to Euler angles (roll, pitch, yaw).

    Args:
        w, x, y, z: Quaternion components.

    Returns:
        roll, pitch, yaw: Euler angles in radians.
    """
    # Normalize quaternion
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
    """Print IMU data to the terminal."""
    print("\n===== IMU Data Output =====")
    print("Format: Acceleration | Angular Velocity | Magnetometer | Euler (computed) | Quaternion")
    print("=" * 150)

    # Control output rate
    last_print_time = time.time()
    print_interval = 0.1  # 10 Hz output

    while not stop_flag[0]:
        current_time = time.time()
        if current_time - last_print_time >= print_interval:
            acc = my_ego.get_accelerometer()
            gyr = my_ego.get_gyroscope()
            mag = my_ego.get_magnetometer()
            quat = my_ego.get_quaternion()

            # Compute Euler angles from quaternion
            w, x, y, z = quat
            roll, pitch, yaw = quaternion_to_euler(w, x, y, z)
            euler_str = f"Euler(computed): [R:{roll:7.3f}, P:{pitch:7.3f}, Y:{yaw:7.3f}]"
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
    print("===== Pika Ego Camera and IMU Test =====")

    # Create Ego device object
    # Note: Update serial port path and camera index for your setup
    my_ego = ego('/dev/ttyUSB81')

    # Set fisheye camera index
    my_ego.set_fisheye_camera_index(81)

    # Set RealSense camera serial number
    my_ego.set_realsense_serial_number('260422273747')

    # Connect device
    print("\nConnecting to device...")
    if not my_ego.connect():
        print("Failed to connect. Please check serial port path and device connection.")
        return

    print("Device connected successfully!")

    # Get fisheye camera
    print("\nInitializing fisheye camera...")
    fisheye_camera = my_ego.get_fisheye_camera()
    if not fisheye_camera:
        print("Warning: Failed to initialize fisheye camera.")

    # Get RealSense camera
    print("Initializing RealSense camera...")
    realsense_camera = my_ego.get_realsense_camera()
    if not realsense_camera:
        print("Warning: Failed to initialize RealSense camera.")

    # Start IMU output thread
    stop_flag = [False]
    imu_thread = threading.Thread(target=print_imu_data, args=(my_ego, stop_flag))
    imu_thread.daemon = True
    imu_thread.start()

    print("\nCamera windows opened. Press 'q' to quit.")
    print("=" * 80)

    try:
        while True:
            # Display fisheye camera feed
            if fisheye_camera:
                success, fisheye_frame = fisheye_camera.get_frame()
                if success and fisheye_frame is not None:
                    cv2.imshow('Fisheye Camera', fisheye_frame)

            # Display RealSense feed
            if realsense_camera:
                success, color_frame, depth_frame = realsense_camera.get_frames()
                if success and color_frame is not None:
                    cv2.imshow('RealSense Color', color_frame)

                    if depth_frame is not None:
                        # Normalize depth map for display
                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_frame, alpha=0.03),
                            cv2.COLORMAP_JET
                        )
                        cv2.imshow('RealSense Depth', depth_colormap)

            # Check key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nRuntime error: {e}")
    finally:
        # Stop IMU output thread
        stop_flag[0] = True
        time.sleep(0.2)

        # Close all OpenCV windows
        cv2.destroyAllWindows()

        # Disconnect
        print("\n\nDisconnecting device...")
        my_ego.disconnect()
        print("Device disconnected.")

    print("\n===== Test Complete =====")


if __name__ == "__main__":
    main()
