#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vive Tracker module - retrieve pose data for the WM0 device on Pika Ego.
Ego applies translation only (+X 33.27 mm, -Z 39 mm); no rotation.
"""

import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_vive_tracker_ego')

try:
    from pika.ego import Ego

    def test_vive_tracker_wm0():
        """Test retrieving pose data for the WM0 device."""
        logger.info("Starting to retrieve WM0 device pose data...")

        # Initialize Ego object
        my_ego = Ego()

        # Connect device
        logger.info("Connecting to Ego device...")
        if not my_ego.connect():
            logger.error("Failed to connect to Ego device.")
            return False

        # Configure Vive Tracker (optional)
        # my_ego.set_vive_tracker_config(config_path="path/to/config", lh_config="lighthouse_config")

        try:
            # Get Vive Tracker object (applies Ego translation-only transform)
            logger.info("Getting Vive Tracker object...")
            tracker = my_ego.get_vive_tracker()

            if not tracker:
                logger.error("Failed to get Vive Tracker object. Please ensure pysurvive is installed.")
                return False

            # Wait for device initialization
            logger.info("Waiting for device initialization...")
            time.sleep(2.0)  # Wait 2 seconds

            # Get all tracking devices
            logger.info("Getting tracking device list...")
            devices = my_ego.get_tracker_devices()
            logger.info(f"Detected devices: {devices}")

            # Check for WM0 device; retry if not found
            target_device = "WM0"
            retry_count = 0
            max_retries = 10

            while target_device not in devices and retry_count < max_retries:
                logger.info(f"{target_device} not detected, waiting and retrying ({retry_count+1}/{max_retries})...")
                time.sleep(1.0)
                devices = my_ego.get_tracker_devices()
                logger.info(f"Detected devices: {devices}")
                retry_count += 1

            if target_device not in devices:
                logger.warning(f"{target_device} not detected after multiple attempts.")
                logger.info("Please ensure the device is connected and recognized correctly.")
                return False

            logger.info(f"Successfully detected {target_device} device!")

            # Loop to retrieve WM0 pose data
            logger.info(f"Starting to retrieve pose data for {target_device}...")
            for i in range(20):  # Retrieve data 20 times
                # Get WM0 pose data
                pose = my_ego.get_pose(target_device)

                if pose:
                    logger.info(f"Data #{i+1}: {target_device} - Position: {pose.position}, Rotation: {pose.rotation}")

                    # Extract position and rotation for further processing
                    position = pose.position  # [x, y, z]
                    rotation = pose.rotation  # [x, y, z, w] quaternion

                    # Example: compute sum of squared position (for distance calculation)
                    distance_squared = sum([p*p for p in position])
                    logger.info(f"Distance squared from origin: {distance_squared:.6f}")

                    # Example: extract individual quaternion components
                    x, y, z, w = rotation
                    logger.info(f"Quaternion components: x={x:.6f}, y={y:.6f}, z={z:.6f}, w={w:.6f}")

                else:
                    logger.warning(f"Failed to get pose data for {target_device}, waiting for next attempt...")

                time.sleep(0.2)  # Retrieve every 0.2 seconds

            logger.info(f"Pose data retrieval for {target_device} complete.")
            return True

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return False
        finally:
            # Disconnect
            logger.info("Disconnecting Ego device...")
            my_ego.disconnect()

    if __name__ == "__main__":
        test_vive_tracker_wm0()

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please ensure all required dependencies are installed, including pysurvive.")
