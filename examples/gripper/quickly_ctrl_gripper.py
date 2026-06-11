#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper example.
Demonstrates how to control the gripper.
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
    
    # Enable motor
    print("\nEnabling motor...")
    if my_gripper.enable():
        print("Motor enabled successfully.")
    else:
        print("Failed to enable motor.")
        # Consider exiting if enable fails; subsequent operations may not work
    
    # Wait for motor to enable
    time.sleep(1)
    
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
        current_gripper_distance = my_gripper.get_gripper_distance()
        current_pos_rad_after_set = my_gripper.get_motor_position()
        current_pos_deg_after_set = current_pos_rad_after_set * 180 / np.pi
        print(f"Current position (mm): {current_gripper_distance:.2f} mm")
        print(f"Current position (deg): {current_pos_deg_after_set:.2f}°")
        print(f"Current position (rad): {current_pos_rad_after_set:.2f} rad")

if __name__ == "__main__":
    main()
