#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Sense example.
Demonstrates how to control Sense lights and vibration motor.
"""

import time
import numpy as np
from pika import sense

def main():
    # Create Sense object and connect
    print("Connecting to Pika Sense device...")
    my_sense = sense('/dev/ttyUSB0')  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_sense.connect():
        print("Failed to connect to Pika Sense. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Sense device.")
    
    print("Running light control sequence...")
    print("White light on for 2 seconds...")
    my_sense.light_ctrl(0)
    time.sleep(2)
    
    print("Red light on for 2 seconds...")
    my_sense.light_ctrl(1)
    time.sleep(2)
    
    print("Green light on for 2 seconds...")
    my_sense.light_ctrl(2)
    time.sleep(2)
    
    print("Blue light on for 2 seconds...")
    my_sense.light_ctrl(3)
    time.sleep(2)
    
    print("Yellow light on for 2 seconds...")
    my_sense.light_ctrl(4)
    time.sleep(2)
    
    print("Running vibration motor sequence...")
    print("Vibrating for 2 seconds...")
    my_sense.vibrate_ctrl(1)
    time.sleep(2)
    print("Turning off vibration motor...")
    my_sense.vibrate_ctrl(0)


if __name__ == "__main__":
    main()
