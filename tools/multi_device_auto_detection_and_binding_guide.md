# Multi-Device Auto-Detection and Binding Tool Guide

<p align="center">
  <a> English </a> | <a href="多设备自动检测与绑定工具使用说明.md">中文</a>
</p>

## Overview

This tool is designed for Pika devices. Based on the number of devices you specify, it guides you to connect devices one at a time and automatically detects and binds each device. Main features include:

1. Support for configuring any number of Pika devices
2. Automatic detection of each device's RealSense camera serial number
3. Automatic detection of each device's ttyUSB port
4. Interactive detection of each device's fisheye camera
5. Automatic generation of udev rules to bind devices to fixed ports

## Usage

### Prerequisites

For best results, make sure the following packages are installed:

```bash
# 1. Install v4l-utils (for video device detection)
sudo apt install v4l-utils

# 2. Install RealSense SDK tools (for RealSense camera detection)

# 3. Install OpenCV (for camera image capture)
pip install opencv-python
```

### Running the Script

1. Make sure all Pika devices are disconnected
2. Run the script:

```bash
cd pika_sdk
python3 tools/multi_device_detector.py
```

3. Follow the on-screen prompts:
   - Enter the number of devices to configure
   - Connect each device one at a time and press Enter to continue
   - When a camera preview is shown, press `s` to select the fisheye camera or `q` to skip
   - After all devices are detected, choose whether to apply the rules immediately

### Workflow

1. When the script starts, it first checks whether required tools are installed
2. Enter the number of devices to configure (e.g., 3)
3. Connect the 1st device and press Enter to continue
4. The script automatically detects the RealSense serial number and ttyUSB port for the 1st device
5. The script displays available camera previews; press `s` when you see the fisheye camera, or `q` to skip non-fisheye cameras
6. Disconnect the 1st device, connect the 2nd device, and press Enter to continue
7. Repeat steps 4–5 until all devices are detected
8. The script generates configuration files and asks whether to apply the rules immediately
9. If you choose to apply the rules, the script automatically sets up the udev rules

## Optimization Updates

The script has been optimized with the following improvements:

1. **Camera detection interaction**:
   - The preview stays on the current video device until you press `q` or `s`
   - Press `q` to skip the current camera; press `s` to select it as the fisheye camera

2. **Device numbering**:
   - All device numbers start from 80
   - 1st device: ttyUSB81, video81
   - 2nd device: ttyUSB82, video82
   - And so on...

3. **Expanded video device matching range**:
   - Video device matching range extended to video0–video60
   - Supports more video device types

4. **Simplified output files**:
   - Removed example code generation; only essential configuration files are kept
   - Generated files are more concise and practical

## Generated Files

After the script runs, the following files are generated:

1. **setup.bash**: Device binding rules script for setting up udev rules
2. **devices_info.conf**: Device information configuration file containing details for all devices

## Device Binding Rules

The script assigns fixed device paths to each device:

- 1st device: ttyUSB81, video81
- 2nd device: ttyUSB82, video82
- 3rd device: ttyUSB83, video83
- And so on...

## Using Bound Devices with Pika SDK

```python
from pika import sense

# Use the 1st device
device1 = sense('/dev/ttyUSB81')
device1.connect()
device1.set_fisheye_camera_index(81)  # Use the fisheye camera of the 1st device

# Use the 2nd device
device2 = sense('/dev/ttyUSB82')
device2.connect()
device2.set_fisheye_camera_index(82)  # Use the fisheye camera of the 2nd device

# Disconnect when done
device1.disconnect()
device2.disconnect()
```

## Notes

1. During device detection, connect only one device at a time
2. After binding, each device must be plugged into the same USB port used during detection
3. If a device is plugged into a different USB port, the binding rules may not apply correctly
4. To reconfigure, simply run the script again
5. If something goes wrong during detection, press Ctrl+C to interrupt the script and run it again
