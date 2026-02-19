# Steam Audio Python 库

一个高级的、Pythonic 的 Steam Audio C 库包装器。提供 3D 音频空间化、混音和效果处理，具有简洁易用的 API。

## 功能特性

- **3D 音频空间化** - 在 3D 空间中定位声音，支持 HRTF 双耳渲染
- **多源混音** - 混合多个空间定位的音频源
- **房间混响** - 参数化房间声学模拟
- **直接效果** - 遮挡和传输建模
- **Pythonic API** - 简洁直观的接口，隐藏 C 复杂性
- **自动资源管理** - 使用上下文管理器安全管理资源
- **类型提示** - 完整的类型注解支持 IDE

## 安装

```bash
pip install steamaudio
```

## 快速开始

```python
import steamaudio
import numpy as np

# 初始化 Steam Audio 上下文
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 创建单源处理器
    processor = steamaudio.AudioProcessor(input_channels=1)
    
    # 创建空间化参数
    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)
    params.sound_pos = steamaudio.Vector3(5, 0, 0)
    
    # 处理音频
    audio = np.random.randn(44100).astype(np.float32)
    output = processor.process(audio, params)
    
    # output 是立体声 (44100, 2)
```

## 多源混音

```python
with steamaudio.Context():
    mixer = steamaudio.AudioMixer(max_sources=8)
    
    # 添加音源
    mixer.add_source(0, input_channels=1)
    mixer.add_source(1, input_channels=1)
    
    # 准备音频和参数
    sources_data = {
        0: audio_chunk_1,
        1: audio_chunk_2,
    }
    
    params = {
        0: steamaudio.SpatializationParams(...),
        1: steamaudio.SpatializationParams(...),
    }
    
    # 混合音源
    output = mixer.process(sources_data, params)
```

## 房间混响

```python
with steamaudio.Context():
    reverb = steamaudio.RoomReverb()
    
    # 使用预设
    reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
    
    # 或设置自定义参数
    reverb.set_params(
        room_width=5.0,
        room_height=3.0,
        room_depth=4.0,
        wall_absorption=0.5,
        reverb_time=0.8
    )
    
    # 处理音频
    output = reverb.process(audio)
```

## 直接效果（遮挡）

```python
with steamaudio.Context():
    effect = steamaudio.DirectEffect()
    
    # 设置参数
    effect.set_params(
        distance=5.0,
        occlusion=0.5,
        transmission_low=0.8,
        transmission_mid=0.6,
        transmission_high=0.4
    )
    
    # 处理音频
    output = effect.process(audio)
```

## 3D 向量操作

```python
v1 = steamaudio.Vector3(1, 2, 3)
v2 = steamaudio.Vector3(4, 5, 6)

# 向量运算
v3 = v1 + v2
v4 = v1 * 2
distance = v1.distance_to(v2)
normalized = v1.normalize()
dot_product = v1.dot(v2)
cross_product = v1.cross(v2)
```

## API 参考

### Context

全局 Steam Audio 上下文管理器。

```python
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 使用 Steam Audio
    pass
```

### Vector3

3D 向量，支持数学运算。

```python
v = steamaudio.Vector3(x, y, z)
v.distance_to(other)
v.normalize()
v.dot(other)
v.cross(other)
```

### SpatializationParams

3D 音频空间化参数。

```python
params = steamaudio.SpatializationParams()
params.listener_pos = steamaudio.Vector3(...)
params.listener_forward = steamaudio.Vector3(...)
params.listener_up = steamaudio.Vector3(...)
params.sound_pos = steamaudio.Vector3(...)
params.min_distance = 0.1
params.max_distance = 1000.0
params.rolloff = 1.0
params.directional_attenuation = 1.0
```

### AudioProcessor

单源音频处理器。

```python
processor = steamaudio.AudioProcessor(input_channels=1)
output = processor.process(audio, params)
```

### AudioMixer

多源音频混音器。

```python
mixer = steamaudio.AudioMixer(max_sources=32)
mixer.add_source(source_id, input_channels=1)
mixer.remove_source(source_id)
output = mixer.process(sources_data, params)
```

### RoomReverb

参数化房间混响效果。

```python
reverb = steamaudio.RoomReverb()
reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
reverb.set_params(room_width, room_height, room_depth, wall_absorption, reverb_time)
params = reverb.get_params()
output = reverb.process(audio)
```

### DirectEffect

直接效果（遮挡和传输）。

```python
effect = steamaudio.DirectEffect()
effect.set_params(distance, occlusion, transmission_low, transmission_mid, transmission_high)
output = effect.process(audio)
```

## 系统要求

- Python 3.7+
- NumPy 1.20+
- Steam Audio C 库（自动包含）

## 打包应用

### PyInstaller

```bash
pyinstaller --onefile your_script.py
```

DLL 文件会自动被包含。

### Nuitka

```bash
python -m nuitka \
    --onefile \
    --include-package=steamaudio \
    your_script.py
```

详见 `PACKAGING.md`。

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献

欢迎提交 Pull Request！

## 支持

如有问题或建议，请提交 Issue。
