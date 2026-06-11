#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Gripper example.
Demonstrates how to query Pika Gripper firmware version information.
"""

import time
from pika.gripper import Gripper

def main():
    # Create Gripper object and connect
    print("Connecting to Pika Gripper device...")
    my_gripper = Gripper("/dev/ttyUSB0")  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_gripper.connect():
        print("Failed to connect to Pika Gripper. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Gripper device.")
    print("Fetching version information...")
    
    # Send get_version() every 0.1 seconds, 5 times
    for _ in range(5):
        my_gripper.get_version()
        # Sleep 0.1 seconds waiting for response
        time.sleep(0.1)


if __name__ == "__main__":
    main()
