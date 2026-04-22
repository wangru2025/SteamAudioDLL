# SteamAudioDLL

本项目为Steam Audio SDK提供简单的C接口封装，并包含Python绑定。

## 项目说明

本项目使用了大量来自 [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev) 的代码。除了对Steam Audio API的简单封装外，其他所有调用Steam Audio的代码都来自NVGT项目。本项目主要工作是：

- 提供方便的C接口封装
- 创建Python ctypes绑定
- 添加简单的演示应用

## 主要功能

- 暴露Steam Audio的C接口，方便其他语言调用
- Python包装，提供Pythonic的API
- 包含交互式3D音频演示

## 📋 系统要求

### 编译环境
- CMake 3.20+
- MSVC
- Steam Audio SDK
- Windows操作系统（当前版本）

### Python环境
- Python 3.7+
- NumPy 1.20+
- soundfile（音频文件读取）
- pyaudio（音频播放）
- wxPython（可选，用于演示应用）

## 🚀 快速开始

### 1. 编译C++库

```bash
# 克隆仓库
git clone https://github.com/wangru2025/SteamAudioDLL.git
cd SteamAudioDLL

# 创建构建目录
mkdir build
cd build

# 配置和编译
cmake -G "MinGW Makefiles" ..
cmake --build .
```

编译完成后，DLL文件将位于 `build/bin/Release/SteamAudioDLL.dll`

### 2. 安装Python包

```bash
cd python-steamaudio
pip install -e .
```

### 3. 运行演示

```bash
cd python
python interactive_3d.py
```

## 📖 使用示例

### Python - 单源音频处理

```python
import steamaudio
import numpy as np

# 初始化Steam Audio上下文
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 创建音频处理器
    processor = steamaudio.AudioProcessor(input_channels=1)
    
    # 设置空间化参数
    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)  # 听者位置
    params.sound_pos = steamaudio.Vector3(5, 0, 0)     # 声源位置
    
    # 处理音频（单声道输入 -> 立体声输出）
    audio = np.random.randn(44100).astype(np.float32)
    output = processor.process(audio, params)
    
    print(f"输出形状: {output.shape}")  # (44100, 2)
```

### Python - 多源混音

```python
with steamaudio.Context():
    # 创建混音器，支持最多8个音源
    mixer = steamaudio.AudioMixer(max_sources=8)
    
    # 添加两个音源
    mixer.add_source(0, input_channels=1)
    mixer.add_source(1, input_channels=1)
    
    # 准备音频数据
    sources_data = {
        0: audio_chunk_1,  # 第一个音源
        1: audio_chunk_2,  # 第二个音源
    }
    
    # 设置每个音源的空间化参数
    params = {
        0: steamaudio.SpatializationParams(
            listener_pos=steamaudio.Vector3(0, 0, 0),
            sound_pos=steamaudio.Vector3(5, 0, 0)
        ),
        1: steamaudio.SpatializationParams(
            listener_pos=steamaudio.Vector3(0, 0, 0),
            sound_pos=steamaudio.Vector3(-5, 0, 0)
        ),
    }
    
    # 混合所有音源
    output = mixer.process(sources_data, params)
```

### Python - 房间混响

```python
with steamaudio.Context():
    reverb = steamaudio.RoomReverb()
    
    # 使用预设
    reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
    
    # 或设置自定义参数
    reverb.set_params(
        room_width=5.0,      # 房间宽度（米）
        room_height=3.0,     # 房间高度（米）
        room_depth=4.0,      # 房间深度（米）
        wall_absorption=0.5, # 墙壁吸收系数（0-1）
        reverb_time=0.8      # 混响时间（秒）
    )
    
    # 处理音频
    output = reverb.process(audio)
```

### C++ - 直接使用

```cpp
#include "c_interface.h"

// 初始化
steam_audio_init(44100, 256);

// 创建处理器
void* processor = audio_processor_create(1, 256);

// 设置空间化参数
SpatializationParams params;
params.listener_pos = {0, 0, 0};
params.sound_pos = {5, 0, 0};
params.min_distance = 0.1f;
params.max_distance = 1000.0f;

// 处理音频
float input[256];
float output[512];  // 立体声输出
int output_frames;

audio_processor_process(
    processor,
    input, 256,
    output, &output_frames,
    &params
);

// 清理
audio_processor_destroy(processor);
steam_audio_shutdown();
```

## 🎮 交互式演示

演示应用提供了一个可视化的3D音频环境：

### 控制方式
- **方向键** - 移动听者位置
- **空格键** - 启用/禁用房间混响
- **F3** - 打开混响预设菜单

## 📚 API文档

### 核心类

#### Context
全局Steam Audio上下文管理器，必须在使用其他功能前初始化。

```python
with steamaudio.Context(sample_rate=44100, frame_size=256):
    # 使用Steam Audio功能
    pass
```

#### Vector3
3D向量类，支持数学运算。

```python
v1 = steamaudio.Vector3(1, 2, 3)
v2 = steamaudio.Vector3(4, 5, 6)
v3 = v1 + v2
distance = v1.distance_to(v2)
normalized = v1.normalize()
```

#### SpatializationParams
空间化参数，定义听者和声源的位置关系。

```python
params = steamaudio.SpatializationParams()
params.listener_pos = steamaudio.Vector3(0, 0, 0)
params.listener_forward = steamaudio.Vector3(0, 0, 1)
params.listener_up = steamaudio.Vector3(0, 1, 0)
params.sound_pos = steamaudio.Vector3(5, 0, 0)
params.min_distance = 0.1
params.max_distance = 1000.0
params.rolloff = 1.0
```

#### AudioProcessor
单源音频处理器。

```python
processor = steamaudio.AudioProcessor(input_channels=1)
output = processor.process(audio_data, params)
```

#### AudioMixer
多源音频混音器，支持最多256个并发音源。

```python
mixer = steamaudio.AudioMixer(max_sources=32)
mixer.add_source(source_id, input_channels=1)
output = mixer.process(sources_data, params_dict)
mixer.remove_source(source_id)
```

#### RoomReverb
房间混响效果处理器。

```python
reverb = steamaudio.RoomReverb()
reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
output = reverb.process(audio_data)
```

#### DirectEffect
直接效果（遮挡和传输）处理器。

```python
effect = steamaudio.DirectEffect()
effect.set_params(
    distance=5.0,
    occlusion=0.5,
    transmission_low=0.8,
    transmission_mid=0.6,
    transmission_high=0.4
)
output = effect.process(audio_data)
```

详细API文档请参阅 [python-steamaudio/API.md](python-steamaudio/API.md)

## 🏗️ 项目结构

```
SteamAudioDLL/
├── include/              # C++头文件
│   ├── audio_mixer.h
│   ├── audio_processor.h
│   ├── c_interface.h
│   ├── direct_effect.h
│   ├── phonon_wrapper.h
│   └── room_reverb.h
├── src/                  # C++源文件
│   ├── audio_mixer.cpp
│   ├── audio_processor.cpp
│   ├── c_interface.cpp
│   ├── direct_effect.cpp
│   ├── phonon_wrapper.cpp
│   └── room_reverb.cpp
├── python-steamaudio/    # Python包
│   ├── steamaudio/       # Python模块
│   │   ├── core/         # 核心功能
│   │   ├── effects/      # 音频效果
│   │   ├── processor/    # 音频处理器
│   │   ├── spatial/      # 空间音频
│   │   └── utils/        # 工具函数
│   ├── tests/            # 单元测试
│   ├── API.md            # API文档
│   ├── README.md         # Python包说明
│   └── setup.py          # 安装脚本
├── python/               # 演示应用
│   ├── interactive_3d.py # 交互式3D演示
│   ├── 1.ogg             # 音频文件1
│   ├── 2.ogg             # 脚步声
│   └── 3.ogg             # 音频文件2
├── steamaudio/           # Steam Audio SDK
│   ├── include/          # SDK头文件
│   ├── lib/              # SDK库文件
│   └── doc/              # SDK文档
├── build/                # 构建输出目录
├── CMakeLists.txt        # CMake配置
├── LICENSE               # 许可证
├── CHANGELOG.md          # 更新日志
├── CONTRIBUTING.md       # 贡献指南
└── README.md             # 本文件
```

## 🔧 高级配置

### 混响预设

库提供7种预设房间配置：

| 预设 | 房间尺寸 | 混响时间 | 适用场景 |
|------|----------|----------|----------|
| PRESET_SMALL_ROOM | 2×2×2m | 0.3s | 小房间、卧室 |
| PRESET_MEDIUM_ROOM | 5×4×3m | 0.5s | 客厅、办公室 |
| PRESET_LARGE_ROOM | 10×8×4m | 0.8s | 大厅、会议室 |
| PRESET_SMALL_HALL | 15×10×5m | 1.2s | 小礼堂 |
| PRESET_LARGE_HALL | 30×20×10m | 2.0s | 音乐厅 |
| PRESET_CATHEDRAL | 50×40×20m | 4.0s | 教堂、大教堂 |
| PRESET_OUTDOOR | - | 0.1s | 室外环境 |

### 性能优化

- **块大小**: 默认256样本（44.1kHz时为5.8ms），可根据延迟要求调整
- **音源数量**: 混音器支持最多256个音源，但建议根据CPU性能限制实际使用数量
- **HRTF**: 可通过 `Context.set_hrtf_enabled()` 启用/禁用以平衡质量和性能

## 🧪 测试

### 运行Python测试

```bash
cd python-steamaudio
pytest tests/ -v
```

### 测试覆盖率

```bash
pytest tests/ --cov=steamaudio --cov-report=html
```

## 📦 打包分发

### PyInstaller

```bash
pyinstaller --onefile your_script.py
```

### Nuitka

```bash
python -m nuitka \
    --onefile \
    --include-package=steamaudio \
    your_script.py
```

详细打包说明请参阅 [python-steamaudio/PACKAGING.md](python-steamaudio/PACKAGING.md)

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献流程

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m '[功能] 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用zlib许可证 - 详见 [LICENSE](LICENSE) 文件

### 重要声明

本项目使用了大量来自 [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev) 的代码。NVGT由Sam Tupy开发，采用zlib许可证。详细信息请参阅 [NVGT_LICENSE.md](NVGT_LICENSE.md)。

Steam Audio SDK由Valve Corporation提供，遵循其自身的许可条款。

## 🙏 致谢

- [NVGT (NonVisual Gaming Toolkit)](https://nvgt.dev) - 本项目使用了大量NVGT的代码，特别感谢Sam Tupy和NVGT项目
- [Steam Audio](https://valvesoftware.github.io/steam-audio/) - Valve Corporation提供的3D音频SDK
- 所有贡献者

## 📞 联系方式

- 问题反馈: [GitHub Issues](https://github.com/wangru2025/SteamAudioDLL/issues)
- 讨论: [GitHub Discussions](https://github.com/wangru2025/SteamAudioDLL/discussions)

---

**注意**: 本项目主要是对NVGT代码的封装和Python绑定，核心功能来自NVGT和Steam Audio。
