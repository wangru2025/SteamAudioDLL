# Steam Audio Python 库 API 文档

## 目录

1. [Context - 全局上下文](#context)
2. [Vector3 - 3D 向量](#vector3)
3. [SpatializationParams - 空间化参数](#spatializationparams)
4. [AudioProcessor - 单源处理器](#audioprocessor)
5. [AudioMixer - 多源混音器](#audiomixer)
6. [RoomReverb - 房间混响](#roomreverb)
7. [DirectEffect - 直接效果](#directeffect)
8. [异常类](#异常类)

---

## Context

全局 Steam Audio 上下文管理器。必须在使用任何其他功能前初始化。

### 初始化

```python
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 在这里使用 Steam Audio
    pass
```

### 参数

- `sample_rate` (int): 采样率，单位 Hz。默认 44100
- `frame_size` (int): 帧大小，单位样本数。默认 256

### 类方法

#### `is_initialized() -> bool`

检查 Steam Audio 是否已初始化。

```python
if steamaudio.Context.is_initialized():
    print("Steam Audio 已初始化")
```

#### `get_instance() -> Context | None`

获取当前 Context 实例。

```python
ctx = steamaudio.Context.get_instance()
```

#### `get_version() -> str`

获取 Steam Audio 库版本。

```python
version = steamaudio.Context.get_version()
print(f"版本: {version}")
```

#### `set_hrtf_enabled(enabled: bool) -> None`

启用或禁用 HRTF（头部相关传递函数）。

```python
with steamaudio.Context():
    steamaudio.Context.set_hrtf_enabled(True)
```

#### `get_hrtf_enabled() -> bool`

检查 HRTF 是否启用。

```python
with steamaudio.Context():
    enabled = steamaudio.Context.get_hrtf_enabled()
```

### 异常

- `InitializationError`: 初始化失败时抛出

---

## Vector3

3D 向量类，支持数学运算。

### 初始化

```python
v = steamaudio.Vector3(x=1.0, y=2.0, z=3.0)
v_zero = steamaudio.Vector3()  # (0, 0, 0)
```

### 属性

- `x` (float): X 坐标
- `y` (float): Y 坐标
- `z` (float): Z 坐标

### 方法

#### `distance_to(other: Vector3) -> float`

计算到另一点的距离。

```python
v1 = steamaudio.Vector3(0, 0, 0)
v2 = steamaudio.Vector3(3, 4, 0)
distance = v1.distance_to(v2)  # 5.0
```

#### `magnitude() -> float`

计算向量的长度。

```python
v = steamaudio.Vector3(3, 4, 0)
length = v.magnitude()  # 5.0
```

#### `length() -> float`

`magnitude()` 的别名。

```python
length = v.length()
```

#### `normalize() -> Vector3`

返回归一化（单位）向量。

```python
v = steamaudio.Vector3(3, 4, 0)
v_norm = v.normalize()  # Vector3(0.6, 0.8, 0)
```

#### `dot(other: Vector3) -> float`

计算点积。

```python
v1 = steamaudio.Vector3(1, 0, 0)
v2 = steamaudio.Vector3(0, 1, 0)
dot = v1.dot(v2)  # 0.0
```

#### `cross(other: Vector3) -> Vector3`

计算叉积。

```python
v1 = steamaudio.Vector3(1, 0, 0)
v2 = steamaudio.Vector3(0, 1, 0)
v3 = v1.cross(v2)  # Vector3(0, 0, 1)
```

#### `to_tuple() -> tuple[float, float, float]`

转换为元组。

```python
t = v.to_tuple()  # (1.0, 2.0, 3.0)
```

### 静态方法

#### `from_tuple(t: tuple[float, float, float]) -> Vector3`

从元组创建向量。

```python
v = steamaudio.Vector3.from_tuple((1, 2, 3))
```

### 运算符

```python
v1 = steamaudio.Vector3(1, 2, 3)
v2 = steamaudio.Vector3(4, 5, 6)

v3 = v1 + v2      # 向量加法
v4 = v1 - v2      # 向量减法
v5 = v1 * 2       # 标量乘法
v6 = 2 * v1       # 标量乘法
v7 = v1 / 2       # 标量除法
v8 = -v1          # 取反
```

---

## SpatializationParams

空间化参数，定义监听者和声源的位置和方向。

### 初始化

```python
params = steamaudio.SpatializationParams()
```

### 属性

#### 监听者属性

- `listener_pos` (Vector3): 监听者位置。默认 (0, 0, 0)
- `listener_forward` (Vector3): 监听者前向方向。默认 (0, 0, 1)
- `listener_up` (Vector3): 监听者上向方向。默认 (0, 1, 0)

#### 声源属性

- `sound_pos` (Vector3): 声源位置。默认 (0, 0, 0)

#### 衰减属性

- `min_distance` (float): 最小距离。默认 0.1
- `max_distance` (float): 最大距离。默认 1000.0
- `rolloff` (float): 衰减因子。默认 1.0
- `directional_attenuation` (float): 方向衰减。默认 1.0

### 属性（只读）

#### `distance -> float`

自动计算监听者到声源的距离。

```python
params.listener_pos = steamaudio.Vector3(0, 0, 0)
params.sound_pos = steamaudio.Vector3(5, 0, 0)
dist = params.distance  # 5.0
```

#### `direction -> Vector3`

自动计算从监听者到声源的方向（归一化）。

```python
direction = params.direction
```

### 方法

#### `to_dict() -> dict`

转换为字典。

```python
d = params.to_dict()
# {
#     'listener_pos': (0, 0, 0),
#     'sound_pos': (5, 0, 0),
#     'distance': 5.0,
#     'direction': (1.0, 0, 0),
#     ...
# }
```

---

## AudioProcessor

单源音频处理器，支持 3D 空间化。

### 初始化

```python
with steamaudio.Context():
    processor = steamaudio.AudioProcessor(input_channels=1)
```

### 参数

- `input_channels` (int): 输入通道数，1 或 2。默认 1

### 属性

- `input_channels` (int): 输入通道数
- `_handle` (AudioProcessorHandle): 内部句柄

### 方法

#### `process(audio_data, params) -> np.ndarray`

处理音频。

```python
import numpy as np

audio = np.random.randn(44100).astype(np.float32)
params = steamaudio.SpatializationParams()
params.listener_pos = steamaudio.Vector3(0, 0, 0)
params.sound_pos = steamaudio.Vector3(5, 0, 0)

output = processor.process(audio, params)
# output.shape = (44100, 2)  # 立体声输出
```

### 参数

- `audio_data` (np.ndarray | list): 输入音频
  - 形状：(frames,) 或 (frames, channels)
  - 数据类型：float32
- `params` (SpatializationParams): 空间化参数

### 返回值

- `np.ndarray`: 处理后的立体声音频，形状 (frames, 2)，数据类型 float32

### 异常

- `AudioProcessingError`: 处理失败时抛出
- `InvalidParameterError`: 参数无效时抛出

### 上下文管理

```python
with steamaudio.Context():
    with steamaudio.AudioProcessor(input_channels=1) as processor:
        output = processor.process(audio, params)
    # 自动清理资源
```

---

## AudioMixer

多源音频混音器。

### 初始化

```python
with steamaudio.Context():
    mixer = steamaudio.AudioMixer(max_sources=32)
```

### 参数

- `max_sources` (int): 最大音源数，1-256。默认 32

### 属性

- `max_sources` (int): 最大音源数
- `_sources` (dict): 音源字典

### 方法

#### `add_source(source_id, input_channels) -> None`

添加音源。

```python
mixer.add_source(0, input_channels=1)
mixer.add_source(1, input_channels=2)
```

### 参数

- `source_id` (int): 唯一音源标识符
- `input_channels` (int): 输入通道数，1 或 2

### 异常

- `InvalidParameterError`: 参数无效或音源已存在
- `AudioProcessingError`: 混音器已满

#### `remove_source(source_id) -> None`

移除音源。

```python
mixer.remove_source(0)
```

### 参数

- `source_id` (int): 音源标识符

### 异常

- `InvalidParameterError`: 音源不存在

#### `get_source_count() -> int`

获取当前音源数。

```python
count = mixer.get_source_count()
```

#### `process(sources_data, params) -> np.ndarray`

处理多个音源并混合。

```python
sources_data = {
    0: audio1,
    1: audio2,
}

params = {
    0: steamaudio.SpatializationParams(...),
    1: steamaudio.SpatializationParams(...),
}

output = mixer.process(sources_data, params)
# output.shape = (frames, 2)  # 立体声混合输出
```

### 参数

- `sources_data` (dict): {source_id: audio_data}
- `params` (dict): {source_id: SpatializationParams}

### 返回值

- `np.ndarray`: 混合后的立体声音频

### 异常

- `AudioProcessingError`: 处理失败
- `InvalidParameterError`: 参数无效

---

## RoomReverb

参数化房间混响效果。

### 初始化

```python
with steamaudio.Context():
    reverb = steamaudio.RoomReverb()
```

### 预设常量

```python
steamaudio.RoomReverb.PRESET_SMALL_ROOM      # 小房间
steamaudio.RoomReverb.PRESET_MEDIUM_ROOM     # 中等房间
steamaudio.RoomReverb.PRESET_LARGE_ROOM      # 大房间
steamaudio.RoomReverb.PRESET_SMALL_HALL      # 小厅
steamaudio.RoomReverb.PRESET_LARGE_HALL      # 大厅
steamaudio.RoomReverb.PRESET_CATHEDRAL       # 教堂
steamaudio.RoomReverb.PRESET_OUTDOOR         # 户外
```

### 方法

#### `set_preset(preset: int) -> None`

设置预设。

```python
reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
```

### 参数

- `preset` (int): 预设常量

### 异常

- `InvalidParameterError`: 预设无效

#### `set_params(room_width, room_height, room_depth, wall_absorption, reverb_time) -> None`

设置自定义参数。

```python
reverb.set_params(
    room_width=5.0,
    room_height=3.0,
    room_depth=4.0,
    wall_absorption=0.5,
    reverb_time=0.8
)
```

### 参数

- `room_width` (float): 房间宽度，单位米。> 0.1
- `room_height` (float): 房间高度，单位米。> 0.1
- `room_depth` (float): 房间深度，单位米。> 0.1
- `wall_absorption` (float): 墙壁吸收系数。0.0-1.0
- `reverb_time` (float): 混响衰减时间（RT60），单位秒。0.1-10.0

### 异常

- `InvalidParameterError`: 参数无效

#### `get_params() -> dict`

获取当前参数。

```python
params = reverb.get_params()
# {
#     'room_width': 5.0,
#     'room_height': 3.0,
#     'room_depth': 4.0,
#     'wall_absorption': 0.5,
#     'reverb_time': 0.8,
# }
```

#### `process(audio_data) -> np.ndarray`

处理音频。

```python
audio = np.random.randn(44100).astype(np.float32)
output = reverb.process(audio)
# output.shape = (44100,)  # 单声道输出
```

### 参数

- `audio_data` (np.ndarray | list): 输入音频，形状 (frames,)

### 返回值

- `np.ndarray`: 处理后的音频

### 异常

- `AudioProcessingError`: 处理失败
- `InvalidParameterError`: 参数无效

---

## DirectEffect

直接效果（遮挡和传输）。

### 初始化

```python
with steamaudio.Context():
    effect = steamaudio.DirectEffect()
```

### 方法

#### `set_params(distance, occlusion, transmission_low, transmission_mid, transmission_high) -> None`

设置参数。

```python
effect.set_params(
    distance=5.0,
    occlusion=0.5,
    transmission_low=0.8,
    transmission_mid=0.6,
    transmission_high=0.4
)
```

### 参数

- `distance` (float): 距离，单位米。> 0.1
- `occlusion` (float): 遮挡因子。0.0-1.0，默认 0.0
- `transmission_low` (float): 低频传输。0.0-1.0，默认 1.0
- `transmission_mid` (float): 中频传输。0.0-1.0，默认 1.0
- `transmission_high` (float): 高频传输。0.0-1.0，默认 1.0

### 异常

- `InvalidParameterError`: 参数无效

#### `process(audio_data) -> np.ndarray`

处理音频。

```python
audio = np.random.randn(44100).astype(np.float32)
output = effect.process(audio)
# output.shape = (44100,)  # 单声道输出
```

### 参数

- `audio_data` (np.ndarray | list): 输入音频，形状 (frames,)

### 返回值

- `np.ndarray`: 处理后的音频

### 异常

- `AudioProcessingError`: 处理失败
- `InvalidParameterError`: 参数无效

---

## 异常类

### SteamAudioError

所有 Steam Audio 异常的基类。

```python
try:
    # Steam Audio 操作
    pass
except steamaudio.SteamAudioError as e:
    print(f"错误: {e}")
```

### InitializationError

初始化失败时抛出。

```python
try:
    with steamaudio.Context():
        pass
except steamaudio.InitializationError as e:
    print(f"初始化失败: {e}")
```

### AudioProcessingError

音频处理失败时抛出。

```python
try:
    output = processor.process(audio, params)
except steamaudio.AudioProcessingError as e:
    print(f"处理失败: {e}")
```

### InvalidParameterError

参数无效时抛出。

```python
try:
    processor = steamaudio.AudioProcessor(input_channels=5)
except steamaudio.InvalidParameterError as e:
    print(f"参数无效: {e}")
```

### ResourceError

资源分配失败时抛出。

```python
try:
    # 资源操作
    pass
except steamaudio.ResourceError as e:
    print(f"资源错误: {e}")
```

---

## 完整示例

```python
import steamaudio
import numpy as np

# 初始化上下文
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 创建处理器
    processor = steamaudio.AudioProcessor(input_channels=1)
    
    # 创建混音器
    mixer = steamaudio.AudioMixer(max_sources=4)
    mixer.add_source(0, input_channels=1)
    mixer.add_source(1, input_channels=1)
    
    # 创建效果
    reverb = steamaudio.RoomReverb()
    reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
    
    direct = steamaudio.DirectEffect()
    direct.set_params(distance=5.0, occlusion=0.3)
    
    # 创建测试音频
    audio1 = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
    audio2 = np.sin(2 * np.pi * 880 * np.arange(44100) / 44100).astype(np.float32)
    
    # 创建空间化参数
    params1 = steamaudio.SpatializationParams()
    params1.listener_pos = steamaudio.Vector3(0, 0, 0)
    params1.sound_pos = steamaudio.Vector3(5, 0, 0)
    
    params2 = steamaudio.SpatializationParams()
    params2.listener_pos = steamaudio.Vector3(0, 0, 0)
    params2.sound_pos = steamaudio.Vector3(-5, 0, 0)
    
    # 混合音源
    mixed = mixer.process(
        {0: audio1, 1: audio2},
        {0: params1, 1: params2}
    )
    
    # 应用效果
    with_reverb = reverb.process(mixed[:, 0])
    with_direct = direct.process(audio1)
    
    print(f"混合输出形状: {mixed.shape}")
    print(f"混响输出形状: {with_reverb.shape}")
    print(f"直接效果输出形状: {with_direct.shape}")
```
