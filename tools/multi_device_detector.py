#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Multi-device auto-detection and binding tool.

Purpose: Based on the number of devices specified by the user, guides the user
to connect devices one at a time and automatically detects and binds each device.
Output: Generates udev rule files to bind devices to fixed ports.
Usage: Run this script directly: python3 multi_device_detector.py
"""

import subprocess
import re
import os
import cv2
import time
import sys

def run_command(command):
    """
    Run a shell command and return the output.

    Args:
        command: Shell command to execute.

    Returns:
        Standard output of the command, or None on error.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command: {str(e)}")
        print(f"执行命令时出错: {str(e)}")
        return None

def get_device_info(device_index):
    """
    Get device information, including RealSense serial number, ttyUSB path,
    and fisheye camera path.

    Args:
        device_index: Device index used for display prompts.

    Returns:
        (serial_number, usb_path, video_path): Device serial number, USB path,
        and video device path.
    """
    # Run rs-enumerate-devices to get RealSense camera information
    print(f"\nDetecting RealSense camera for device {device_index}...")
    print(f"\n正在检测第{device_index}个设备的RealSense相机...")
    rs_output = run_command("rs-enumerate-devices -s")
    if not rs_output:
        print("Warning: No RealSense device detected. Please ensure the device is connected correctly.")
        print("警告: 未检测到RealSense设备，请确保设备已正确连接")
        print("Continuing to detect other device information...")
        print("继续尝试检测其他设备信息...")
        serial_number = f"unknown_device_{device_index}"
    else:
        # Parse output to extract serial number
        serial_match = re.search(r'Intel RealSense D405\s+(\d+)', rs_output)
        if not serial_match:
            print("Warning: RealSense D405 not found, trying other models...")
            print("警告: 未找到RealSense D405设备，尝试查找其他型号...")
            # Try matching other possible models
            alt_match = re.search(r'Intel RealSense\s+\w+\s+(\d+)', rs_output)
            if alt_match:
                serial_number = alt_match.group(1)
                print(f"Found other RealSense model, serial number: {serial_number}")
                print(f"找到其他型号RealSense相机，序列号: {serial_number}")
            else:
                print("Warning: No RealSense device serial number found.")
                print("警告: 未找到任何RealSense设备序列号")
                serial_number = f"unknown_device_{device_index}"
        else:
            serial_number = serial_match.group(1)
            print(f"Found RealSense D405 camera, serial number: {serial_number}")
            print(f"找到RealSense D405相机，序列号: {serial_number}")

    # Run udevadm to get ttyUSB device information
    print(f"\nDetecting ttyUSB port for device {device_index}...")
    print(f"\n正在检测第{device_index}个设备的ttyUSB端口...")
    
    # Get all ttyUSB devices
    ttyusb_devices = run_command("ls /dev/ttyUSB*").split()
    if not ttyusb_devices:
        print("Error: No ttyUSB devices detected. Please ensure the device is connected correctly.")
        print("错误: 未检测到任何ttyUSB设备，请确保设备已正确连接")
        return serial_number, None, None
    
    # Use the first ttyUSB device by default
    ttyusb_device = ttyusb_devices[0]
    print(f"Found ttyUSB device: {ttyusb_device}")
    print(f"找到ttyUSB设备: {ttyusb_device}")
    
    # Get device path information
    udev_output = run_command(f"udevadm info {ttyusb_device} | grep DEVPATH")
    if not udev_output:
        print(f"Error: Unable to get device path information for {ttyusb_device}")
        print(f"错误: 无法获取{ttyusb_device}的设备路径信息")
        return serial_number, None, None

    # Parse USB path (e.g. 1-13.2.4:1.0)
    usb_path = udev_output[:udev_output.find("ttyUSB")][:-1]
    usb_path = usb_path[usb_path.rfind("/")+1:]
    print(f"ttyUSB device path: {usb_path}")
    print(f"ttyUSB设备路径: {usb_path}")
    
    print(f"\nSearching for fisheye camera for device {device_index}...")
    print(f"\n正在为第{device_index}个设备寻找鱼眼摄像头...")
    print("Press 's' in the preview window for the fisheye camera, or 'q' for non-fisheye cameras.")
    print("请在出现鱼眼摄像头时在弹出的画面窗口中按下s键，非鱼眼摄像头则按下q键")
    print("Tip: Fisheye cameras usually show circular or distorted images.")
    print("提示: 鱼眼相机通常会显示圆形或畸变的图像")
    
    video_path = None
    # Iterate over possible video devices
    for i in range(60):  # Check the first 60 video devices
        try:
            # OpenCV 4.13.0 lacks setLogLevel; handle compatibility here
            if hasattr(cv2, 'setLogLevel'):
                cv2.setLogLevel(0)
            # Use V4L2 backend to prevent FFMPEG fallback causing device index mismatch
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if not cap.isOpened():
                continue

            # Confirm V4L2 backend
            backend_name = cap.getBackendName()
            if "v4l2" not in backend_name.lower():
                print(f"Skipping non-V4L2 device /dev/video{i}: {backend_name}")
                print(f"跳过非V4L2后端设备 /dev/video{i}: {backend_name}")
                cap.release()
                continue

            # Set camera parameters
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"Detecting port: /dev/video{i}")
            print(f"正在检测端口: /dev/video{i}")
            print("Press 's' to select this camera as the fisheye camera, 'q' to skip.")
            print("按s键选择此相机作为鱼眼相机，按q键跳过此相机")
            
            # Show camera preview and wait for user input
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Draw prompt text on the frame
                cv2.putText(frame, f"/dev/video{i}", (5, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow(f"device {device_index} - /dev/video{i}", frame)
                key = cv2.waitKey(1)
                
                # Press q to skip, s to select current camera
                if key & 0xFF == ord('q'):
                    print(f"Skipping camera /dev/video{i}")
                    print(f"跳过相机 /dev/video{i}")
                    break
                elif key & 0xFF == ord('s'):
                    video_path = f'video{i}'
                    print(f"Selected fisheye camera: /dev/{video_path}")
                    print(f"已选择鱼眼相机: /dev/{video_path}")
                    break
                
            cap.release()
            cv2.destroyAllWindows()
            
            # User selected the current camera
            if video_path:
                break
                
        except Exception as e:
            print(f"Error detecting video device {i}: {str(e)}")
            print(f"检测视频设备 {i} 时出错: {str(e)}")
            continue
    
    # No fisheye camera found
    if video_path is None:
        print("Warning: No fisheye camera found, or user did not select any camera.")
        print("警告: 未找到鱼眼相机，或用户未选择任何相机")
        return serial_number, usb_path, None
    
    # Get USB path for the video device
    udev_output = run_command(f"udevadm info /dev/{video_path} | grep DEVPATH")
    if not udev_output:
        print(f"Warning: Unable to get device path information for /dev/{video_path}")
        print(f"警告: 无法获取 /dev/{video_path} 的设备路径信息")
        return serial_number, usb_path, None
        
    # Parse USB path for the video device
    video_usb_path = udev_output[:udev_output.find("video")][:-1]
    video_usb_path = video_usb_path[video_usb_path.rfind("/")+1:]
    print(f"Fisheye camera USB path: {video_usb_path}")
    print(f"鱼眼相机USB路径: {video_usb_path}")
    
    return serial_number, usb_path, video_usb_path

def generate_setup_bash(devices_info):
    """
    Generate udev rule script for device binding.

    Args:
        devices_info: List of device info tuples
            (index, serial_number, usb_path, video_path).

    Returns:
        Path to the generated script file.
    """
    # Generate file header
    content = """#!/bin/bash
# Auto-generated device binding configuration file
# Generated at: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """

# Clear existing rule files
sudo sh -c 'echo "" > /etc/udev/rules.d/serial.rules'
sudo sh -c 'echo "" > /etc/udev/rules.d/fisheye.rules'

"""

    # Generate serial port rules for each device
    content += "# Serial device binding rules\n"
    for device in devices_info:
        index, serial, usb_path, video_path = device
        if not usb_path:  # Skip invalid USB paths
            continue
            
        tty_index = 80 + index  # Number from ttyUSB80
        content += f'sudo sh -c \'echo "ACTION==\\"add\\", KERNELS==\\"{usb_path}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"ttyUSB{tty_index}\\"" >> /etc/udev/rules.d/serial.rules\'\n'
    
    content += "\n# Fisheye camera binding rules\n"
    # Generate fisheye camera rules for each device
    for device in devices_info:
        index, serial, usb_path, video_path = device
        if not video_path:  # Skip invalid video paths
            continue
            
        video_index = 80 + index  # Number from video80
        content += f'sudo sh -c \'echo "ACTION==\\"add\\", KERNEL==\\"video*[02468]\\",' \
                  f' KERNELS==\\"{video_path}\\", SUBSYSTEMS==\\"usb\\", MODE:=\\"0777\\", SYMLINK+=\\"video{video_index}\\"" >> /etc/udev/rules.d/fisheye.rules\'\n'
    
    # Apply rules
    content += """
# Reload rules and trigger
sudo udevadm control --reload-rules && sudo service udev restart && sudo udevadm trigger

echo "Device binding rules applied. Please reconnect devices for changes to take effect."
"""

    # Write to file
    with open("setup.bash", "w") as f:
        f.write(content)
    os.chmod("setup.bash", 0o755)
    
    return "setup.bash"

def generate_device_info_file(devices_info):
    """
    Generate device information configuration file for other programs to read.

    Args:
        devices_info: List of device info tuples
            (index, serial_number, usb_path, video_path).

    Returns:
        Path to the generated configuration file.
    """
    content = """# Device information configuration
# Auto-generated at: """ + time.strftime("%Y-%m-%d %H:%M:%S") + """

"""
    
    for device in devices_info:
        index, serial, usb_path, video_path = device
        tty_index = 80 + index  # Number from ttyUSB80
        video_index = 80 + index  # Number from video80
        
        content += f"# Device {index}\n"
        content += f"DEVICE_{index}_SERIAL={serial}\n"
        
        if usb_path:
            content += f"DEVICE_{index}_TTY_PATH=/dev/ttyUSB{tty_index}\n"
        else:
            content += f"DEVICE_{index}_TTY_PATH=未检测到\n"
            
        if video_path:
            content += f"DEVICE_{index}_VIDEO_PATH=/dev/video{video_index}\n"
        else:
            content += f"DEVICE_{index}_VIDEO_PATH=未检测到\n"
            
        content += "\n"
    
    # Write to file
    with open("devices_info.conf", "w") as f:
        f.write(content)
    
    return "devices_info.conf"

def print_colored(text, color="green"):
    """
    Print colored text to improve user experience.

    Args:
        text: Text to print.
        color: Color name; supports green, yellow, red, blue, bold.
    """
    colors = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "bold": "\033[1m",
        "end": "\033[0m"
    }
    
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def main():
    """
    Main function: run device detection and configuration workflow.

    Steps:
    1. Get the number of devices from user input.
    2. Guide the user to connect each device and collect information.
    3. Generate device binding rules and configuration files.
    4. Apply rules and show usage instructions.
    """
    print_colored("====================================", "bold")
    print_colored("  Multi-Device Auto-Detection Tool  ", "bold")
    print_colored("     多设备自动检测与绑定工具 v1.1   ", "bold")
    print_colored("====================================", "bold")
    
    # Check required tools
    missing_tools = []
    if not run_command("which v4l2-ctl"):
        missing_tools.append("v4l-utils")
    if not run_command("which rs-enumerate-devices"):
        missing_tools.append("realsense-sdk")
    
    if missing_tools:
        print_colored("\nWarning: The following tools are missing and may affect detection:", "yellow")
        print_colored("\n警告: 检测到缺少以下工具，可能影响检测结果:", "yellow")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\nRecommended installation:")
        print("\n建议安装:")
        if "v4l-utils" in missing_tools:
            print("  sudo apt install v4l-utils")
        if "realsense-sdk" in missing_tools:
            print("realsense sdk")
        
        print_colored("\nContinue anyway? (y/n)", "yellow")
        print_colored("\n是否继续执行？(y/n)", "yellow")
        choice = input().strip().lower()
        if choice != 'y':
            print_colored("Operation cancelled.", "red")
            print_colored("操作已取消", "red")
            return
    
    # Get the number of devices from user input
    while True:
        try:
            print_colored("\nEnter the number of devices to configure, for example:", "blue")
            print_colored("\n请输入需要配置的设备数量，如：", "blue")
            print_colored("\n* 1 sense or 1 gripper              count: 1 ", "green")
            print_colored("\n* 1 个 sense 或 1 个 gripper    数量为： 1 ", "green")
            print_colored("\n* 2 sense devices                   count: 2 ", "green")
            print_colored("\n* 2 个 sense                   数量为： 2 ", "green")
            print_colored("\n* 2 gripper devices                 count: 2 ", "green")
            print_colored("\n* 2 个 gripper                 数量为： 2 ", "green")
            print_colored("\n* 1 sense and 1 gripper             count: 2 ", "green")
            print_colored("\n* 1 个 sense 和 1 个 gripper    数量为： 2 ", "green")
            print_colored("\n* 2 sense and 1 gripper             count: 3 ", "green")
            print_colored("\n* 2 个 sense 和 1 个 gripper    数量为： 3 ", "green")
            print_colored("\n* 2 sense and 2 gripper             count: 4 ", "green")
            print_colored("\n* 2 个 sense 和 2 个 gripper    数量为： 4 ", "green")
            print_colored("\nEnter the number of devices to configure, then press Enter...", "blue")
            print_colored("\n请输入需要配置的设备数量，然后按回车键继续...", "blue")
            num_devices = int(input().strip())
            if num_devices <= 0:
                print_colored("Device count must be greater than 0. Please try again.", "red")
                print_colored("设备数量必须大于0，请重新输入", "red")
                continue
            break
        except ValueError:
            print_colored("Please enter a valid number.", "red")
            print_colored("请输入有效的数字", "red")
    
    devices_info = []
    
    # Collect information for each device in order
    for i in range(1, num_devices + 1):
        print_colored(f"\n===== Configuring device {i}/{num_devices} =====", "bold")
        print_colored(f"\n===== 配置第 {i}/{num_devices} 个设备 =====", "bold")
        print_colored(f"\nConnect device {i}, then press Enter to continue...", "blue")
        print_colored(f"\n请插入第{i}个设备，然后按回车键继续...", "blue")
        input()
        print_colored(f"Getting information for device {i}...", "green")
        print_colored(f"正在获取第{i}个设备信息...", "green")
        
        # Get device information
        serial_number, usb_path, video_path = get_device_info(i)
        
        if not serial_number and not usb_path and not video_path:
            print_colored(f"Error: Unable to get any information for device {i}.", "red")
            print_colored(f"错误: 无法获取第{i}个设备的任何信息", "red")
            print_colored("Skip this device and continue with the next one? (y/n)", "yellow")
            print_colored("是否跳过此设备并继续配置下一个设备？(y/n)", "yellow")
            choice = input().strip().lower()
            if choice != 'y':
                print_colored("Operation cancelled.", "red")
                print_colored("操作已取消", "red")
                return
            continue
        
        # Save device information
        devices_info.append((i, serial_number, usb_path, video_path))
        
        print_colored(f"\nDevice {i} information collected successfully:", "green")
        print_colored(f"\n第{i}个设备信息获取成功:", "green")
        print(f"  Serial number: {serial_number}")
        print(f"  序列号: {serial_number}")
        print(f"  USB path: {usb_path if usb_path else 'Not detected'}")
        print(f"  USB路径: {usb_path if usb_path else '未检测到'}")
        print(f"  Video path: {video_path if video_path else 'Not detected'}")
        print(f"  视频路径: {video_path if video_path else '未检测到'}")
        
        if i < num_devices:
            print_colored(f"\nDisconnect device {i} and prepare to connect the next device.", "yellow")
            print_colored(f"\n请拔出第{i}个设备，准备插入下一个设备", "yellow")
            print_colored("Note: Do not reuse the same USB port. USB ports must not change after binding.", "yellow")
            print_colored("注意: 请不要插入同一个USB口，配置完成后USB口不能改变", "yellow")
    
    if not devices_info:
        print_colored("\nNo device information collected. Configuration failed.", "red")
        print_colored("\n未获取到任何设备信息，配置失败", "red")
        return
    
    # Generate configuration files
    print_colored("\nGenerating configuration files...", "green")
    print_colored("\n正在生成配置文件...", "green")
    setup_file = generate_setup_bash(devices_info)
    info_file = generate_device_info_file(devices_info)
    
    print_colored("\nConfiguration complete! Generated files:", "green")
    print_colored("\n配置完成！已生成以下文件：", "green")
    print(f"1. {setup_file} - Device binding rules script")
    print(f"1. {setup_file} - 设备绑定规则脚本")
    print(f"2. {info_file} - Device information configuration file")
    print(f"2. {info_file} - 设备信息配置文件")
    
    # Ask whether to apply rules immediately
    print_colored("\nApply device binding rules now? (y/n)", "blue")
    print_colored("\n是否立即应用设备绑定规则？(y/n)", "blue")
    choice = input().strip().lower()
    if choice == 'y':
        print_colored("\nRunning device binding rules script...", "green")
        print_colored("\n执行设备绑定规则脚本...", "green")
        result = run_command(f"bash {setup_file}")
        print(result if result else "Rules applied successfully.")
        print(result if result else "规则应用完成")
        
        print_colored("\nDone!", "green")
        print_colored("\n执行完成！", "green")
        print_colored("Reconnect all devices using the same USB ports used during binding.", "yellow")
        print_colored("请拔插所有设备，注意插入先前绑定的同一个USB口", "yellow")
        print(f"Device binding information saved to {info_file}")
        print(f"设备绑定信息已保存到 {info_file}")
        
        print_colored("\nUsage after device binding:", "bold")
        print_colored("\n设备绑定后的使用方法:", "bold")
        print("1. Each device has fixed ttyUSB and video device paths.")
        print("1. 每个设备都有固定的ttyUSB和video设备路径")
        for device in devices_info:
            index, serial, usb_path, video_path = device
            tty_index = 80 + index
            video_index = 80 + index
            print(f"   Device {index}:")
            print(f"   设备 {index}: ")
            print(f"     * Serial port              /dev/ttyUSB{tty_index}")
            print(f"     *串口端口号                /dev/ttyUSB{tty_index}")
            print(f"     * Fisheye camera index     video{video_index}")
            print(f"     *鱼眼相机索引              video{video_index}")
            print(f"     * RealSense serial number  {serial}")
            print(f"     *双目深度相机序列号        {serial}")
            
        
        print("\n2. Use these fixed paths in your code:")
        print("\n2. 在代码中使用这些固定路径:")
        print("   from pika import sense")
        print("   my_device = sense('/dev/ttyUSB81')  # Use the 1st device")
        print("   my_device = sense('/dev/ttyUSB81')  # 使用第1个设备")
        print("   my_device.set_fisheye_camera_index(81)  # Use fisheye camera of the 1st device")
        print("   my_device.set_fisheye_camera_index(81)  # 使用第1个设备的鱼眼相机")
        print("   my_device.set_realsense_serial_number(230322270988)  # Use RealSense with serial 230322270988")
        print("   my_device.set_realsense_serial_number(230322270988)  # 使用序列号为230322270988的Realsense设备")
    else:
        print_colored(f"\nYou can run bash {setup_file} later to apply device binding rules.", "blue")
        print_colored(f"\n您可以稍后手动执行 bash {setup_file} 应用设备绑定规则", "blue")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nOperation cancelled.", "red")
        print_colored("\n\n操作已取消", "red")
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n\nProgram error: {str(e)}", "red")
        print_colored(f"\n\n程序执行出错: {str(e)}", "red")
        sys.exit(1)
