#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper example.
Demonstrates basic usage of the Pika Gripper device.
"""

import time
import cv2
import numpy as np
from pika.gripper import Gripper

def main():
    # Create Gripper object and connect
    print("Connecting to Pika Gripper device...")
    my_gripper = Gripper("/dev/ttyUSB81")  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_gripper.connect():
        print("Failed to connect to Pika Gripper. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Gripper device.")
        
    # Set camera parameters
    my_gripper.set_camera_param(1280, 720, 30)
    # Set fisheye camera index
    my_gripper.set_fisheye_camera_index(81)
    # Set RealSense camera serial number
    my_gripper.set_realsense_serial_number('230322275885')
    
    try:
        # Get initial motor status
        print("\n--- Initial Motor Status ---")
        initial_voltage = my_gripper.get_voltage()
        initial_driver_temp = my_gripper.get_driver_temp()
        initial_motor_temp = my_gripper.get_motor_temp()
        initial_status_raw = my_gripper.get_status_raw()
        initial_bus_current = my_gripper.get_bus_current()
        print(f"Driver voltage: {initial_voltage:.1f} V")
        print(f"Driver temperature: {initial_driver_temp} °C")
        print(f"Motor temperature: {initial_motor_temp} °C")
        print(f"Driver status (raw): {initial_status_raw}")
        print(f"Bus current: {initial_bus_current} mA")

        # Enable motor
        print("\nEnabling motor...")
        if my_gripper.enable():
            print("Motor enabled successfully.")
        else:
            print("Failed to enable motor.")
            # Consider exiting if enable fails; subsequent operations may not work
        
        # Wait for motor to enable
        time.sleep(1)
        
        # Get updated motor status (mainly raw status code change)
        print("\n--- Updated Motor Status ---")
        updated_status_raw = my_gripper.get_status_raw()
        print(f"Driver status (raw): {updated_status_raw}")

        # Get motor data
        print("\n--- Initial Motor Data ---")
        position_rad = my_gripper.get_motor_position()
        position_deg = position_rad * 180 / np.pi 
        gripper_distance = my_gripper.get_gripper_distance()
        speed_rad_s = my_gripper.get_motor_speed()
        current_ma = my_gripper.get_motor_current()
        print(f"Position (rad): {position_rad:.2f} rad")
        print(f"Position (deg): {position_deg:.2f}°")
        print(f"Position (mm): {gripper_distance:.2f} mm")
        print(f"Speed: {speed_rad_s:.2f} rad/s")
        print(f"Current: {current_ma} mA")
        
        # # Set zero point
        # print("\nSetting zero point...")
        # if my_gripper.set_zero():
        #     print("Zero point set successfully.")
        # else:
        #     print("Failed to set zero point.")
        
        # # Wait for setting to take effect
        # time.sleep(1)
        
        # Test different gripper opening distances (mm)
        test_distance = [0, 30, 60, 90, 60, 30, 0]
        for gripper_distance in test_distance:
            print(f"\nSetting target distance: {gripper_distance} mm")
            if my_gripper.set_gripper_distance(gripper_distance):
                print(f"Target distance {gripper_distance} mm set successfully.")
            else:
                print(f"Failed to set target distance {gripper_distance} mm.")
            
            # Wait for motor to move
            time.sleep(2)
            
            # Get current motor position
            current_gripper_distance  = my_gripper.get_gripper_distance()
            current_pos_rad_after_set = my_gripper.get_motor_position()
            current_pos_deg_after_set = current_pos_rad_after_set * 180 / np.pi
            print(f"Current position (mm): {current_gripper_distance:.2f} mm")
            print(f"Current position (deg): {current_pos_deg_after_set:.2f}°")
            print(f"Current position (rad): {current_pos_rad_after_set:.2f} rad")
            
        # Try to capture fisheye camera image
        try:
            fisheye_camera = my_gripper.get_fisheye_camera()
            if fisheye_camera:
                print("\nAttempting to capture fisheye camera image...")
                success, frame = fisheye_camera.get_frame()
                if success and frame is not None:
                    print("Successfully captured fisheye camera image.")
                    cv2.imshow("Fisheye Camera", frame)
                    cv2.waitKey(1000)  # Display for 1 second
                    cv2.imwrite("gripper_fisheye_image.jpg", frame)
                    print("Saved fisheye camera image to gripper_fisheye_image.jpg")
                else:
                    print("Failed to capture fisheye camera image or frame is empty.")
            else:
                print("Failed to get fisheye camera object, skipping image capture.")
        except Exception as e:
            print(f"Error capturing fisheye camera image: {e}")
        
        # Try to capture RealSense camera images
        try:
            realsense_camera = my_gripper.get_realsense_camera()
            if realsense_camera:
                print("\nAttempting to capture RealSense camera images...")
                success_color, color_frame = realsense_camera.get_color_frame()
                if success_color and color_frame is not None:
                    print("Successfully captured RealSense color image.")
                    cv2.imshow("RealSense Color", color_frame)
                    cv2.waitKey(1000)  # Display for 1 second
                    cv2.imwrite("gripper_realsense_color.jpg", color_frame)
                    print("Saved RealSense color image to gripper_realsense_color.jpg")
                else:
                    print("Failed to capture RealSense color image or frame is empty.")
                
                success_depth, depth_frame = realsense_camera.get_depth_frame()
                if success_depth and depth_frame is not None:
                    print("Successfully captured RealSense depth image.")
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=0.03), cv2.COLORMAP_JET)
                    cv2.imshow("RealSense Depth", depth_colormap)
                    cv2.waitKey(1000)  # Display for 1 second
                    cv2.imwrite("gripper_realsense_depth.jpg", depth_colormap)
                    print("Saved RealSense depth image to gripper_realsense_depth.jpg")
                else:
                    print("Failed to capture RealSense depth image or frame is empty.")
            else:
                print("Failed to get RealSense camera object, skipping image capture.")
        except Exception as e:
            print(f"Error capturing RealSense camera image: {e}")
        
        # Disable motor
        print("\nDisabling motor...")
        if my_gripper.disable():
            print("Motor disabled successfully.")
        else:
            print("Failed to disable motor.")
        
        # Wait for motor to disable
        time.sleep(1)
        
        # Get final motor status
        final_status_raw = my_gripper.get_status_raw()
        print(f"Final driver status (raw): {final_status_raw}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting.")
    except Exception as e:
        print(f"\nProgram error: {e}")
    finally:
        # Disconnect
        print("\nDisconnecting Pika Gripper device.")
        my_gripper.disconnect()
        cv2.destroyAllWindows()
        print("All OpenCV windows closed.")

if __name__ == "__main__":
    main()
