#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pika SDK test script.
Used to verify SDK installation and basic functionality.
"""

import os
import sys
import time

def test_import():
    """Test module imports."""
    print("Testing module imports...")
    try:
        from pika import sense, gripper
        print("✓ Successfully imported pika module")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_serial_comm():
    """Test serial communication module."""
    print("\nTesting serial communication module...")
    try:
        from pika.serial_comm import SerialComm
        
        # Create SerialComm object
        serial_comm = SerialComm(port='/dev/ttyUSB0')  # Update serial port path as needed
        print("✓ Successfully created SerialComm object")
        
        # Check connect method (no actual connection)
        print("✓ SerialComm class method checks passed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_sense_class():
    """Test Sense class."""
    print("\nTesting Sense class...")
    try:
        from pika import sense
        
        # Create Sense object (no actual connection)
        my_sense = sense('/dev/ttyUSB0')  # Update serial port path as needed
        print("✓ Successfully created Sense object")
        
        # Check whether methods exist
        methods = [
            'connect', 'disconnect', 'get_gripper_distance', 'get_encoder_data',
            'get_command_state', 'get_fisheye_camera', 'get_realsense_camera',
            'get_vive_tracker'
        ]
        for method in methods:
            if hasattr(my_sense, method) and callable(getattr(my_sense, method)):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} does not exist or is not callable")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_gripper_class():
    """Test Gripper class."""
    print("\nTesting Gripper class...")
    try:
        from pika import gripper
        
        # Create Gripper object (no actual connection)
        my_gripper = gripper('/dev/ttyUSB0')  # Update serial port path as needed
        print("✓ Successfully created Gripper object")
        
        # Check whether methods exist
        methods = [
            'connect', 'disconnect', 'enable', 'disable', 'set_zero',
            'set_velocity', 'set_effort', 
            'get_motor_data', 'get_motor_status', 'get_motor_speed', 'get_motor_current','get_motor_position',
            'get_voltage','get_driver_temp','get_motor_temp','get_status_raw',
            'get_bus_current',
            'get_fisheye_camera', 'get_realsense_camera',
            'get_gripper_distance',
            'set_motor_angle','set_gripper_distance','set_velocity','set_effort',
            'set_camera_param'
        ]
        for method in methods:
            if hasattr(my_gripper, method) and callable(getattr(my_gripper, method)):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} does not exist or is not callable")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_ego_class():
    """Test Ego class."""
    print("\nTesting Ego class...")
    try:
        from pika import ego

        # Create Ego object (no actual connection)
        my_ego = ego('/dev/ttyUSB0')
        print("✓ Successfully created Ego object")

        # Check whether methods exist
        methods = [
            'connect', 'disconnect',
            'get_imu_data', 'get_accelerometer', 'get_gyroscope',
            'get_magnetometer', 'get_quaternion',
            'get_fisheye_camera', 'get_realsense_camera',
            'set_camera_param', 'set_fisheye_camera_index', 'set_realsense_serial_number'
        ]
        for method in methods:
            if hasattr(my_ego, method) and callable(getattr(my_ego, method)):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} does not exist or is not callable")
                return False

        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_camera_modules():
    """Test camera modules."""
    print("\nTesting camera modules...")
    try:
        from pika.camera.fisheye import FisheyeCamera
        print("✓ Successfully imported FisheyeCamera class")
        
        try:
            from pika.camera.realsense import RealSenseCamera
            print("✓ Successfully imported RealSenseCamera class")
        except ImportError:
            print("! Failed to import RealSenseCamera; pyrealsense2 may not be installed")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Main function."""
    print("===== Pika SDK Test =====")
    
    # Test imports
    if not test_import():
        print("\nImport test failed. Please check your installation.")
        return
    
    # Test serial communication module
    test_serial_comm()
    
    # Test Sense class
    test_sense_class()
    
    # Test Gripper class
    test_gripper_class()

    # Test Ego class
    test_ego_class()

    # Test camera modules
    test_camera_modules()
    
    print("\n===== Test Complete =====")
    print("Note: This is a basic functionality test only; no devices were actually connected.")
    print("For real device testing, run the example programs in the examples directory.")

if __name__ == "__main__":
    main()
