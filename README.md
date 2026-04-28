# SteamAudioDLL

本项目为 Steam Audio SDK 提供简单的 C 接口封装，并包含 Python 绑定与演示应用。

## 项目说明

本项目使用了大量来自 [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev) 的代码。除了对 Steam Audio 接口的封装、整理和 Python 绑定外，仓库中不少实际调用 Steam Audio 的实现都来自 NVGT 项目。

本项目当前主要工作是：

- 提供更方便调用的 C 接口
- 提供 Python ctypes 绑定
- 补充可直接运行的演示应用
- 提供基础测试和文档

## 主要功能

- 暴露 Steam Audio 的 C 接口，方便其他语言调用
- Python 包装，提供更直接的 API
- 单源空间化处理
- 多源混音
- 房间混响
- 直达声效果
- 几何场景与材质
- 基于场景的直达声模拟
- 基于场景的反射效果
- 包含交互式 3D 音频演示

## 系统要求

### 编译环境

- CMake 3.20+
- MSVC / Visual Studio Build Tools
- Steam Audio SDK
- Windows

### Python 环境

- Python 3.7+
- NumPy 1.20+
- soundfile
- pyaudio
- wxPython（演示应用使用）

## 快速开始

### 1. 编译 C++ 库

```powershell
git clone https://github.com/wangru2025/SteamAudioDLL.git
cd SteamAudioDLL

python -m cmake -S . -B build -G "Visual Studio 17 2022" -A x64
python -m cmake --build build --config Release
```

编译完成后，主 DLL 位于：

`build/bin/Release/SteamAudioDLL.dll`

同时，构建过程会自动把运行 Python 所需的 DLL 同步到：

`python-steamaudio/steamaudio/bindings/dll/`

### 2. 安装 Python 包

```powershell
cd python-steamaudio
python -m pip install -e .
```

### 3. 运行演示

```powershell
cd python
python interactive_3d_lib.py
```

## 使用示例

### Python - 单源音频处理

```python
import steamaudio
import numpy as np

with steamaudio.Context(sample_rate=44100, frame_size=256):
    processor = steamaudio.AudioProcessor(input_channels=1)

    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)
    params.sound_pos = steamaudio.Vector3(5, 0, 0)

    audio = np.random.randn(44100).astype(np.float32)
    output = processor.process(audio, params)

    print(output.shape)  # (44100, 2)
```

### Python - 多源混音

```python
with steamaudio.Context():
    mixer = steamaudio.AudioMixer(max_sources=8)

    mixer.add_source(0, input_channels=1)
    mixer.add_source(1, input_channels=1)

    output = mixer.process(
        {
            0: audio_chunk_1,
            1: audio_chunk_2,
        },
        {
            0: params_1,
            1: params_2,
        }
    )
```

### Python - 房间混响

```python
with steamaudio.Context():
    reverb = steamaudio.RoomReverb()
    reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
    output = reverb.process(audio)
```

### Python - 几何场景与材质

```python
with steamaudio.Context():
    scene = steamaudio.GeometryScene()

    scene.add_static_mesh(
        vertices=[
            steamaudio.Vector3(0, 0, 0),
            steamaudio.Vector3(1, 0, 0),
            steamaudio.Vector3(0, 1, 0),
        ],
        triangles=[(0, 1, 2)],
        material_indices=[0],
        materials=[steamaudio.Material.preset("concrete")],
    )

    scene.commit()
```

### Python - 直达声模拟

```python
with steamaudio.Context():
    scene = steamaudio.GeometryScene()
    scene.add_static_mesh(
        vertices=[
            steamaudio.Vector3(0, 0, 0),
            steamaudio.Vector3(1, 0, 0),
            steamaudio.Vector3(0, 1, 0),
        ],
        triangles=[(0, 1, 2)],
        material_indices=[0],
        materials=[steamaudio.Material.preset("brick")],
    )
    scene.commit()

    simulator = steamaudio.DirectSimulator(scene, max_sources=1)
    simulator.add_source(0)
    simulator.set_listener(steamaudio.Vector3(0, 0, 0))
    simulator.set_source(
        0,
        steamaudio.Vector3(2, 0, 0),
        direct_flags=(
            steamaudio.DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION
            | steamaudio.DIRECT_EFFECT_APPLY_AIR_ABSORPTION
            | steamaudio.DIRECT_EFFECT_APPLY_OCCLUSION
            | steamaudio.DIRECT_EFFECT_APPLY_TRANSMISSION
        ),
    )
    simulator.run_direct()

    params = simulator.get_direct_params(0)
```

### Python - AudioEnvironment 高层封装

```python
with steamaudio.Context():
    env = steamaudio.AudioEnvironment(
        max_sources=2,
        settings=steamaudio.EnvironmentSettings(
            geometry=steamaudio.GeometrySettings(enabled=True),
            indirect=steamaudio.IndirectSoundSettings(
                enabled=True,
                quality="medium",
                mix_level=0.9,
            ),
        ),
    )
    env.add_room(12.0, 3.0, 10.0, wall_material="plaster")
    env.add_wall_with_doorway("x", 0.0, -5.0, 5.0, 3.0, material="brick")
    env.commit_geometry()

    env.add_source(0, steamaudio.SourceConfig(position=steamaudio.Vector3(-2, 0, 0)))
    env.add_source(1, steamaudio.SourceConfig(position=steamaudio.Vector3(2, 0, 0)))
    env.update_sources({1: {"occlusion_radius": 1.5, "num_occlusion_samples": 32}})
    env.set_listener(steamaudio.Vector3(0, 0, 0))
    env.settings.indirect.num_rays = 1024
    env.settings.indirect.num_bounces = 16
    env.settings.indirect.duration = 1.5

    output = env.process({0: audio_chunk_1, 1: audio_chunk_2})
```

### C++ - 直接使用

```cpp
#include "c_interface.h"

steam_audio_init(44100, 256);

AudioProcessorHandle processor = audio_processor_create(1, 2);

SpatializationParams params{};
params.listener_pos = {0, 0, 0};
params.listener_forward = {0, 0, 1};
params.listener_up = {0, 1, 0};
params.sound_pos = {5, 0, 0};
params.min_distance = 0.1f;
params.max_distance = 1000.0f;
params.rolloff = 1.0f;
params.directional_attenuation = 1.0f;

float input[256]{};
float output[512]{};
int output_frames = 256;

audio_processor_process(
    processor,
    input,
    256,
    output,
    &output_frames,
    &params
);

audio_processor_destroy(processor);
steam_audio_shutdown();
```

## 交互式演示

演示应用提供了一个可视化的 3D 音频环境，并包含房间几何、隔墙、门洞、混响、直达声和场景反射。

### 控制方式

- `方向键`：移动听者位置
- `空格键`：启用 / 禁用混响
- `F3`：打开混响预设菜单
- `F4`：打开几何设置对话框
- `F5`：启用 / 禁用几何应用
- `F6`：启用 / 禁用场景反射
- `Alt + F4`：关闭窗口

## 文档

- Python 包说明：[`python-steamaudio/README.md`](python-steamaudio/README.md)
- Python API 文档：[`python-steamaudio/API.md`](python-steamaudio/API.md)
- 更新日志：[`CHANGELOG.md`](CHANGELOG.md)

## 项目结构

```text
SteamAudioDLL/
├── include/
├── src/
├── python/
├── python-steamaudio/
├── steamaudio/
├── build/
├── CMakeLists.txt
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── NVGT_LICENSE.md
└── README.md
```

## 测试

运行 Python 测试：

```powershell
python -m pytest python-steamaudio\tests -q
```

## 许可证

本项目采用 zlib 许可证，详见 [`LICENSE`](LICENSE)。

### 重要说明

本项目使用了大量来自 [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev) 的代码。NVGT 由 Sam Tupy 开发，采用 zlib 许可证。详细信息请参阅 [`NVGT_LICENSE.md`](NVGT_LICENSE.md)。

Steam Audio SDK 由 Valve Corporation 提供，遵循其自身的许可条款。

## 致谢

- [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev)
- [Steam Audio](https://valvesoftware.github.io/steam-audio/)
- 所有贡献者

## 联系方式

- 问题反馈：<https://github.com/wangru2025/SteamAudioDLL/issues>
- 讨论：<https://github.com/wangru2025/SteamAudioDLL/discussions>
