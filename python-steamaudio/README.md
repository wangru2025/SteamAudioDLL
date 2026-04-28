# Steam Audio Python 包

`steamaudio` 是这个仓库提供的 Python 绑定包，用来在 Python 中访问项目封装好的音频能力。

## 当前提供

- 3D 空间化
- 多声源混音
- 房间混响
- 直达声效果
- 几何场景与材质
- 基于场景的直达声模拟
- 基于场景的反射效果

## 安装

在仓库内开发安装：

```powershell
python -m pip install -e .
```

## 快速开始

### 单源空间化

```python
import numpy as np
import steamaudio

with steamaudio.Context(sample_rate=44100, frame_size=256):
    processor = steamaudio.AudioProcessor(input_channels=1)

    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)
    params.sound_pos = steamaudio.Vector3(5, 0, 0)

    audio = np.random.randn(1024).astype(np.float32)
    output = processor.process(audio, params)
```

### 多源混音

```python
with steamaudio.Context():
    mixer = steamaudio.AudioMixer(max_sources=8)
    mixer.add_source(0, input_channels=1)
    mixer.add_source(1, input_channels=1)

    output = mixer.process(
        {0: audio_1, 1: audio_2},
        {0: params_1, 1: params_2},
    )
```

### 房间混响

```python
with steamaudio.Context():
    reverb = steamaudio.RoomReverb()
    reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
    output = reverb.process(audio)
```

### 几何场景

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

### 直达声模拟

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
```

### AudioEnvironment 高层封装

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
    env.add_room(10.0, 3.0, 8.0, wall_material="plaster")
    env.add_wall_with_doorway("x", 0.0, -4.0, 4.0, 3.0, material="brick")
    env.commit_geometry()

    env.add_source(0, steamaudio.SourceConfig(position=steamaudio.Vector3(-2, 0, 0)))
    env.add_source(1, steamaudio.SourceConfig(position=steamaudio.Vector3(2, 0, 0)))
    env.update_sources(
        {
            0: {"min_distance": 0.5},
            1: {"occlusion_radius": 1.5, "num_occlusion_samples": 32},
        }
    )
    env.set_listener(steamaudio.Vector3(0, 0, 0))
    env.settings.indirect.num_rays = 1024
    env.settings.indirect.num_bounces = 16
    env.settings.indirect.duration = 1.5

    output = env.process({0: audio_1, 1: audio_2})
```

## 主要对象

- `Context`
- `Vector3`
- `SpatializationParams`
- `AudioProcessor`
- `AudioMixer`
- `RoomReverb`
- `DirectEffect`
- `ReflectionEffect`
- `Material`
- `GeometryScene`
- `StaticMesh`
- `DirectSimulator`
- `AudioEnvironment`
- `SourceConfig`
- `GeometrySettings`
- `DirectSoundSettings`
- `IndirectSoundSettings`
- `EnvironmentSettings`

## 材质预设

支持的材质预设：

- `generic`
- `brick`
- `concrete`
- `ceramic`
- `gravel`
- `carpet`
- `glass`
- `plaster`
- `wood`
- `metal`
- `rock`

## API 文档

详细说明见 [`API.md`](API.md)。
