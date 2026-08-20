<div align="center">
  <h1 align="center"> Pika SDK </h1>
  <h3 align="center"> Agilex Robotics </h3>
  <p align="center">
    <a> English </a> | <a href="README_zh-CN.md">中文</a> 
  </p>
</div>
<div align="center">

![ubuntu](https://img.shields.io/badge/Ubuntu-20.04-orange.svg)
![ubuntu](https://img.shields.io/badge/Ubuntu-22.04-orange.svg)
![python](https://img.shields.io/badge/Python-%3C%3D%203.9-blue.svg)

</div>

## Introduction

Pika SDK is a Python software development kit designed for Pika series devices, providing simple yet powerful programming interfaces. The SDK supports two main device types: Pika Sense and Pika Gripper, enabling developers to easily control and access the full functionality of these devices.

If you encounter any issues while using Pika SDK, or have suggestions and feedback, please contact us through the following channels:

- GitHub Issues: https://github.com/agilexrobotics/pika_sdk/issues
- Email: support@agilex.ai

Our technical team will respond to your questions as soon as possible and provide the necessary support.

## Software Environment

- Architecture: x86_64/arm64
- Operating System: Ubuntu 20.04/22.04
- Python version: ≤ 3.9

It should work in other Linux environments, but only the environments listed above are tested regularly.

## Install Dependencies

```bash 
sudo apt update

sudo apt install cmake g++ git v4l-utils  libudev-dev pkg-config libgtk-3-dev build-essential zlib1g-dev libx11-dev libeigen3-dev freeglut3-dev liblapacke-dev libopenblas-dev libpcap-dev libatlas-base-dev libusb-1.0-0-dev pkg-config libglfw3-dev libssl-dev libglu1-mesa-dev python3-pip
```

## Install RealSense SDK

If RealSense SDK is already installed on your system, skip this step.

To check whether RealSense SDK is already installed:

```bash
realsense-viewer
```

If the RealSense Viewer opens, the SDK is already installed—skip this step.

1. Download the package

```bash
git clone https://github.com/IntelRealSense/librealsense
# Or download a specific version
git clone https://github.com/IntelRealSense/librealsense/releases/tag/vxxx   # Note: replace vxxx with the actual version number
```

2. Build and install

```bash
cd librealsense
mkdir build 
cd build
cmake .. -DCHECK_FOR_UPDATES=false
make -j$(nproc)
sudo make install
```

## Install libsurvive

```bash
git clone https://github.com/cntools/libsurvive.git
cd libsurvive
sudo cp ./useful_files/81-vive.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
make
```

## Install SDK

### pip3 Installation

```bash
pip3 install agx-pypika
```

1. During installation, the step `Building wheel for wxpython (setup.py) ...` (compiling `wxPython`) can take a long time—please be patient.

2. Building `wxpython` from source may take half an hour or longer and is prone to errors. The best approach is to use a pre-built version:

```bash
pip3 install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-22.04 wxpython
```

*(Replace `ubuntu-22.04` with your system version)*

### Install from Source

First, obtain the SDK source code. You can clone the GitHub repository or download a compressed archive. If you use Git, run the following commands in your terminal:

```bash
git clone https://github.com/agilexrobotics/pika_sdk.git
cd pika_sdk
```

Next, install the basic dependencies required by the SDK. These libraries are essential for the SDK to run properly:

```bash
pip3 install -r requirements.txt  
```

If downloads are slow, you can use the Tsinghua mirror:

```bash
pip3 install -r requirements.txt  -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple 
```

Finally, install the SDK itself with the following command. The `-e` flag installs in editable/development mode, so changes to the source code take effect immediately without reinstalling:

```bash
pip3 install -e .
```

### Testing

After installation, you can run the SDK's built-in test script to verify that everything is set up correctly:

```bash
python3 test_sdk.py
```

If the test script outputs success messages, the SDK is installed correctly and you can start developing applications with it.

## Multi-Device Auto-Detection and Binding

Pika SDK provides a multi-device auto-detection and binding tool to help you automatically detect and bind devices when multiple Pika devices are connected to the system. For detailed instructions, see [`tools/multi_device_auto_detection_and_binding_guide.md`](tools/multi_device_auto_detection_and_binding_guide.md).

Before running your code, perform device detection and binding first. If devices are not properly bound, you may encounter device open failures.

Run the device detection and binding tool:

```bash
cd pika_sdk
python3 tools/multi_device_detector.py
```

## Example Code

The SDK includes several examples in the `examples` directory, including:

- gripper:
  - `gripper_example.py`: Demonstrates basic usage of the Pika Gripper device
  - `quickly_ctrl_gripper.py`: Demonstrates how to control the gripper
  - `quickly_open_camera.py`: Demonstrates how to quickly open the camera and save images
  - `quickly_set_zero_point.py`: Demonstrates how to set the gripper zero point (calibrate when the gripper travel range is incorrect)

- sense:
  - `sense_example.py`: Demonstrates basic usage of the Pika Sense device
  - `quickly_open_camera.py`: Demonstrates how to quickly open the camera and save images
  - `vive_tracker_example.py`: Retrieves pose information from Pika Sense

- ego:
  - `ego_examples.py`: Demonstrates basic usage of the Pika Ego device
  - `vive_tracker_example.py`: Retrieves pose information from Pika Ego

These examples show basic SDK usage and common features, and can serve as a reference for developing your own applications.

## API Reference

For detailed usage instructions, see [`API_Doc.md`](API_Doc.md).

## Error Handling

Pika SDK uses Python's logging system to record errors and warnings, making debugging and troubleshooting easier for developers. By default, the log level is set to INFO, recording basic operation information and errors. If you need more detailed logs, set the log level to DEBUG:

```python
import logging
logging.getLogger('pika').setLevel(logging.DEBUG)  # Set to DEBUG level for more detailed logs
```

Most methods in the SDK return specific error codes or False values on failure, and log detailed error information. During development, pay close attention to log output to identify and resolve issues promptly.

For common errors such as device not connected or camera initialization failure, the SDK provides clear error messages and handles errors gracefully whenever possible to avoid program crashes.

## Notes

When developing applications with Pika SDK, please keep the following in mind:

1. **Device connection**: Before use, ensure the Pika device is properly connected to your computer and the serial port path (e.g., `/dev/ttyUSB0`) is correct. If you are unsure of the device path, run `ls /dev/ttyUSB*` on Linux to list available devices.

2. **Resource cleanup**: After use, always call the `disconnect()` method to release resources. This is especially important for hardware resources such as cameras; otherwise, resource leaks or device lock-ups may occur.

3. **RealSense camera**: Using RealSense camera features requires the pyrealsense2 library. If you do not need depth camera functionality, you can skip installing this library—the SDK will automatically fall back to using only the fisheye camera.

4. **Vive Tracker**: Using Vive Tracker features requires the pysurvive library. Ensure SteamVR and base stations are properly installed and configured.

5. **Permissions**: If you encounter serial port access permission issues, add your user to the dialout group: `sudo usermod -a -G dialout $USER`. You must log out and back in for the permission change to take effect.

6. **Camera device ID**: Fisheye camera device IDs may vary depending on system configuration and connection order. If the default ID cannot access the camera, use the `set_fisheye_camera_index()` method to set the correct device ID.

7. **RealSense serial number**: RealSense cameras can be uniquely identified by serial number. If multiple RealSense cameras are connected, use the `set_realsense_serial_number()` method to specify which camera to use.

8. **Thread safety**: The SDK uses internal thread locks to ensure thread-safe data access, but in multi-threaded applications, still be mindful of potential issues from concurrent access.

9. **Error handling**: In production environments, check for errors and handle exceptions for all operations that may fail, to ensure application stability and reliability.

10. **Performance**: Processing image and depth data can require significant compute resources, especially at high resolution and frame rates. Set camera parameters appropriately based on your application requirements and hardware capabilities.

By following these guidelines, you can use Pika SDK more smoothly to develop applications and fully leverage the capabilities of Pika devices.
