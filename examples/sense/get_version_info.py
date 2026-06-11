#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika Sense example.
Demonstrates how to query Pika Sense firmware version information.
"""

import time
from pika import sense

def main():
    # Create Sense object and connect
    print("Connecting to Pika Sense device...")
    my_sense = sense('/dev/ttyUSB0')  # Update serial port path as needed; default: /dev/ttyUSB0
    
    if not my_sense.connect():
        print("Failed to connect to Pika Sense. Please check device connection and serial port path.")
        return
    
    print("Successfully connected to Pika Sense device.")
    print("Fetching version information...")
    # Send get_version() every 0.1 seconds, 5 times
    for _ in range(5):
        my_sense.get_version()
        # Sleep 0.1 seconds waiting for response
        time.sleep(0.1)


if __name__ == "__main__":
    main()
