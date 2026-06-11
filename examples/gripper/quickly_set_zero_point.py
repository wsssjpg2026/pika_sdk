#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper example.
Demonstrates how to set the Gripper zero point.
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
    
    # Set zero point
    print("\nSetting zero point...")
    if my_gripper.set_zero():
        print("Zero point set successfully.")
    else:
        print("Failed to set zero point.")
    
    # Wait for setting to take effect
    time.sleep(1)

if __name__ == "__main__":
    main()
