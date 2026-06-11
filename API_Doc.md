# Pika SDK API Documentation

<p align="center">
  <a> English </a> | <a href="API_Doc_ch-CN.md">中文</a>
</p>

## Table of Contents

1. [Module Overview](#module-overview)
2. [Sense Class](#sense-class)
3. [Ego Class](#ego-class)
4. [Gripper Class](#gripper-class)
5. [FisheyeCamera Class](#fisheyecamera-class)
6. [RealSenseCamera Class](#realsensecamera-class)
7. [SerialComm Class](#serialcomm-class)
8. [ViveTracker Class](#vivetracker-class)
9. [Error Handling](#error-handling)
10. [FAQ](#faq)

## Module Overview

Pika SDK consists of the following main modules:

### pika.sense

The `pika.sense` module provides access to Pika Sense devices, supporting encoder data reading and camera access. The core of this module is the `Sense` class, used for communicating with Pika Sense devices.

### pika.ego

The `pika.ego` module provides access to Pika Ego devices, supporting IMU data reading and camera access. The core of this module is the `Ego` class, used for communicating with Pika Ego devices.

### pika.gripper

The `pika.gripper` module provides access to Pika Gripper devices, supporting motor control and status monitoring. The core of this module is the `Gripper` class, used for communicating with and controlling Pika Gripper devices.

### pika.camera

The `pika.camera` module contains two submodules: `fisheye` and `realsense`, which provide access to fisheye cameras and RealSense depth cameras respectively.

### pika.serial_comm

The `pika.serial_comm` module provides low-level serial communication functionality for data exchange with Pika devices. This module is typically not used directly; it is called internally by the `Sense` and `Gripper` classes.

### pika.tracker

The `pika.tracker` module provides access to pose tracking devices, currently supporting Vive Tracker devices. The core of this module is the `ViveTracker` class, used for obtaining device pose data.

## Sense Class

The `Sense` class is the main interface for Pika Sense devices, providing access to device sensors and cameras.

### Import

```python
from pika import sense
```

### Initialization

```python
my_sense = sense(port='/dev/ttyUSB0')
```

#### Parameters

- `port` (str): Serial device path, default is '/dev/ttyUSB0'

### Methods

#### connect()

Connect to the Pika Sense device.

```python
success = my_sense.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:

```python
my_sense = sense('/dev/ttyUSB0')
if my_sense.connect():
    print("Device connected successfully")
else:
    print("Device connection failed")
```

#### disconnect()

Disconnect from the Pika Sense device and release resources.

```python
my_sense.disconnect()
```

**Returns**:
- None

**Example**:
```python
my_sense.disconnect()
print("Device disconnected")
```

#### get_encoder_data()

Get encoder data.

```python
encoder_data = my_sense.get_encoder_data()
```

**Returns**:
- `dict`: A dictionary containing the following fields:
  - `angle` (float): Angle value
  - `rad` (float): Radian value

**Example**:
```python
encoder_data = my_sense.get_encoder_data()
print(f"Angle: {encoder_data['angle']}")
print(f"Radians: {encoder_data['rad']}")
```

#### get_command_state()

Get command state.

```python
state = my_sense.get_command_state()
```

**Returns**:
- `int`: Command state code

**Example**:
```python
state = my_sense.get_command_state()
print(f"Command state: {state}")
```

#### get_gripper_distance()

Get gripper opening distance.

```python
distance = my_sense.get_gripper_distance()
print(f"Gripper opening distance: {distance}")
```

**Returns**:
- `float`: Gripper opening distance (mm)

**Example**:
```python
distance = my_sense.get_gripper_distance()
print(f"Gripper opening distance: {distance}")
```


#### set_camera_param(camera_width, camera_height, camera_fps)

Set camera resolution and frame rate.

```python
my_sense.set_camera_param(camera_width, camera_height, camera_fps)
```

**Parameters**:

- `camera_width` (int): Camera width, default is 640
- `camera_height` (int): Camera height, default is 480
- `camera_fps` (int): Camera frame rate, default is 30

**Returns**:

- None

**Example**:
```python
# Set camera parameters to 640x480 at 30fps
my_sense.set_camera_param(640, 480, 30)
```

The following resolutions and frame rates are available:

| Resolution | Frame Rate |
| :--------: | :--------: |
| 1280x720   |     30     |
| 640x480    | 30/60/90   |

#### set_fisheye_camera_index(index)

Set the fisheye camera index.

```python
my_sense.set_fisheye_camera_index(index)
```

**Parameters**:
- `index` (int): Fisheye camera index

**Returns**:
- None

**Example**:
```python
# Set fisheye camera index to 1
my_sense.set_fisheye_camera_index(1)
```

#### set_realsense_serial_number(serial_number)

Set the RealSense camera serial number.

```python
my_sense.set_realsense_serial_number(serial_number)
```

**Parameters**:
- `serial_number` (str): RealSense camera serial number

**Returns**:
- None

**Example**:
```python
# Set RealSense camera serial number
my_sense.set_realsense_serial_number("12345678")
```

#### get_fisheye_camera()

Get the fisheye camera object.

```python
fisheye_camera = my_sense.get_fisheye_camera()
```

**Returns**:

- `FisheyeCamera`: Fisheye camera object; returns None if initialization fails

**Example**:

```python
fisheye_camera = my_sense.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # Process image
        pass
```

#### get_realsense_camera()

Get the RealSense camera object.

```python
realsense_camera = my_sense.get_realsense_camera()
```

**Returns**:
- `RealSenseCamera`: RealSense camera object; returns None if initialization fails

**Example**:
```python
realsense_camera = my_sense.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # Process color image
        pass
```

#### set_vive_tracker_config(config_path, lh_config, args)

Set Vive Tracker configuration parameters.

```python
my_sense.set_vive_tracker_config(config_path, lh_config, args)
```

**Parameters**:
- `config_path` (str, optional): Configuration file path
- `lh_config` (str, optional): Lighthouse configuration
- `args` (list, optional): Additional pysurvive parameters

**Returns**:
- None

**Example**:
```python
# Set Vive Tracker configuration
my_sense.set_vive_tracker_config(config_path="/path/to/config", lh_config="lighthouse_config")
```

#### get_vive_tracker()

Get the Vive Tracker object.

```python
vive_tracker = my_sense.get_vive_tracker()
```

**Returns**:
- `ViveTracker`: Vive Tracker object; returns None if initialization fails

**Example**:
```python
vive_tracker = my_sense.get_vive_tracker()
if vive_tracker:
    # Get device list
    devices = vive_tracker.get_devices()
    print(f"Detected devices: {devices}")
```

#### get_pose(device_name)

Get pose data for the specified device.

```python
pose = my_sense.get_pose(device_name)
```

**Parameters**:
- `device_name` (str, optional): Device name; if None, returns pose data for all devices

**Returns**:
- `PoseData` or `dict`: If device_name is specified, returns the PoseData object for that device; otherwise returns a dictionary of all device poses {device_name: PoseData}

**Example**:
```python
# Get pose for a specific device
pose = my_sense.get_pose("WM0")
if pose:
    print(f"Position: {pose.position}")
    print(f"Rotation: {pose.rotation}")

# Get poses for all devices
all_poses = my_sense.get_pose()
for device_name, pose in all_poses.items():
    print(f"Device {device_name} - Position: {pose.position}, Rotation: {pose.rotation}")
```

#### get_tracker_devices()

Get a list of all detected Vive Tracker devices.

```python
devices = my_sense.get_tracker_devices()
```

**Returns**:
- `list`: List of device names

**Example**:
```python
devices = my_sense.get_tracker_devices()
print(f"Detected devices: {devices}")
```

#### light_ctrl(light_id)

Control the lights on the Pika Sense device.

```python
my_sense.light_ctrl(light_id)
```

**Parameters**:
- `light_id` (int): Light ID; 0-4 correspond to white, red, green, blue, and yellow lights respectively

**Returns**:
- None

**Example**:
```python
# Turn on white light
my_sense.light_ctrl(0)
```

#### vibrate_ctrl(mode)

Control the vibration motor on the Pika Sense device.

```python
my_sense.vibrate_ctrl(mode)
```

**Parameters**:
- `mode` (int): Vibration mode; 0 is off, 1 is on

**Returns**:
- None

**Example**:
```python
# Turn on vibration motor
my_sense.vibrate_ctrl(1)
```

#### get_version()

Get the firmware version of the Pika Sense device.

```python
my_sense.get_version()
```

**Returns**:
- None

**Example**:
```python
my_sense.get_version()
```


## Ego Class

The `Ego` class is the main interface for Pika Ego devices, providing access to IMU sensors and cameras.

### Import

```python
from pika import ego
```

### Initialization

```python
my_ego = ego(port='/dev/ttyUSB0')
```

#### Parameters

- `port` (str): Serial device path

### Methods

#### connect()

Connect to the Pika Ego device.

```python
success = my_ego.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:

```python
my_ego = ego('/dev/ttyUSB0')
if my_ego.connect():
    print("Device connected successfully")
else:
    print("Device connection failed")
```

#### disconnect()

Disconnect from the Pika Ego device and release resources.

```python
my_ego.disconnect()
```

**Returns**:
- None

**Example**:
```python
my_ego.disconnect()
print("Device disconnected")
```

#### get_imu_data()

Get complete raw IMU data.

```python
imu_data = my_ego.get_imu_data()
```

**Returns**:
- `dict`: A dictionary containing the following fields:
  - `acc` (list): Accelerometer data [x, y, z], in m/s^2
  - `gyr` (list): Gyroscope data [x, y, z], in rad/s
  - `mag` (list): Magnetometer data [x, y, z], in uT
  - `quat` (list): Quaternion [w, x, y, z]

**Example**:
```python
imu_data = my_ego.get_imu_data()
print(f"Acceleration: {imu_data['acc']}")
print(f"Angular velocity: {imu_data['gyr']}")
print(f"Magnetometer: {imu_data['mag']}")
print(f"Quaternion: {imu_data['quat']}")
```

#### get_accelerometer()

Get accelerometer data.

```python
acc = my_ego.get_accelerometer()
```

**Returns**:
- `list`: [x, y, z] acceleration data, in m/s^2

**Example**:
```python
acc = my_ego.get_accelerometer()
print(f"Acceleration: x={acc[0]:.3f}, y={acc[1]:.3f}, z={acc[2]:.3f} m/s^2")
```

#### get_gyroscope()

Get gyroscope data.

```python
gyr = my_ego.get_gyroscope()
```

**Returns**:
- `list`: [x, y, z] angular velocity data, in rad/s

**Example**:
```python
gyr = my_ego.get_gyroscope()
print(f"Angular velocity: x={gyr[0]:.3f}, y={gyr[1]:.3f}, z={gyr[2]:.3f} rad/s")
```

#### get_magnetometer()

Get magnetometer data.

```python
mag = my_ego.get_magnetometer()
```

**Returns**:
- `list`: [x, y, z] magnetometer data, in uT

**Example**:
```python
mag = my_ego.get_magnetometer()
print(f"Magnetometer: x={mag[0]:.1f}, y={mag[1]:.1f}, z={mag[2]:.1f} uT")
```

#### get_quaternion()

Get quaternion orientation data.

```python
quat = my_ego.get_quaternion()
```

**Returns**:
- `list`: [w, x, y, z] quaternion

**Example**:
```python
quat = my_ego.get_quaternion()
w, x, y, z = quat
print(f"Quaternion: w={w:.3f}, x={x:.3f}, y={y:.3f}, z={z:.3f}")
```

#### set_camera_param(camera_width, camera_height, camera_fps, fisheye_thread_fps=100)

Set camera resolution and frame rate.

```python
my_ego.set_camera_param(camera_width, camera_height, camera_fps, fisheye_thread_fps=100)
```

**Parameters**:

- `camera_width` (int): Camera width, default is 1280
- `camera_height` (int): Camera height, default is 720
- `camera_fps` (int): Camera frame rate, default is 30
- `fisheye_thread_fps` (int): Fisheye camera read thread frame rate, default is 100

**Returns**:
- None

**Example**:
```python
# Set camera parameters to 1280x720 at 30fps, fisheye thread rate 100Hz
my_ego.set_camera_param(1280, 720, 30, 100)
```

The following resolutions and frame rates are available:

| Resolution | Frame Rate |
| :--------: | :--------: |
| 1280x720   |     30     |
| 640x480    | 30/60/90   |

#### set_fisheye_camera_index(index)

Set the fisheye camera index.

```python
my_ego.set_fisheye_camera_index(index)
```

**Parameters**:
- `index` (int): Fisheye camera index

**Returns**:
- None

**Example**:
```python
# Set fisheye camera index to 81
my_ego.set_fisheye_camera_index(81)
```

#### set_realsense_serial_number(serial_number)

Set the RealSense camera serial number.

```python
my_ego.set_realsense_serial_number(serial_number)
```

**Parameters**:
- `serial_number` (str): RealSense camera serial number

**Returns**:
- None

**Example**:
```python
# Set RealSense camera serial number
my_ego.set_realsense_serial_number("260422273747")
```

#### get_fisheye_camera()

Get the fisheye camera object.

```python
fisheye_camera = my_ego.get_fisheye_camera()
```

**Returns**:
- `FisheyeCamera`: Fisheye camera object; returns None if initialization fails

**Example**:
```python
fisheye_camera = my_ego.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # Process image
        pass
```

#### get_realsense_camera()

Get the RealSense camera object.

```python
realsense_camera = my_ego.get_realsense_camera()
```

**Returns**:
- `RealSenseCamera`: RealSense camera object; returns None if initialization fails

**Example**:
```python
realsense_camera = my_ego.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # Process color image
        pass
```

#### get_version()

Get the firmware version of the Pika Ego device.

```python
my_ego.get_version()
```

**Returns**:
- `tuple`: Tuple containing version information

**Example**:
```python
version_info = my_ego.get_version()
print(f"Device version: {version_info}")
```

## Gripper Class

The `Gripper` class is the main interface for Pika Gripper devices, providing access to motor control and status monitoring.

### Import

```python
from pika import gripper
```

### Initialization

```python
my_gripper = gripper(port='/dev/ttyUSB0')
```

#### Parameters

- `port` (str): Serial device path, default is '/dev/ttyUSB0'

### Methods

#### connect()

Connect to the Pika Gripper device.

```python
success = my_gripper.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:
```python
my_gripper = gripper('/dev/ttyUSB0')
if my_gripper.connect():
    print("Device connected successfully")
else:
    print("Device connection failed")
```

#### disconnect()

Disconnect from the Pika Gripper device and release resources.

```python
my_gripper.disconnect()
```

**Returns**:
- None

**Example**:
```python
my_gripper.disconnect()
print("Device disconnected")
```

#### enable()

Enable the motor.

```python
success = my_gripper.enable()
```

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
if my_gripper.enable():
    print("Motor enabled")
else:
    print("Failed to enable motor")
```

#### disable()

Disable the motor.

```python
success = my_gripper.disable()
```

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
if my_gripper.disable():
    print("Motor disabled")
else:
    print("Failed to disable motor")
```

#### set_zero()

Set the current position as zero.

```python
success = my_gripper.set_zero()
```

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
if my_gripper.set_zero():
    print("Zero position set")
else:
    print("Failed to set zero position")
```

#### set_motor_angle(position)

Set motor position (radians).

```python
success = my_gripper.set_motor_angle(position)
```

**Parameters**:
- `position` (float): Target position, in radians

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
# Set motor position to 0.5 radians
if my_gripper.set_motor_angle(0.5):
    print("Position set")
else:
    print("Failed to set position")
```

#### set_motor_torque(current)

Set motor current to adjust motor torque.

```python
success = my_gripper.set_motor_torque(current)
```

**Parameters**:
- `current` (float): Target current, in A. Typical range is 0~8A; exceeding this range may trigger motor overcurrent protection.

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
# Set motor current to 0.8 A
if my_gripper.set_motor_torque(0.8):
    print("Current set")
else:
    print("Failed to set current")
```


#### set_gripper_distance(target_gripper_distance_mm)

Set gripper opening distance (mm).

```python
success = my_gripper.set_gripper_distance(target_gripper_distance_mm)
```

**Parameters**:
- `target_gripper_distance_mm` (float): Target gripper opening distance (mm). Typical range is 0-90mm; exceeding this range may cause the operation to fail.

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
# Set gripper opening distance to 50mm
if my_gripper.set_gripper_distance(50.0):
    print("Gripper distance set")
else:
    print("Failed to set gripper distance")
```

#### set_velocity(velocity)

Set motor velocity.

```python
success = my_gripper.set_velocity(velocity)
```

**Parameters**:
- `velocity` (float): Target velocity

**Returns**:

- `bool`: Whether the operation succeeded

**Example**:
```python
# Set motor velocity to 10.0
if my_gripper.set_velocity(10.0):
    print("Velocity set")
else:
    print("Failed to set velocity")
```

#### set_effort(effort)

Set motor effort (torque).

```python
success = my_gripper.set_effort(effort)
```

**Parameters**:

- `effort` (float): Target effort

**Returns**:
- `bool`: Whether the operation succeeded

**Example**:
```python
# Set motor effort to 5.0
if my_gripper.set_effort(5.0):
    print("Effort set")
else:
    print("Failed to set effort")
```

#### get_gripper_distance()

Get the current gripper opening distance (mm).

```python
distance = my_gripper.get_gripper_distance()
```

**Returns**:
- `float`: Current gripper opening distance (mm)

**Example**:
```python
distance = my_gripper.get_gripper_distance()
print(f"Current gripper opening distance: {distance} mm")
```

#### get_motor_data()

Get complete motor data.

```python
motor_data = my_gripper.get_motor_data()
```

**Returns**:
- `dict`: A dictionary containing the following fields:
  - `Speed` (float): Current motor speed (rad/s)
  - `Current` (int): Current motor phase current (mA)
  - `Position` (float): Current motor position (rad)

**Example**:
```python
motor_data = my_gripper.get_motor_data()
print(f"Speed: {motor_data['Speed']} rad/s")
print(f"Current: {motor_data['Current']} mA")
print(f"Position: {motor_data['Position']} rad")
```

#### get_motor_status()

Get motor status.

```python
motor_status = my_gripper.get_motor_status()
```

**Returns**:
- `dict`: A dictionary containing the following fields:
  - `Voltage` (float): Motor driver voltage (V)
  - `DriverTemp` (int): Motor driver temperature (°C)
  - `MotorTemp` (int): Motor temperature (°C)
  - `Status` (str): Motor driver status (hexadecimal string)
  - `BusCurrent` (int): Bus current (mA)

**Example**:
```python
motor_status = my_gripper.get_motor_status()
print(f"Voltage: {motor_status['Voltage']} V")
print(f"Driver temperature: {motor_status['DriverTemp']} °C")
print(f"Motor temperature: {motor_status['MotorTemp']} °C")
print(f"Status code: {motor_status['Status']}")
print(f"Bus current: {motor_status['BusCurrent']} mA")
```

#### get_motor_speed()

Get the current motor speed.

```python
speed = my_gripper.get_motor_speed()
```

**Returns**:
- `float`: Current motor speed (rad/s)

**Example**:

```python
speed = my_gripper.get_motor_speed()
print(f"Motor speed: {speed} rad/s")
```

#### get_motor_current()

Get the current motor phase current.

```python
current = my_gripper.get_motor_current()
```

**Returns**:

- `int`: Current motor phase current (mA)

**Example**:
```python
current = my_gripper.get_motor_current()
print(f"Motor current: {current} mA")
```

#### get_motor_position()

Get the current motor position.

```python
position = my_gripper.get_motor_position()
```

**Returns**:
- `float`: Current motor position (rad)

**Example**:
```python
position = my_gripper.get_motor_position()
print(f"Motor position: {position} rad")
```

#### get_voltage()

Get the motor driver voltage.

```python
voltage = my_gripper.get_voltage()
```

**Returns**:
- `float`: Motor driver voltage (V)

**Example**:
```python
voltage = my_gripper.get_voltage()
print(f"Driver voltage: {voltage} V")
```

#### get_driver_temp()

Get the motor driver temperature.

```python
temp = my_gripper.get_driver_temp()
```

**Returns**:
- `int`: Motor driver temperature (°C)

**Example**:
```python
temp = my_gripper.get_driver_temp()
print(f"Driver temperature: {temp} °C")
```

#### get_motor_temp()

Get the motor temperature.

```python
temp = my_gripper.get_motor_temp()
```

**Returns**:
- `int`: Motor temperature (°C)

**Example**:
```python
temp = my_gripper.get_motor_temp()
print(f"Motor temperature: {temp} °C")
```

#### get_status_raw()

Get the motor driver status (raw string).

```python
status = my_gripper.get_status_raw()
```

**Returns**:

- `str`: Motor driver status (hexadecimal string)

**Example**:

```python
status = my_gripper.get_status_raw()
print(f"Driver status: {status}")
```

Status code table:

| Hex Code |          Description           |
| :------: | :----------------------------: |
|   0x00   | All normal, driver disabled    |
|   0x01   |         Low voltage            |
|   0x02   |       Motor over-temperature   |
|   0x04   |    Driver motor overcurrent    |
|   0x08   |      Driver over-temperature   |
|   0x10   |    Sensor status abnormal      |
|   0x20   |      Driver error state        |
|   0x40   |      Driver enabled state      |
|   0x80   | Homed or has been homed before |

#### get_bus_current()

Get bus current.

```python
current = my_gripper.get_bus_current()
```

**Returns**:
- `int`: Bus current (mA)

**Example**:
```python
current = my_gripper.get_bus_current()
print(f"Bus current: {current} mA")
```

#### set_camera_param(camera_width, camera_height, camera_fps)

Set camera resolution and frame rate.

```python
my_gripper.set_camera_param(camera_width, camera_height, camera_fps)
```

**Parameters**:
- `camera_width` (int): Camera width, default is 640
- `camera_height` (int): Camera height, default is 480
- `camera_fps` (int): Camera frame rate, default is 30

**Returns**:
- None

**Example**:

```python
# Set camera parameters to 640x480 at 30fps
my_gripper.set_camera_param(640, 480, 30)
```

The following resolutions and frame rates are available:

| Resolution | Frame Rate |
| :--------: | :--------: |
| 1280x720   |     30     |
| 640x480    | 30/60/90   |

#### set_fisheye_camera_index(index)

Set the fisheye camera index.

```python
my_gripper.set_fisheye_camera_index(index)
```

**Parameters**:
- `index` (int): Fisheye camera index

**Returns**:
- None

**Example**:
```python
# Set fisheye camera index to 1
my_gripper.set_fisheye_camera_index(1)
```

#### set_realsense_serial_number(serial_number)

Set the RealSense camera serial number.

```python
my_gripper.set_realsense_serial_number(serial_number)
```

**Parameters**:
- `serial_number` (str): RealSense camera serial number

**Returns**:
- None

**Example**:
```python
# Set RealSense camera serial number
my_gripper.set_realsense_serial_number("12345678")
```

#### get_fisheye_camera()

Get the fisheye camera object.

```python
fisheye_camera = my_gripper.get_fisheye_camera()
```

**Returns**:
- `FisheyeCamera`: Fisheye camera object; returns None if initialization fails

**Example**:
```python
fisheye_camera = my_gripper.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # Process image
        pass
```

#### get_realsense_camera()

Get the RealSense camera object.

```python
realsense_camera = my_gripper.get_realsense_camera()
```

**Returns**:
- `RealSenseCamera`: RealSense camera object; returns None if initialization fails

**Example**:
```python
realsense_camera = my_gripper.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # Process color image
        pass
```

#### get_version()

Get the firmware version of the Pika Gripper device.

```python
my_sense.get_version()
```

**Returns**:
- None

**Example**:
```python
my_sense.get_version()
```


## FisheyeCamera Class

The `FisheyeCamera` class provides access to the fisheye camera on Pika devices.

### Import

Direct import is typically not required; obtain the object via the `get_fisheye_camera()` method on the `Sense` or `Gripper` class.

```python
# If direct import is needed
from pika.camera.fisheye import FisheyeCamera
```

### Initialization

```python
camera = FisheyeCamera(camera_width=640, camera_height=480, camera_fps=30, device_id=0)
```

#### Parameters

- `camera_width` (int): Camera width, default is 640
- `camera_height` (int): Camera height, default is 480
- `camera_fps` (int): Camera frame rate, default is 30
- `device_id` (int): Camera device ID, default is 0

### Methods

#### connect()

Connect to the fisheye camera.

```python
success = camera.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:
```python
camera = FisheyeCamera()
if camera.connect():
    print("Camera connected successfully")
else:
    print("Camera connection failed")
```

#### disconnect()

Disconnect from the fisheye camera and release resources.

```python
camera.disconnect()
```

**Returns**:
- None

**Example**:
```python
camera.disconnect()
print("Camera disconnected")
```

#### get_frame()

Get a single frame.

```python
success, frame = camera.get_frame()
```

**Returns**:
- `tuple`: (success flag, image data)
  - `success` (bool): Whether retrieval succeeded
  - `frame` (numpy.ndarray): Image data; None if retrieval failed

**Example**:
```python
success, frame = camera.get_frame()
if success:
    import cv2
    cv2.imshow('Fisheye Camera', frame)
    cv2.waitKey(1)
```

#### get_camera_info()

Get camera information.

```python
info = camera.get_camera_info()
```

**Returns**:
- `dict`: A dictionary containing the following fields:
  - `width` (int): Image width
  - `height` (int): Image height
  - `fps` (float): Frame rate
  - `device_id` (int): Device ID

**Example**:
```python
info = camera.get_camera_info()
print(f"Resolution: {info['width']}x{info['height']}")
print(f"Frame rate: {info['fps']}")
print(f"Device ID: {info['device_id']}")
```

## RealSenseCamera Class

The `RealSenseCamera` class provides access to the RealSense D405 depth camera on Pika devices.

### Import

Direct import is typically not required; obtain the object via the `get_realsense_camera()` method on the `Sense` or `Gripper` class.

```python
# If direct import is needed
from pika.camera.realsense import RealSenseCamera
```

### Initialization

```python
camera = RealSenseCamera(camera_width=640, camera_height=480, camera_fps=30, serial_number=None)
```

#### Parameters

- `camera_width` (int): Camera width, default is 640
- `camera_height` (int): Camera height, default is 480
- `camera_fps` (int): Camera frame rate, default is 30
- `serial_number` (str): Camera serial number, default is None

### Methods

#### connect()

Connect to the RealSense camera.

```python
success = camera.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:
```python
camera = RealSenseCamera()
if camera.connect():
    print("Camera connected successfully")
else:
    print("Camera connection failed")
```

#### disconnect()

Disconnect from the RealSense camera and release resources.

```python
camera.disconnect()
```

**Returns**:
- None

**Example**:
```python
camera.disconnect()
print("Camera disconnected")
```

#### get_frames()

Get a set of frames (color and depth).

```python
success, color_image, depth_image = camera.get_frames()
```

**Returns**:
- `tuple`: (success flag, color image, depth image)
  - `success` (bool): Whether retrieval succeeded
  - `color_image` (numpy.ndarray): Color image data; None if retrieval failed
  - `depth_image` (numpy.ndarray): Depth image data; None if retrieval failed

**Example**:
```python
success, color_image, depth_image = camera.get_frames()
if success:
    import cv2
    cv2.imshow('Color Image', color_image)
    
    # Normalize depth image for display
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
    cv2.imshow('Depth Image', depth_colormap)
    
    cv2.waitKey(1)
```

#### get_color_frame()

Get the color image.

```python
success, color_image = camera.get_color_frame()
```

**Returns**:
- `tuple`: (success flag, color image)
  - `success` (bool): Whether retrieval succeeded
  - `color_image` (numpy.ndarray): Color image data; None if retrieval failed

**Example**:
```python
success, color_image = camera.get_color_frame()
if success:
    import cv2
    cv2.imshow('Color Image', color_image)
    cv2.waitKey(1)
```

#### get_depth_frame()

Get the depth image.

```python
success, depth_image = camera.get_depth_frame()
```

**Returns**:
- `tuple`: (success flag, depth image)
  - `success` (bool): Whether retrieval succeeded
  - `depth_image` (numpy.ndarray): Depth image data; None if retrieval failed

**Example**:
```python
success, depth_image = camera.get_depth_frame()
if success:
    import cv2
    import numpy as np
    
    # Normalize depth image for display
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
    cv2.imshow('Depth Image', depth_colormap)
    cv2.waitKey(1)
```

#### get_camera_info()	

Get camera information.

```python
info = camera.get_camera_info()
```

**Returns**:
- `dict`: A dictionary containing camera intrinsics and serial number:
  - `color_width` (int): Color image width
  - `color_height` (int): Color image height
  - `color_fx` (float): Color camera focal length in x direction
  - `color_fy` (float): Color camera focal length in y direction
  - `color_ppx` (float): Color camera principal point in x direction
  - `color_ppy` (float): Color camera principal point in y direction
  - `depth_width` (int): Depth image width
  - `depth_height` (int): Depth image height
  - `depth_fx` (float): Depth camera focal length in x direction
  - `depth_fy` (float): Depth camera focal length in y direction
  - `depth_ppx` (float): Depth camera principal point in x direction
  - `depth_ppy` (float): Depth camera principal point in y direction
  - `serial_number` (str): Camera serial number

**Example**:
```python
info = camera.get_camera_info()
print(f"Color resolution: {info['color_width']}x{info['color_height']}")
print(f"Depth resolution: {info['depth_width']}x{info['depth_height']}")
print(f"Color camera focal length: ({info['color_fx']}, {info['color_fy']})")
print(f"Depth camera focal length: ({info['depth_fx']}, {info['depth_fy']})")
print(f"Serial number: {info['serial_number']}")
```

## SerialComm Class

The `SerialComm` class provides low-level serial communication functionality for data exchange with Pika devices. It is typically not used directly; it is called internally by the `Sense` and `Gripper` classes.

### Import

```python
from pika.serial_comm import SerialComm
```

### Initialization

```python
serial_comm = SerialComm(port='/dev/ttyUSB0', baudrate=460800, timeout=1.0)
```

#### Parameters

- `port` (str): Serial device path, default is '/dev/ttyUSB0'
- `baudrate` (int): Baud rate, default is 460800
- `timeout` (float): Timeout in seconds, default is 1.0

### Methods

#### connect()

Connect to the serial device.

```python
success = serial_comm.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:
```python
serial_comm = SerialComm('/dev/ttyUSB0')
if serial_comm.connect():
    print("Serial port connected successfully")
else:
    print("Serial port connection failed")
```

#### disconnect()

Disconnect from the serial device.

```python
serial_comm.disconnect()
```

**Returns**:
- None

**Example**:
```python
serial_comm.disconnect()
print("Serial port disconnected")
```

#### send_data(data)

Send data to the serial port.

```python
success = serial_comm.send_data(data)
```

**Parameters**:
- `data` (bytes): Data to send

**Returns**:
- `bool`: Whether sending succeeded

**Example**:
```python
data = b'Hello, Pika!\r\n'
if serial_comm.send_data(data):
    print("Data sent successfully")
else:
    print("Failed to send data")
```

#### send_command(command_type, value)

Send a command to the device.

```python
success = serial_comm.send_command(command_type, value)
```

**Parameters**:
- `command_type` (int): Command type
- `value` (float): Command value, default is 0.0

**Returns**:
- `bool`: Whether sending succeeded

**Example**:
```python
# Send command type 1 with value 0.5
if serial_comm.send_command(1, 0.5):
    print("Command sent successfully")
else:
    print("Failed to send command")
```

#### read_data()

Read data from the serial port.

```python
data = serial_comm.read_data()
```

**Returns**:
- `bytes`: Data read

**Example**:
```python
data = serial_comm.read_data()
if data:
    print(f"Data read: {data}")
```

#### start_reading_thread(callback)

Start the data reading thread.

```python
serial_comm.start_reading_thread(callback=my_callback_function)
```

**Parameters**:
- `callback` (function): Data callback function that receives parsed JSON data

**Returns**:
- None

**Example**:
```python
def my_callback(json_data):
    print(f"Received data: {json_data}")

serial_comm.start_reading_thread(callback=my_callback)
```

#### stop_reading_thread()

Stop the data reading thread.

```python
serial_comm.stop_reading_thread()
```

**Returns**:
- None

**Example**:
```python
serial_comm.stop_reading_thread()
print("Reading thread stopped")
```

#### get_latest_data()

Get the latest data.

```python
data = serial_comm.get_latest_data()
```

**Returns**:
- `dict`: Latest data

**Example**:
```python
data = serial_comm.get_latest_data()
print(f"Latest data: {data}")
```

## ViveTracker Class

The `ViveTracker` class provides access to Vive Tracker device pose data.

### Import

Direct import is typically not required; obtain the object via the `get_vive_tracker()` method on the `Sense` class.

```python
# If direct import is needed
from pika.tracker.vive_tracker import ViveTracker
```

### Initialization

```python
tracker = ViveTracker(config_path=None, lh_config=None, args=None)
```

#### Parameters

- `config_path` (str, optional): Configuration file path
- `lh_config` (str, optional): Lighthouse configuration
- `args` (list, optional): Additional pysurvive parameters

### Methods

#### connect()

Initialize and connect to Vive Tracker devices.

```python
success = tracker.connect()
```

**Returns**:
- `bool`: Whether the connection succeeded

**Example**:
```python
tracker = ViveTracker()
if tracker.connect():
    print("Vive Tracker connected successfully")
else:
    print("Vive Tracker connection failed")
```

#### disconnect()

Disconnect from Vive Tracker devices.

```python
tracker.disconnect()
```

**Returns**:
- None

**Example**:
```python
tracker.disconnect()
print("Vive Tracker disconnected")
```

#### get_pose(device_name)

Get the latest pose data for the specified device.

```python
pose = tracker.get_pose(device_name)
```

**Parameters**:
- `device_name` (str, optional): Device name; if None, returns pose data for all devices

**Returns**:
- `PoseData` or `dict`: If device_name is specified, returns the PoseData object for that device; otherwise returns a dictionary of all device poses {device_name: PoseData}

**Example**:
```python
# Get pose for a specific device
pose = tracker.get_pose("WM0")
if pose:
    print(f"Position: {pose.position}")
    print(f"Rotation: {pose.rotation}")

# Get poses for all devices
all_poses = tracker.get_pose()
for device_name, pose in all_poses.items():
    print(f"Device {device_name} - Position: {pose.position}, Rotation: {pose.rotation}")
```

The coordinate diagram for tracker pose data is shown below:

![img](img/mmexport1746516732555.png)

The coordinate system is located at the gripper center.

#### get_devices()

Get a list of all detected devices.

```python
devices = tracker.get_devices()
```

**Returns**:
- `list`: List of device names

**Example**:
```python
devices = tracker.get_devices()
print(f"Detected devices: {devices}")
```

#### get_device_info(device_name)

Get device information.

```python
info = tracker.get_device_info(device_name)
```

**Parameters**:
- `device_name` (str, optional): Device name; if None, returns information for all devices

**Returns**:
- `dict`: Device information dictionary

**Example**:
```python
# Get information for a specific device
info = tracker.get_device_info("WM0")
if info:
    print(f"Update count: {info['updates']}")
    print(f"Last update time: {info['last_update']}")

# Get information for all devices
all_info = tracker.get_device_info()
for device_name, info in all_info.items():
    print(f"Device {device_name} - Update count: {info['updates']}, Last update time: {info['last_update']}")
```

### PoseData Class

The `PoseData` class is used to store and format pose information.

#### Properties

- `device_name` (str): Device name
- `timestamp` (float): Timestamp
- `position` (list): Position [x, y, z]
- `rotation` (list): Rotation quaternion [x, y, z, w]

#### Example

```python
# Get PoseData object via ViveTracker
pose = tracker.get_pose("WM0")
if pose:
    print(f"Device name: {pose.device_name}")
    print(f"Timestamp: {pose.timestamp}")
    print(f"Position: {pose.position}")  # [x, y, z]
    print(f"Rotation: {pose.rotation}")  # [x, y, z, w] quaternion
    
    # Extract position and rotation data for further processing
    position = pose.position  # [x, y, z]
    rotation = pose.rotation  # [x, y, z, w] quaternion
    
    # Compute sum of squared position components (for distance calculation)
    distance_squared = sum([p*p for p in position])
    print(f"Distance squared from origin: {distance_squared:.6f}")
    
    # Extract individual quaternion components
    x, y, z, w = rotation
    print(f"Quaternion components: x={x:.6f}, y={y:.6f}, z={z:.6f}, w={w:.6f}")
```

## Error Handling

Pika SDK uses Python's logging system to record errors and warnings, making it easier for developers to debug and troubleshoot. By default, the log level is set to INFO, recording basic operation information and errors. If you need more detailed log information, you can set the log level to DEBUG:

```python
import logging
logging.getLogger('pika').setLevel(logging.DEBUG)  # Set to DEBUG level for more detailed logs
```

Most methods in the SDK return specific error codes or False values when errors occur, and log detailed error information. It is recommended to pay close attention to log output during development to identify and resolve issues promptly.

For common error situations such as device not connected or camera initialization failure, the SDK provides clear error messages and performs graceful error handling whenever possible to avoid program crashes.

## FAQ

### 1. How do I determine the serial device path?

On Linux systems, you can use the following command to list all serial devices:

```bash
ls /dev/ttyUSB*
```

If there are multiple devices, try disconnecting and reconnecting the Pika device and observe which device path appears or disappears to determine the correct path.

### 2. Why can't I connect to the RealSense camera?

First, make sure the pyrealsense2 library is installed:

```bash
pip install pyrealsense2
```

If you still cannot connect, possible causes include:

- RealSense camera is not properly connected to the USB port
- The USB port does not have sufficient bandwidth; try using a USB 3.0 or higher port
- Camera serial number is set incorrectly; try not specifying a serial number or using the correct serial number

### 3. How do I resolve serial port access permission issues?

If you encounter serial port access permission issues, you can add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

You need to log out and log back in for the permissions to take effect.

### 4. How do I use the Vive Tracker feature?

Using the Vive Tracker feature requires installing the pysurvive library:

```bash
pip install pysurvive
```

Then obtain the ViveTracker object via the `get_vive_tracker()` method on the Sense class:

```python
from pika import sense

my_sense = sense()
my_sense.connect()

# Get Vive Tracker object
tracker = my_sense.get_vive_tracker()

# Get device list
devices = tracker.get_devices()
print(f"Detected devices: {devices}")

# Get pose for a specific device
pose = tracker.get_pose("WM0")
if pose:
    print(f"Position: {pose.position}")
    print(f"Rotation: {pose.rotation}")
```

### 5. How do I use multiple Pika devices simultaneously?

Create a separate object for each device and specify different serial port paths:

```python
from pika import sense, gripper

# Create two Sense objects
sense1 = sense('/dev/ttyUSB0')
sense2 = sense('/dev/ttyUSB1')

# Create a Gripper object
grip1 = gripper('/dev/ttyUSB2')

# Connect devices
sense1.connect()
sense2.connect()
grip1.connect()

# Use devices
# ...

# Disconnect
sense1.disconnect()
sense2.disconnect()
grip1.disconnect()
```

### 6. How do I process camera images?

Images returned by Pika SDK are in numpy.ndarray format and can be processed directly with OpenCV:

```python
import cv2
import numpy as np

# Get fisheye camera image
fisheye_camera = my_sense.get_fisheye_camera()
success, frame = fisheye_camera.get_frame()

if success:
    # Display original image
    cv2.imshow('Original Image', frame)
    
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Grayscale Image', gray)
    
    # Edge detection
    edges = cv2.Canny(gray, 100, 200)
    cv2.imshow('Edge Detection', edges)
    
    cv2.waitKey(1)
```

### 7. How do I save and load camera parameters?

You can save and load camera parameters using JSON or YAML format:

```python
import json

# Get camera information
realsense_camera = my_sense.get_realsense_camera()
camera_info = realsense_camera.get_camera_info()

# Save to file
with open('camera_params.json', 'w') as f:
    json.dump(camera_info, f, indent=4)

# Load from file
with open('camera_params.json', 'r') as f:
    loaded_params = json.load(f)

print(f"Loaded camera parameters: {loaded_params}")
```
