#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Sense example.
Demonstrates basic usage of the Pika Sense device.
"""

import time
import cv2
import numpy as np
from pika import sense

def main():
    # Create Sense object and connect
    print("Connecting to Pika Sense device...")
    my_sense = sense('/dev/ttyUSB81')  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_sense.connect():
        print("Failed to connect to Pika Sense. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Sense device.")
    
    # Set camera parameters
    my_sense.set_camera_param(640, 480, 30)
    # Set fisheye camera index
    my_sense.set_fisheye_camera_index(81)
    # Set RealSense camera serial number
    my_sense.set_realsense_serial_number('230322270988')
    
    try:
        # Loop to fetch data
        for i in range(100):  # Fetch data 100 times
            # Get encoder data
            encoder_data = my_sense.get_encoder_data()
            print("\n--- Encoder Data ---")
            print(f"Angle: {encoder_data['angle']:.2f}°")
            print(f"Radians: {encoder_data['rad']:.2f} rad")
            
            # Get command state
            command_state = my_sense.get_command_state()
            print(f"\nCommand state: {command_state}")
            
            # Try to capture fisheye camera image
            try:
                fisheye_camera = my_sense.get_fisheye_camera()
                if fisheye_camera:
                    success, frame = fisheye_camera.get_frame()
                    print("Camera info:", fisheye_camera.get_camera_info())
                    if success:
                        print("\nSuccessfully captured fisheye camera image.")
                        # Display image
                        cv2.imshow('Fisheye Camera', frame)
                        cv2.waitKey(1)
                        
                        # Save one image
                        if i == 0:
                            cv2.imwrite('fisheye_image.jpg', frame)
                            print("Saved fisheye camera image to fisheye_image.jpg")
            except Exception as e:
                print(f"Error capturing fisheye camera image: {e}")
            
            # Try to capture RealSense camera images
            try:
                realsense_camera = my_sense.get_realsense_camera()
                if realsense_camera:
                    success, color_frame = realsense_camera.get_color_frame()
                    print("D405 camera info:", realsense_camera.get_camera_info())
                    if success:
                        print("\nSuccessfully captured RealSense color image.")
                        # Display image
                        cv2.imshow('RealSense Color', color_frame)
                        cv2.waitKey(1)
                        
                        # Save one image
                        if i == 0:
                            cv2.imwrite('realsense_color.jpg', color_frame)
                            print("Saved RealSense color image to realsense_color.jpg")
                    
                    success, depth_frame = realsense_camera.get_depth_frame()
                    if success:
                        print("\nSuccessfully captured RealSense depth image.")
                        # Normalize depth image for display
                        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=0.03), cv2.COLORMAP_JET)
                        # Display image
                        cv2.imshow('RealSense Depth', depth_colormap)
                        cv2.waitKey(1)
                        
                        # Save one image
                        if i == 0:
                            cv2.imwrite('realsense_depth.jpg', depth_colormap)
                            print("Saved RealSense depth image to realsense_depth.jpg")
            except Exception as e:
                print(f"Error capturing RealSense camera image: {e}")
            
            # Wait before next iteration
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting.")
    except Exception as e:
        print(f"\nProgram error: {e}")
    finally:
        # Disconnect
        print("\nDisconnecting Pika Sense device.")
        my_sense.disconnect()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
