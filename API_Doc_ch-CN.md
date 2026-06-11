# Pika SDK API 文档

<p align="center">
  <a href="API_Doc.md"> English </a> | <a>中文</a>
</p>

## 目录

1. [模块概述](#模块概述)
2. [Sense 类](#sense-类)
3. [Ego 类](#ego-类)
4. [Gripper 类](#gripper-类)
5. [FisheyeCamera 类](#fisheyecamera-类)
6. [RealSenseCamera 类](#realsensecamera-类)
7. [SerialComm 类](#serialcomm-类)
8. [ViveTracker 类](#vivetracker-类)
9. [错误处理](#错误处理)
10. [常见问题解答](#常见问题解答)

## 模块概述

Pika SDK 由以下主要模块组成：

### pika.sense

`pika.sense` 模块提供了对 Pika Sense 设备的访问接口，支持编码器数据读取和相机访问。该模块的核心是 `Sense` 类，用于与 Pika Sense 设备进行通信。

### pika.ego

`pika.ego` 模块提供了对 Pika Ego 设备的访问接口，支持IMU数据读取和相机访问。该模块的核心是 `Ego` 类，用于与 Pika Ego 设备进行通信。

### pika.gripper

`pika.gripper` 模块提供了对 Pika Gripper 设备的访问接口，支持电机控制和状态监测。该模块的核心是 `Gripper` 类，用于与 Pika Gripper 设备进行通信和控制。

### pika.camera

`pika.camera` 模块包含两个子模块：`fisheye` 和 `realsense`，分别提供对鱼眼相机和 RealSense 深度相机的访问接口。

### pika.serial_comm

`pika.serial_comm` 模块提供了底层串口通信功能，用于与 Pika 设备进行数据交换。该模块通常不需要直接使用，而是由 `Sense` 和 `Gripper` 类内部调用。

### pika.tracker

`pika.tracker` 模块提供了对位姿追踪设备的访问接口，目前支持 Vive Tracker 设备。该模块的核心是 `ViveTracker` 类，用于获取设备的位姿数据。

## Sense 类

`Sense` 类是 Pika Sense 设备的主要接口，提供对设备传感器和相机的访问。

### 导入方式

```python
from pika import sense
```

### 初始化

```python
my_sense = sense(port='/dev/ttyUSB0')
```

#### 参数

- `port` (str): 串口设备路径，默认为 '/dev/ttyUSB0'

### 方法

#### connect()

连接 Pika Sense 设备。

```python
success = my_sense.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:

```python
my_sense = sense('/dev/ttyUSB0')
if my_sense.connect():
    print("设备连接成功")
else:
    print("设备连接失败")
```

#### disconnect()

断开 Pika Sense 设备连接，释放资源。

```python
my_sense.disconnect()
```

**返回值**:
- 无

**示例**:
```python
my_sense.disconnect()
print("设备已断开连接")
```

#### get_encoder_data()

获取编码器数据。

```python
encoder_data = my_sense.get_encoder_data()
```

**返回值**:
- `dict`: 包含以下字段的字典:
  - `angle` (float): 角度值
  - `rad` (float): 弧度值

**示例**:
```python
encoder_data = my_sense.get_encoder_data()
print(f"角度: {encoder_data['angle']}")
print(f"弧度: {encoder_data['rad']}")
```

#### get_command_state()

获取命令状态。

```python
state = my_sense.get_command_state()
```

**返回值**:
- `int`: 命令状态码

**示例**:
```python
state = my_sense.get_command_state()
print(f"命令状态: {state}")
```

#### get_gripper_distance()

获取夹爪开合距离。

```python
distance = my_sense.get_gripper_distance()
print(f"夹爪开合距离: {distance}")
```

**返回值**:
- `float`: 夹爪开合距离(mm)

**示例**:
```python
distance = my_sense.get_gripper_distance()
print(f"夹爪开合距离: {distance}")
```


#### set_camera_param(camera_width, camera_height, camera_fps)

设置相机分辨率和帧率。

```python
my_sense.set_camera_param(camera_width, camera_height, camera_fps)
```

**参数**:

- `camera_width` (int): 相机宽度，默认为 640
- `camera_height` (int): 相机高度，默认为 480
- `camera_fps` (int): 相机帧率，默认为 30

**返回值**:

- 无

**示例**:
```python
# 设置相机参数为 640x480，帧率 30fps
my_sense.set_camera_param(640, 480, 30)
```

以下是可选的分辨率和帧率：

|  分辨率  |   帧率   |
| :------: | :------: |
| 1280x720 |    30    |
| 640x480  | 30/60/90 |

#### set_fisheye_camera_index(index)

设置鱼眼相机的索引。

```python
my_sense.set_fisheye_camera_index(index)
```

**参数**:
- `index` (int): 鱼眼相机索引

**返回值**:
- 无

**示例**:
```python
# 设置鱼眼相机索引为 1
my_sense.set_fisheye_camera_index(1)
```

#### set_realsense_serial_number(serial_number)

设置 RealSense 相机序列号。

```python
my_sense.set_realsense_serial_number(serial_number)
```

**参数**:
- `serial_number` (str): RealSense 相机序列号

**返回值**:
- 无

**示例**:
```python
# 设置 RealSense 相机序列号
my_sense.set_realsense_serial_number("12345678")
```

#### get_fisheye_camera()

获取鱼眼相机对象。

```python
fisheye_camera = my_sense.get_fisheye_camera()
```

**返回值**:

- `FisheyeCamera`: 鱼眼相机对象，如果初始化失败则返回 None

**示例**:

```python
fisheye_camera = my_sense.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # 处理图像
        pass
```

#### get_realsense_camera()

获取 RealSense 相机对象。

```python
realsense_camera = my_sense.get_realsense_camera()
```

**返回值**:
- `RealSenseCamera`: RealSense 相机对象，如果初始化失败则返回 None

**示例**:
```python
realsense_camera = my_sense.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # 处理彩色图像
        pass
```

#### set_vive_tracker_config(config_path, lh_config, args)

设置 Vive Tracker 配置参数。

```python
my_sense.set_vive_tracker_config(config_path, lh_config, args)
```

**参数**:
- `config_path` (str, optional): 配置文件路径
- `lh_config` (str, optional): 灯塔配置
- `args` (list, optional): 其他 pysurvive 参数

**返回值**:
- 无

**示例**:
```python
# 设置 Vive Tracker 配置
my_sense.set_vive_tracker_config(config_path="/path/to/config", lh_config="lighthouse_config")
```

#### get_vive_tracker()

获取 Vive Tracker 对象。

```python
vive_tracker = my_sense.get_vive_tracker()
```

**返回值**:
- `ViveTracker`: Vive Tracker 对象，如果初始化失败则返回 None

**示例**:
```python
vive_tracker = my_sense.get_vive_tracker()
if vive_tracker:
    # 获取设备列表
    devices = vive_tracker.get_devices()
    print(f"检测到的设备: {devices}")
```

#### get_pose(device_name)

获取指定设备的位姿数据。

```python
pose = my_sense.get_pose(device_name)
```

**参数**:
- `device_name` (str, optional): 设备名称，如果为 None 则返回所有设备的位姿数据

**返回值**:
- `PoseData` 或 `dict`: 如果指定了 device_name，返回该设备的 PoseData 对象；否则返回包含所有设备位姿的字典 {device_name: PoseData}

**示例**:
```python
# 获取特定设备的位姿
pose = my_sense.get_pose("WM0")
if pose:
    print(f"位置: {pose.position}")
    print(f"旋转: {pose.rotation}")

# 获取所有设备的位姿
all_poses = my_sense.get_pose()
for device_name, pose in all_poses.items():
    print(f"设备 {device_name} - 位置: {pose.position}, 旋转: {pose.rotation}")
```

#### get_tracker_devices()

获取所有已检测到的 Vive Tracker 设备列表。

```python
devices = my_sense.get_tracker_devices()
```

**返回值**:
- `list`: 设备名称列表

**示例**:
```python
devices = my_sense.get_tracker_devices()
print(f"检测到的设备: {devices}")
```

#### light_ctrl(light_id)

控制 Pika Sense 设备的灯光。

```python
my_sense.light_ctrl(light_id)
```

**参数**:
- `light_id` (int): 灯光 ID，0-4 分别对应白、红、绿、蓝、黄灯

**返回值**:
- 无

**示例**:
```python
# 打开白灯
my_sense.light_ctrl(0)
```

#### vibrate_ctrl(mode)

控制 Pika Sense 设备的振动马达。

```python
my_sense.vibrate_ctrl(mode)
```

**参数**:
- `mode` (int): 振动模式，0为关闭，1为开启

**返回值**:
- 无

**示例**:
```python
# 开启振动马达
my_sense.vibrate_ctrl(1)
```

#### get_version()

获取 Pika Sense 设备的固件版本。

```python
my_sense.get_version()
```

**返回值**:
- 无

**示例**:
```python
my_sense.get_version()
```


## Ego 类

`Ego` 类是 Pika Ego 设备的主要接口，提供对 IMU 传感器和相机的访问。

### 导入方式

```python
from pika import ego
```

### 初始化

```python
my_ego = ego(port='/dev/ttyUSB0')
```

#### 参数

- `port` (str): 串口设备路径

### 方法

#### connect()

连接 Pika Ego 设备。

```python
success = my_ego.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:

```python
my_ego = ego('/dev/ttyUSB0')
if my_ego.connect():
    print("设备连接成功")
else:
    print("设备连接失败")
```

#### disconnect()

断开 Pika Ego 设备连接，释放资源。

```python
my_ego.disconnect()
```

**返回值**:
- 无

**示例**:
```python
my_ego.disconnect()
print("设备已断开连接")
```

#### get_imu_data()

获取 IMU 完整原始数据。

```python
imu_data = my_ego.get_imu_data()
```

**返回值**:
- `dict`: 包含以下字段的字典:
  - `acc` (list): 加速度计数据 [x, y, z]，单位为 m/s^2
  - `gyr` (list): 陀螺仪数据 [x, y, z]，单位为 rad/s
  - `mag` (list): 磁力计数据 [x, y, z]，单位为 uT
  - `quat` (list): 四元数 [w, x, y, z]

**示例**:
```python
imu_data = my_ego.get_imu_data()
print(f"加速度: {imu_data['acc']}")
print(f"角速度: {imu_data['gyr']}")
print(f"磁力计: {imu_data['mag']}")
print(f"四元数: {imu_data['quat']}")
```

#### get_accelerometer()

获取加速度计数据。

```python
acc = my_ego.get_accelerometer()
```

**返回值**:
- `list`: [x, y, z] 加速度数据，单位为 m/s^2

**示例**:
```python
acc = my_ego.get_accelerometer()
print(f"加速度: x={acc[0]:.3f}, y={acc[1]:.3f}, z={acc[2]:.3f} m/s^2")
```

#### get_gyroscope()

获取陀螺仪数据。

```python
gyr = my_ego.get_gyroscope()
```

**返回值**:
- `list`: [x, y, z] 角速度数据，单位为 rad/s

**示例**:
```python
gyr = my_ego.get_gyroscope()
print(f"角速度: x={gyr[0]:.3f}, y={gyr[1]:.3f}, z={gyr[2]:.3f} rad/s")
```

#### get_magnetometer()

获取磁力计数据。

```python
mag = my_ego.get_magnetometer()
```

**返回值**:
- `list`: [x, y, z] 磁力计数据，单位为 uT

**示例**:
```python
mag = my_ego.get_magnetometer()
print(f"磁力计: x={mag[0]:.1f}, y={mag[1]:.1f}, z={mag[2]:.1f} uT")
```

#### get_quaternion()

获取四元数姿态数据。

```python
quat = my_ego.get_quaternion()
```

**返回值**:
- `list`: [w, x, y, z] 四元数

**示例**:
```python
quat = my_ego.get_quaternion()
w, x, y, z = quat
print(f"四元数: w={w:.3f}, x={x:.3f}, y={y:.3f}, z={z:.3f}")
```

#### set_camera_param(camera_width, camera_height, camera_fps, fisheye_thread_fps=100)

设置相机分辨率和帧率。

```python
my_ego.set_camera_param(camera_width, camera_height, camera_fps, fisheye_thread_fps=100)
```

**参数**:

- `camera_width` (int): 相机宽度，默认为 1280
- `camera_height` (int): 相机高度，默认为 720
- `camera_fps` (int): 相机帧率，默认为 30
- `fisheye_thread_fps` (int): 鱼眼相机读取线程帧率，默认为 100

**返回值**:
- 无

**示例**:
```python
# 设置相机参数为 1280x720，帧率 30fps，鱼眼线程帧率 100Hz
my_ego.set_camera_param(1280, 720, 30, 100)
```

以下是可选的分辨率和帧率：

|  分辨率  |   帧率   |
| :------: | :------: |
| 1280x720 |    30    |
| 640x480  | 30/60/90 |

#### set_fisheye_camera_index(index)

设置鱼眼相机的索引。

```python
my_ego.set_fisheye_camera_index(index)
```

**参数**:
- `index` (int): 鱼眼相机索引

**返回值**:
- 无

**示例**:
```python
# 设置鱼眼相机索引为 81
my_ego.set_fisheye_camera_index(81)
```

#### set_realsense_serial_number(serial_number)

设置 RealSense 相机序列号。

```python
my_ego.set_realsense_serial_number(serial_number)
```

**参数**:
- `serial_number` (str): RealSense 相机序列号

**返回值**:
- 无

**示例**:
```python
# 设置 RealSense 相机序列号
my_ego.set_realsense_serial_number("260422273747")
```

#### get_fisheye_camera()

获取鱼眼相机对象。

```python
fisheye_camera = my_ego.get_fisheye_camera()
```

**返回值**:
- `FisheyeCamera`: 鱼眼相机对象，如果初始化失败则返回 None

**示例**:
```python
fisheye_camera = my_ego.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # 处理图像
        pass
```

#### get_realsense_camera()

获取 RealSense 相机对象。

```python
realsense_camera = my_ego.get_realsense_camera()
```

**返回值**:
- `RealSenseCamera`: RealSense 相机对象，如果初始化失败则返回 None

**示例**:
```python
realsense_camera = my_ego.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # 处理彩色图像
        pass
```

#### get_version()

获取 Pika Ego 设备的固件版本。

```python
my_ego.get_version()
```

**返回值**:
- `tuple`: 包含版本信息的元组

**示例**:
```python
version_info = my_ego.get_version()
print(f"设备版本: {version_info}")
```

## Gripper 类

`Gripper` 类是 Pika Gripper 设备的主要接口，提供对电机控制和状态监测的访问。

### 导入方式

```python
from pika import gripper
```

### 初始化

```python
my_gripper = gripper(port='/dev/ttyUSB0')
```

#### 参数

- `port` (str): 串口设备路径，默认为 '/dev/ttyUSB0'

### 方法

#### connect()

连接 Pika Gripper 设备。

```python
success = my_gripper.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:
```python
my_gripper = gripper('/dev/ttyUSB0')
if my_gripper.connect():
    print("设备连接成功")
else:
    print("设备连接失败")
```

#### disconnect()

断开 Pika Gripper 设备连接，释放资源。

```python
my_gripper.disconnect()
```

**返回值**:
- 无

**示例**:
```python
my_gripper.disconnect()
print("设备已断开连接")
```

#### enable()

启用电机。

```python
success = my_gripper.enable()
```

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
if my_gripper.enable():
    print("电机已启用")
else:
    print("电机启用失败")
```

#### disable()

禁用电机。

```python
success = my_gripper.disable()
```

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
if my_gripper.disable():
    print("电机已禁用")
else:
    print("电机禁用失败")
```

#### set_zero()

设置当前位置为零点。

```python
success = my_gripper.set_zero()
```

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
if my_gripper.set_zero():
    print("零点已设置")
else:
    print("零点设置失败")
```

#### set_motor_angle(position)

设置电机位置（弧度）。

```python
success = my_gripper.set_motor_angle(position)
```

**参数**:
- `position` (float): 目标位置，单位为弧度

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
# 设置电机位置为 0.5 弧度
if my_gripper.set_motor_angle(0.5):
    print("位置已设置")
else:
    print("位置设置失败")
```

#### set_motor_torque(current)

设置电机电流大小，通过其调整电机力矩。

```python
success = my_gripper.set_motor_torque(current)
```

**参数**:
- `current` (float): 目标电流，单位为A。取值范围通常为 0~8A，超出范围可能导致电机过流保护。

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
# 设置电机电流为 0.8 A
if my_gripper.set_motor_torque(0.8):
    print("电流已设置")
else:
    print("电流设置失败")
```


#### set_gripper_distance(target_gripper_distance_mm)

设置夹爪开合距离（mm）。

```python
success = my_gripper.set_gripper_distance(target_gripper_distance_mm)
```

**参数**:
- `target_gripper_distance_mm` (float): 目标夹爪开合距离（mm）。取值范围通常为 0-90mm，超出范围可能导致操作失败。

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
# 设置夹爪开合距离为 50mm
if my_gripper.set_gripper_distance(50.0):
    print("夹爪距离已设置")
else:
    print("夹爪距离设置失败")
```

#### set_velocity(velocity)

设置电机速度。

```python
success = my_gripper.set_velocity(velocity)
```

**参数**:
- `velocity` (float): 目标速度

**返回值**:

- `bool`: 操作是否成功

**示例**:
```python
# 设置电机速度为 10.0
if my_gripper.set_velocity(10.0):
    print("速度已设置")
else:
    print("速度设置失败")
```

#### set_effort(effort)

设置电机力矩。

```python
success = my_gripper.set_effort(effort)
```

**参数**:

- `effort` (float): 目标力矩

**返回值**:
- `bool`: 操作是否成功

**示例**:
```python
# 设置电机力矩为 5.0
if my_gripper.set_effort(5.0):
    print("力矩已设置")
else:
    print("力矩设置失败")
```

#### get_gripper_distance()

获取夹爪当前开合距离（mm）。

```python
distance = my_gripper.get_gripper_distance()
```

**返回值**:
- `float`: 夹爪当前开合距离（mm）

**示例**:
```python
distance = my_gripper.get_gripper_distance()
print(f"夹爪当前开合距离: {distance} mm")
```

#### get_motor_data()

获取电机完整数据。

```python
motor_data = my_gripper.get_motor_data()
```

**返回值**:
- `dict`: 包含以下字段的字典:
  - `Speed` (float): 电机当前转速（rad/s）
  - `Current` (int): 电机当前相电流（mA）
  - `Position` (float): 电机当前位置（rad）

**示例**:
```python
motor_data = my_gripper.get_motor_data()
print(f"速度: {motor_data['Speed']} rad/s")
print(f"电流: {motor_data['Current']} mA")
print(f"位置: {motor_data['Position']} rad")
```

#### get_motor_status()

获取电机状态。

```python
motor_status = my_gripper.get_motor_status()
```

**返回值**:
- `dict`: 包含以下字段的字典:
  - `Voltage` (float): 电机驱动器电压（V）
  - `DriverTemp` (int): 电机驱动器温度（°C）
  - `MotorTemp` (int): 电机温度（°C）
  - `Status` (str): 电机驱动器状态（十六进制字符串）
  - `BusCurrent` (int): 母线电流（mA）

**示例**:
```python
motor_status = my_gripper.get_motor_status()
print(f"电压: {motor_status['Voltage']} V")
print(f"驱动器温度: {motor_status['DriverTemp']} °C")
print(f"电机温度: {motor_status['MotorTemp']} °C")
print(f"状态码: {motor_status['Status']}")
print(f"母线电流: {motor_status['BusCurrent']} mA")
```

#### get_motor_speed()

获取电机当前转速。

```python
speed = my_gripper.get_motor_speed()
```

**返回值**:
- `float`: 电机当前转速（rad/s）

**示例**:

```python
speed = my_gripper.get_motor_speed()
print(f"电机转速: {speed} rad/s")
```

#### get_motor_current()

获取电机当前相电流。

```python
current = my_gripper.get_motor_current()
```

**返回值**:

- `int`: 电机当前相电流（mA）

**示例**:
```python
current = my_gripper.get_motor_current()
print(f"电机电流: {current} mA")
```

#### get_motor_position()

获取电机当前位置。

```python
position = my_gripper.get_motor_position()
```

**返回值**:
- `float`: 电机当前位置（rad）

**示例**:
```python
position = my_gripper.get_motor_position()
print(f"电机位置: {position} rad")
```

#### get_voltage()

获取电机驱动器电压。

```python
voltage = my_gripper.get_voltage()
```

**返回值**:
- `float`: 电机驱动器电压（V）

**示例**:
```python
voltage = my_gripper.get_voltage()
print(f"驱动器电压: {voltage} V")
```

#### get_driver_temp()

获取电机驱动器温度。

```python
temp = my_gripper.get_driver_temp()
```

**返回值**:
- `int`: 电机驱动器温度（°C）

**示例**:
```python
temp = my_gripper.get_driver_temp()
print(f"驱动器温度: {temp} °C")
```

#### get_motor_temp()

获取电机温度。

```python
temp = my_gripper.get_motor_temp()
```

**返回值**:
- `int`: 电机温度（°C）

**示例**:
```python
temp = my_gripper.get_motor_temp()
print(f"电机温度: {temp} °C")
```

#### get_status_raw()

获取电机驱动器状态（原始字符串）。

```python
status = my_gripper.get_status_raw()
```

**返回值**:

- `str`: 电机驱动器状态（十六进制字符串）

**示例**:

```python
status = my_gripper.get_status_raw()
print(f"驱动器状态: {status}")
```

状态码表：

| 16进制码 |          说明          |
| :------: | :--------------------: |
|   0x00   |  全部正常且驱动器失能  |
|   0x01   |        电压过低        |
|   0x02   |        电机过温        |
|   0x04   |     驱动器电机过流     |
|   0x08   |       驱动器过温       |
|   0x10   |     传感器状态异常     |
|   0x20   |     驱动器错误状态     |
|   0x40   |     驱动器使能姿态     |
|   0x80   | 已经回零 或 已经回过零 |

#### get_bus_current()

获取母线电流。

```python
current = my_gripper.get_bus_current()
```

**返回值**:
- `int`: 母线电流（mA）

**示例**:
```python
current = my_gripper.get_bus_current()
print(f"母线电流: {current} mA")
```

#### set_camera_param(camera_width, camera_height, camera_fps)

设置相机分辨率和帧率。

```python
my_gripper.set_camera_param(camera_width, camera_height, camera_fps)
```

**参数**:
- `camera_width` (int): 相机宽度，默认为 640
- `camera_height` (int): 相机高度，默认为 480
- `camera_fps` (int): 相机帧率，默认为 30

**返回值**:
- 无

**示例**:

```python
# 设置相机参数为 640x480，帧率 30fps
my_gripper.set_camera_param(640, 480, 30)
```

以下是可选的分辨率和帧率：

|  分辨率  |   帧率   |
| :------: | :------: |
| 1280x720 |    30    |
| 640x480  | 30/60/90 |

#### set_fisheye_camera_index(index)

设置鱼眼相机的索引。

```python
my_gripper.set_fisheye_camera_index(index)
```

**参数**:
- `index` (int): 鱼眼相机索引

**返回值**:
- 无

**示例**:
```python
# 设置鱼眼相机索引为 1
my_gripper.set_fisheye_camera_index(1)
```

#### set_realsense_serial_number(serial_number)

设置 RealSense 相机序列号。

```python
my_gripper.set_realsense_serial_number(serial_number)
```

**参数**:
- `serial_number` (str): RealSense 相机序列号

**返回值**:
- 无

**示例**:
```python
# 设置 RealSense 相机序列号
my_gripper.set_realsense_serial_number("12345678")
```

#### get_fisheye_camera()

获取鱼眼相机对象。

```python
fisheye_camera = my_gripper.get_fisheye_camera()
```

**返回值**:
- `FisheyeCamera`: 鱼眼相机对象，如果初始化失败则返回 None

**示例**:
```python
fisheye_camera = my_gripper.get_fisheye_camera()
if fisheye_camera:
    success, frame = fisheye_camera.get_frame()
    if success:
        # 处理图像
        pass
```

#### get_realsense_camera()

获取 RealSense 相机对象。

```python
realsense_camera = my_gripper.get_realsense_camera()
```

**返回值**:
- `RealSenseCamera`: RealSense 相机对象，如果初始化失败则返回 None

**示例**:
```python
realsense_camera = my_gripper.get_realsense_camera()
if realsense_camera:
    success, color_frame = realsense_camera.get_color_frame()
    if success:
        # 处理彩色图像
        pass
```

#### get_version()

获取 Pika Gripper 设备的固件版本。

```python
my_sense.get_version()
```

**返回值**:
- 无

**示例**:
```python
my_sense.get_version()
```


## FisheyeCamera 类

`FisheyeCamera` 类提供对 Pika 设备上鱼眼相机的访问接口。

### 导入方式

通常不需要直接导入，而是通过 `Sense` 或 `Gripper` 类的 `get_fisheye_camera()` 方法获取。

```python
# 如果需要直接导入
from pika.camera.fisheye import FisheyeCamera
```

### 初始化

```python
camera = FisheyeCamera(camera_width=640, camera_height=480, camera_fps=30, device_id=0)
```

#### 参数

- `camera_width` (int): 相机宽度，默认为 640
- `camera_height` (int): 相机高度，默认为 480
- `camera_fps` (int): 相机帧率，默认为 30
- `device_id` (int): 相机设备 ID，默认为 0

### 方法

#### connect()

连接鱼眼相机。

```python
success = camera.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:
```python
camera = FisheyeCamera()
if camera.connect():
    print("相机连接成功")
else:
    print("相机连接失败")
```

#### disconnect()

断开鱼眼相机连接，释放资源。

```python
camera.disconnect()
```

**返回值**:
- 无

**示例**:
```python
camera.disconnect()
print("相机已断开连接")
```

#### get_frame()

获取一帧图像。

```python
success, frame = camera.get_frame()
```

**返回值**:
- `tuple`: (成功标志, 图像数据)
  - `success` (bool): 获取是否成功
  - `frame` (numpy.ndarray): 图像数据，如果获取失败则为 None

**示例**:
```python
success, frame = camera.get_frame()
if success:
    import cv2
    cv2.imshow('鱼眼相机', frame)
    cv2.waitKey(1)
```

#### get_camera_info()

获取相机信息。

```python
info = camera.get_camera_info()
```

**返回值**:
- `dict`: 包含以下字段的字典:
  - `width` (int): 图像宽度
  - `height` (int): 图像高度
  - `fps` (float): 帧率
  - `device_id` (int): 设备 ID

**示例**:
```python
info = camera.get_camera_info()
print(f"分辨率: {info['width']}x{info['height']}")
print(f"帧率: {info['fps']}")
print(f"设备 ID: {info['device_id']}")
```

## RealSenseCamera 类

`RealSenseCamera` 类提供对 Pika 设备上 RealSense D405 深度相机的访问接口。

### 导入方式

通常不需要直接导入，而是通过 `Sense` 或 `Gripper` 类的 `get_realsense_camera()` 方法获取。

```python
# 如果需要直接导入
from pika.camera.realsense import RealSenseCamera
```

### 初始化

```python
camera = RealSenseCamera(camera_width=640, camera_height=480, camera_fps=30, serial_number=None)
```

#### 参数

- `camera_width` (int): 相机宽度，默认为 640
- `camera_height` (int): 相机高度，默认为 480
- `camera_fps` (int): 相机帧率，默认为 30
- `serial_number` (str): 相机序列号，默认为 None

### 方法

#### connect()

连接 RealSense 相机。

```python
success = camera.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:
```python
camera = RealSenseCamera()
if camera.connect():
    print("相机连接成功")
else:
    print("相机连接失败")
```

#### disconnect()

断开 RealSense 相机连接，释放资源。

```python
camera.disconnect()
```

**返回值**:
- 无

**示例**:
```python
camera.disconnect()
print("相机已断开连接")
```

#### get_frames()

获取一组帧（彩色和深度）。

```python
success, color_image, depth_image = camera.get_frames()
```

**返回值**:
- `tuple`: (成功标志, 彩色图像, 深度图像)
  - `success` (bool): 获取是否成功
  - `color_image` (numpy.ndarray): 彩色图像数据，如果获取失败则为 None
  - `depth_image` (numpy.ndarray): 深度图像数据，如果获取失败则为 None

**示例**:
```python
success, color_image, depth_image = camera.get_frames()
if success:
    import cv2
    cv2.imshow('彩色图像', color_image)
    
    # 将深度图像归一化以便显示
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
    cv2.imshow('深度图像', depth_colormap)
    
    cv2.waitKey(1)
```

#### get_color_frame()

获取彩色图像。

```python
success, color_image = camera.get_color_frame()
```

**返回值**:
- `tuple`: (成功标志, 彩色图像)
  - `success` (bool): 获取是否成功
  - `color_image` (numpy.ndarray): 彩色图像数据，如果获取失败则为 None

**示例**:
```python
success, color_image = camera.get_color_frame()
if success:
    import cv2
    cv2.imshow('彩色图像', color_image)
    cv2.waitKey(1)
```

#### get_depth_frame()

获取深度图像。

```python
success, depth_image = camera.get_depth_frame()
```

**返回值**:
- `tuple`: (成功标志, 深度图像)
  - `success` (bool): 获取是否成功
  - `depth_image` (numpy.ndarray): 深度图像数据，如果获取失败则为 None

**示例**:
```python
success, depth_image = camera.get_depth_frame()
if success:
    import cv2
    import numpy as np
    
    # 将深度图像归一化以便显示
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
    cv2.imshow('深度图像', depth_colormap)
    cv2.waitKey(1)
```

#### get_camera_info()	

获取相机信息。

```python
info = camera.get_camera_info()
```

**返回值**:
- `dict`: 包含相机内参和序列号的字典:
  - `color_width` (int): 彩色图像宽度
  - `color_height` (int): 彩色图像高度
  - `color_fx` (float): 彩色相机 x 方向焦距
  - `color_fy` (float): 彩色相机 y 方向焦距
  - `color_ppx` (float): 彩色相机 x 方向主点
  - `color_ppy` (float): 彩色相机 y 方向主点
  - `depth_width` (int): 深度图像宽度
  - `depth_height` (int): 深度图像高度
  - `depth_fx` (float): 深度相机 x 方向焦距
  - `depth_fy` (float): 深度相机 y 方向焦距
  - `depth_ppx` (float): 深度相机 x 方向主点
  - `depth_ppy` (float): 深度相机 y 方向主点
  - `serial_number` (str): 相机序列号

**示例**:
```python
info = camera.get_camera_info()
print(f"彩色分辨率: {info['color_width']}x{info['color_height']}")
print(f"深度分辨率: {info['depth_width']}x{info['depth_height']}")
print(f"彩色相机焦距: ({info['color_fx']}, {info['color_fy']})")
print(f"深度相机焦距: ({info['depth_fx']}, {info['depth_fy']})")
print(f"序列号: {info['serial_number']}")
```

## SerialComm 类

`SerialComm` 类提供底层串口通信功能，用于与 Pika 设备进行数据交换。通常不需要直接使用，而是由 `Sense` 和 `Gripper` 类内部调用。

### 导入方式

```python
from pika.serial_comm import SerialComm
```

### 初始化

```python
serial_comm = SerialComm(port='/dev/ttyUSB0', baudrate=460800, timeout=1.0)
```

#### 参数

- `port` (str): 串口设备路径，默认为 '/dev/ttyUSB0'
- `baudrate` (int): 波特率，默认为 460800
- `timeout` (float): 超时时间，默认为 1.0 秒

### 方法

#### connect()

连接串口设备。

```python
success = serial_comm.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:
```python
serial_comm = SerialComm('/dev/ttyUSB0')
if serial_comm.connect():
    print("串口连接成功")
else:
    print("串口连接失败")
```

#### disconnect()

断开串口设备连接。

```python
serial_comm.disconnect()
```

**返回值**:
- 无

**示例**:
```python
serial_comm.disconnect()
print("串口已断开连接")
```

#### send_data(data)

发送数据到串口。

```python
success = serial_comm.send_data(data)
```

**参数**:
- `data` (bytes): 要发送的数据

**返回值**:
- `bool`: 发送是否成功

**示例**:
```python
data = b'Hello, Pika!\r\n'
if serial_comm.send_data(data):
    print("数据发送成功")
else:
    print("数据发送失败")
```

#### send_command(command_type, value)

发送命令到设备。

```python
success = serial_comm.send_command(command_type, value)
```

**参数**:
- `command_type` (int): 命令类型
- `value` (float): 命令值，默认为 0.0

**返回值**:
- `bool`: 发送是否成功

**示例**:
```python
# 发送命令类型 1，值为 0.5
if serial_comm.send_command(1, 0.5):
    print("命令发送成功")
else:
    print("命令发送失败")
```

#### read_data()

从串口读取数据。

```python
data = serial_comm.read_data()
```

**返回值**:
- `bytes`: 读取到的数据

**示例**:
```python
data = serial_comm.read_data()
if data:
    print(f"读取到数据: {data}")
```

#### start_reading_thread(callback)

启动数据读取线程。

```python
serial_comm.start_reading_thread(callback=my_callback_function)
```

**参数**:
- `callback` (function): 数据回调函数，接收解析后的 JSON 数据

**返回值**:
- 无

**示例**:
```python
def my_callback(json_data):
    print(f"收到数据: {json_data}")

serial_comm.start_reading_thread(callback=my_callback)
```

#### stop_reading_thread()

停止数据读取线程。

```python
serial_comm.stop_reading_thread()
```

**返回值**:
- 无

**示例**:
```python
serial_comm.stop_reading_thread()
print("读取线程已停止")
```

#### get_latest_data()

获取最新的数据。

```python
data = serial_comm.get_latest_data()
```

**返回值**:
- `dict`: 最新的数据

**示例**:
```python
data = serial_comm.get_latest_data()
print(f"最新数据: {data}")
```

## ViveTracker 类

`ViveTracker` 类提供对 Vive Tracker 设备位姿数据的访问接口。

### 导入方式

通常不需要直接导入，而是通过 `Sense` 类的 `get_vive_tracker()` 方法获取。

```python
# 如果需要直接导入
from pika.tracker.vive_tracker import ViveTracker
```

### 初始化

```python
tracker = ViveTracker(config_path=None, lh_config=None, args=None)
```

#### 参数

- `config_path` (str, optional): 配置文件路径
- `lh_config` (str, optional): 灯塔配置
- `args` (list, optional): 其他 pysurvive 参数

### 方法

#### connect()

初始化并连接到 Vive Tracker 设备。

```python
success = tracker.connect()
```

**返回值**:
- `bool`: 连接是否成功

**示例**:
```python
tracker = ViveTracker()
if tracker.connect():
    print("Vive Tracker 连接成功")
else:
    print("Vive Tracker 连接失败")
```

#### disconnect()

断开 Vive Tracker 设备连接。

```python
tracker.disconnect()
```

**返回值**:
- 无

**示例**:
```python
tracker.disconnect()
print("Vive Tracker 已断开连接")
```

#### get_pose(device_name)

获取指定设备的最新位姿数据。

```python
pose = tracker.get_pose(device_name)
```

**参数**:
- `device_name` (str, optional): 设备名称，如果为 None 则返回所有设备的位姿数据

**返回值**:
- `PoseData` 或 `dict`: 如果指定了 device_name，返回该设备的 PoseData 对象；否则返回包含所有设备位姿的字典 {device_name: PoseData}

**示例**:
```python
# 获取特定设备的位姿
pose = tracker.get_pose("WM0")
if pose:
    print(f"位置: {pose.position}")
    print(f"旋转: {pose.rotation}")

# 获取所有设备的位姿
all_poses = tracker.get_pose()
for device_name, pose in all_poses.items():
    print(f"设备 {device_name} - 位置: {pose.position}, 旋转: {pose.rotation}")
```

获取到 tracker pose 位姿的坐标图如下：

![img](img/mmexport1746516732555.png)

坐标系位于夹爪中

#### get_devices()

获取所有已检测到的设备列表。

```python
devices = tracker.get_devices()
```

**返回值**:
- `list`: 设备名称列表

**示例**:
```python
devices = tracker.get_devices()
print(f"检测到的设备: {devices}")
```

#### get_device_info(device_name)

获取设备信息。

```python
info = tracker.get_device_info(device_name)
```

**参数**:
- `device_name` (str, optional): 设备名称，如果为 None 则返回所有设备的信息

**返回值**:
- `dict`: 设备信息字典

**示例**:
```python
# 获取特定设备的信息
info = tracker.get_device_info("WM0")
if info:
    print(f"更新次数: {info['updates']}")
    print(f"最后更新时间: {info['last_update']}")

# 获取所有设备的信息
all_info = tracker.get_device_info()
for device_name, info in all_info.items():
    print(f"设备 {device_name} - 更新次数: {info['updates']}, 最后更新时间: {info['last_update']}")
```

### PoseData 类

`PoseData` 类用于存储和格式化位姿信息。

#### 属性

- `device_name` (str): 设备名称
- `timestamp` (float): 时间戳
- `position` (list): 位置 [x, y, z]
- `rotation` (list): 旋转四元数 [x, y, z, w]

#### 示例

```python
# 通过 ViveTracker 获取 PoseData 对象
pose = tracker.get_pose("WM0")
if pose:
    print(f"设备名称: {pose.device_name}")
    print(f"时间戳: {pose.timestamp}")
    print(f"位置: {pose.position}")  # [x, y, z]
    print(f"旋转: {pose.rotation}")  # [x, y, z, w] 四元数
    
    # 提取位置和旋转数据用于进一步处理
    position = pose.position  # [x, y, z]
    rotation = pose.rotation  # [x, y, z， w] 四元数
    
    # 计算位置的平方和（用于距离计算）
    distance_squared = sum([p*p for p in position])
    print(f"距离原点的平方: {distance_squared:.6f}")
    
    # 提取旋转四元数的各个分量
    x, y, z, w = rotation
    print(f"四元数分量: x={x:.6f}, y={y:.6f}, z={z:.6f}, w={w:.6f}")
```

## 错误处理

Pika SDK 使用 Python 的日志系统记录错误和警告信息，便于开发者进行调试和问题排查。默认情况下，日志级别设置为 INFO，记录基本的操作信息和错误。如果您需要更详细的日志信息，可以将日志级别设置为 DEBUG：

```python
import logging
logging.getLogger('pika').setLevel(logging.DEBUG)  # 设置为 DEBUG 级别以获取更详细的日志
```

SDK 中的大多数方法都会在发生错误时返回特定的错误码或 False 值，并在日志中记录详细的错误信息。建议在开发过程中密切关注日志输出，及时发现和解决问题。

对于常见的错误情况，如设备未连接、相机初始化失败等，SDK 会提供清晰的错误提示，并尽可能地进行优雅的错误处理，避免程序崩溃。

## 常见问题解答

### 1. 如何确定串口设备路径？

在 Linux 系统中，可以使用以下命令查看所有串口设备：

```bash
ls /dev/ttyUSB*
```

如果有多个设备，可以尝试断开并重新连接 Pika 设备，观察哪个设备路径出现或消失，从而确定正确的设备路径。

### 2. 为什么无法连接到 RealSense 相机？

首先确保已安装 pyrealsense2 库：

```bash
pip install pyrealsense2
```

如果仍然无法连接，可能是因为：

- RealSense 相机未正确连接到 USB 端口
- 使用的 USB 端口带宽不足，尝试使用 USB 3.0 或更高版本的端口
- 相机序列号设置错误，尝试不指定序列号或使用正确的序列号

### 3. 如何解决串口访问权限问题？

如果遇到串口访问权限问题，可以将用户添加到 dialout 组：

```bash
sudo usermod -a -G dialout $USER
```

添加后需要重新登录系统使权限生效。

### 4. 如何使用 Vive Tracker 功能？

使用 Vive Tracker 功能需要安装 pysurvive 库：

```bash
pip install pysurvive
```

然后通过 Sense 类的 get_vive_tracker() 方法获取 ViveTracker 对象：

```python
from pika import sense

my_sense = sense()
my_sense.connect()

# 获取 Vive Tracker 对象
tracker = my_sense.get_vive_tracker()

# 获取设备列表
devices = tracker.get_devices()
print(f"检测到的设备: {devices}")

# 获取特定设备的位姿
pose = tracker.get_pose("WM0")
if pose:
    print(f"位置: {pose.position}")
    print(f"旋转: {pose.rotation}")
```

### 5. 如何同时使用多个 Pika 设备？

可以为每个设备创建单独的对象，并指定不同的串口路径：

```python
from pika import sense, gripper

# 创建两个 Sense 对象
sense1 = sense('/dev/ttyUSB0')
sense2 = sense('/dev/ttyUSB1')

# 创建一个 Gripper 对象
grip1 = gripper('/dev/ttyUSB2')

# 连接设备
sense1.connect()
sense2.connect()
grip1.connect()

# 使用设备
# ...

# 断开连接
sense1.disconnect()
sense2.disconnect()
grip1.disconnect()
```

### 6. 如何处理相机图像？

Pika SDK 返回的图像是 numpy.ndarray 格式，可以直接使用 OpenCV 进行处理：

```python
import cv2
import numpy as np

# 获取鱼眼相机图像
fisheye_camera = my_sense.get_fisheye_camera()
success, frame = fisheye_camera.get_frame()

if success:
    # 显示原始图像
    cv2.imshow('原始图像', frame)
    
    # 灰度转换
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    cv2.imshow('灰度图像', gray)
    
    # 边缘检测
    edges = cv2.Canny(gray, 100, 200)
    cv2.imshow('边缘检测', edges)
    
    cv2.waitKey(1)
```

### 7. 如何保存和加载相机参数？

可以使用 JSON 或 YAML 格式保存和加载相机参数：

```python
import json

# 获取相机信息
realsense_camera = my_sense.get_realsense_camera()
camera_info = realsense_camera.get_camera_info()

# 保存到文件
with open('camera_params.json', 'w') as f:
    json.dump(camera_info, f, indent=4)

# 从文件加载
with open('camera_params.json', 'r') as f:
    loaded_params = json.load(f)

print(f"加载的相机参数: {loaded_params}")
```
