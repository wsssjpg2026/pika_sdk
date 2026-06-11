#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Sense example.
Demonstrates controlling a Pika Gripper using Pika Sense encoder data.
"""

import time
import cv2
import numpy as np
from pika import sense
from pika.gripper import Gripper

def main():
    # Create Sense object and connect
    print("Connecting to Pika Sense device...")
    my_sense = sense('/dev/ttyUSB0')  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_sense.connect():
        print("Failed to connect to Pika Sense. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Sense device.")
    
    # Create Gripper object and connect
    print("Connecting to Pika Gripper device...")
    my_gripper = Gripper("/dev/ttyUSB1")  # Update serial port path as needed; default: /dev/ttyUSB0
    
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
    
    while True:
        # Angle control mode
        # Get encoder data
        encoder_data = my_sense.get_encoder_data()
        
        gripper_value = my_sense.get_gripper_distance()
        
        print(f"Sense gripper opening distance: {gripper_value:.2f} mm")
        
        motor_data = my_gripper.get_motor_data()
        print(f"Current: {motor_data['Current']} mA")

        # Send Sense angle (radians) directly to Gripper
        my_gripper.set_motor_angle(encoder_data['rad'])
        
        # Wait before next iteration
        time.sleep(0.03)
        
        # # Gripper distance control mode
        # # Get Sense gripper opening distance
        # gripper_value = my_sense.get_gripper_distance()
        # # Map value to Gripper
        # my_gripper.set_gripper_distance(gripper_value)
        # # Wait before next iteration
        # time.sleep(0.03)
    

if __name__ == "__main__":
    main()
