#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper example.
Demonstrates how to quickly open the camera and save images.
"""

import cv2
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
    my_gripper.set_camera_param(640, 480, 30)
    # Set fisheye camera index
    my_gripper.set_fisheye_camera_index(81)
    # Set RealSense camera serial number
    my_gripper.set_realsense_serial_number('230322275885')
    # Get fisheye camera object
    fisheye_camera = my_gripper.get_fisheye_camera()
    # Get RealSense camera object
    realsense_camera = my_gripper.get_realsense_camera()
    
    while True:
        if fisheye_camera:
                print("\nAttempting to capture fisheye camera image...")
                success, frame = fisheye_camera.get_frame()
                if success and frame is not None:
                    print("Successfully captured fisheye camera image.")
                    cv2.imshow("Fisheye Camera", frame)
                    cv2.imwrite("gripper_fisheye_image.jpg", frame)
                    print("Saved fisheye camera image to gripper_fisheye_image.jpg")
                else:
                    print("Failed to capture fisheye camera image or frame is empty.")
        else:
            print("Failed to get fisheye camera object, skipping image capture.")

        if realsense_camera:
            print("\nAttempting to capture RealSense camera images...")
            success_color, color_frame = realsense_camera.get_color_frame()
            if success_color and color_frame is not None:
                print("Successfully captured RealSense color image.")
                cv2.imshow("RealSense Color", color_frame)
                cv2.imwrite("gripper_realsense_color.jpg", color_frame)
                print("Saved RealSense color image to gripper_realsense_color.jpg")
            else:
                print("Failed to capture RealSense color image or frame is empty.")
            
            success_depth, depth_frame = realsense_camera.get_depth_frame()
            if success_depth and depth_frame is not None:
                print("Successfully captured RealSense depth image.")
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=0.03), cv2.COLORMAP_JET)
                cv2.imshow("RealSense Depth", depth_colormap)
                cv2.imwrite("gripper_realsense_depth.jpg", depth_colormap)
                print("Saved RealSense depth image to gripper_realsense_depth.jpg")
            else:
                print("Failed to capture RealSense depth image or frame is empty.")
        else:
            print("Failed to get RealSense camera object, skipping image capture.")

        cv2.waitKey(1) 
        
if __name__ == "__main__":
    main()
