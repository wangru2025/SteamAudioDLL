# Steam Audio Python API 文档

本文档描述当前 Python 绑定中可直接使用的主要对象。

## Context

全局上下文。其他对象必须在 `Context` 内使用。

```python
with steamaudio.Context(sample_rate=44100, frame_size=256):
    ...
```

### 方法

- `Context.is_initialized() -> bool`
- `Context.get_instance() -> Context | None`
- `Context.get_version() -> str`
- `Context.set_hrtf_enabled(enabled: bool) -> None`
- `Context.get_hrtf_enabled() -> bool`

## Vector3

3D 向量。

### 构造

```python
v = steamaudio.Vector3(x=1.0, y=2.0, z=3.0)
```

### 常用方法

- `distance_to(other)`
- `magnitude()`
- `length()`
- `normalize()`
- `dot(other)`
- `cross(other)`
- `to_tuple()`
- `from_tuple(t)`

## SpatializationParams

单声源空间化参数。

### 字段

- `listener_pos`
- `listener_forward`
- `listener_up`
- `sound_pos`
- `min_distance`
- `max_distance`
- `rolloff`
- `directional_attenuation`

## AudioProcessor

单声源空间化处理器。

### 构造

```python
processor = steamaudio.AudioProcessor(input_channels=1)
```

### 方法

- `process(audio_data, params) -> np.ndarray`

返回立体声输出，形状为 `(frames, 2)`。

## AudioMixer

多声源混音器。

### 构造

```python
mixer = steamaudio.AudioMixer(max_sources=32)
```

### 方法

- `add_source(source_id, input_channels=1)`
- `remove_source(source_id)`
- `get_source_count()`
- `process(sources_data, params) -> np.ndarray`

## RoomReverb

房间混响处理器。

### 构造

```python
reverb = steamaudio.RoomReverb()
```

### 预设

- `PRESET_SMALL_ROOM`
- `PRESET_MEDIUM_ROOM`
- `PRESET_LARGE_ROOM`
- `PRESET_SMALL_HALL`
- `PRESET_LARGE_HALL`
- `PRESET_CATHEDRAL`
- `PRESET_OUTDOOR`

### 方法

- `set_preset(preset)`
- `set_params(room_width, room_height, room_depth, wall_absorption, reverb_time)`
- `get_params() -> dict`
- `process(audio_data) -> np.ndarray`

## DirectEffect

直达声效果处理器。

### 构造

```python
effect = steamaudio.DirectEffect()
```

### 方法

- `set_params(distance, occlusion=0.0, transmission_low=1.0, transmission_mid=1.0, transmission_high=1.0)`
- `set_simulation_params(params)`
- `process(audio_data) -> np.ndarray`

## Material

几何材质参数。

### 构造

```python
material = steamaudio.Material(
    absorption_low=0.05,
    absorption_mid=0.07,
    absorption_high=0.08,
    scattering=0.05,
    transmission_low=0.015,
    transmission_mid=0.002,
    transmission_high=0.001,
)
```

### 工厂方法

- `Material.preset(name: str) -> Material`

支持的预设：

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

## GeometryScene

几何场景容器。

### 构造

```python
scene = steamaudio.GeometryScene()
```

### 方法

- `commit()`
- `add_static_mesh(vertices, triangles, material_indices, materials) -> StaticMesh`
- `add_box(min_corner, max_corner, material) -> StaticMesh`
- `add_room(width, height, depth, wall_material, floor_material=None, ceiling_material=None, center=Vector3(0.0, 0.0, 0.0)) -> StaticMesh`
- `add_wall_with_doorway(axis, offset, min_extent, max_extent, height, material, doorway_center=0.0, doorway_half_width=1.0, doorway_height=2.5) -> StaticMesh`

## StaticMesh

附着在 `GeometryScene` 上的静态网格。

### 方法

- `set_material(material_index, material)`

## DirectSimulator

基于场景的直达声模拟器。

### 构造

```python
simulator = steamaudio.DirectSimulator(scene, max_sources=16)
```

### 方法

- `add_source(source_id)`
- `remove_source(source_id)`
- `set_listener(position, ahead=..., up=...)`
- `set_source(source_id, position, ahead=..., up=..., min_distance=1.0, direct_flags=0, occlusion_type=..., occlusion_radius=1.0, num_occlusion_samples=16, num_transmission_rays=8)`
- `run_direct()`
- `get_direct_params(source_id)`

## SourceConfig

`AudioEnvironment` 使用的单声源配置对象。

### 字段

- `position`
- `ahead`
- `up`
- `min_distance`
- `direct_flags`
- `occlusion_type`
- `occlusion_radius`
- `num_occlusion_samples`
- `num_transmission_rays`
- `input_channels`

## AudioEnvironment

组合 `GeometryScene`、`DirectSimulator`、`DirectEffect` 和 `AudioMixer` 的高层封装。

### 构造

```python
env = steamaudio.AudioEnvironment(
    scene=None,
    max_sources=16,
    geometry_enabled=True,
    material_registry=None,
)
```

### 方法

- `set_geometry_enabled(enabled: bool) -> None`
- `set_listener(position, ahead=Vector3(0.0, 0.0, -1.0), up=Vector3(0.0, 1.0, 0.0)) -> None`
- `add_source(source_id, config: SourceConfig) -> None`
- `remove_source(source_id) -> None`
- `update_source(source_id, **changes) -> None`
- `update_sources(updates: dict[int, SourceConfig | dict]) -> None`
- `add_static_mesh(vertices, triangles, material_indices, materials) -> StaticMesh`
- `add_box(min_corner, max_corner, material) -> StaticMesh`
- `add_room(width, height, depth, wall_material, floor_material=None, ceiling_material=None, center=Vector3(0.0, 0.0, 0.0)) -> StaticMesh`
- `add_wall_with_doorway(axis, offset, min_extent, max_extent, height, material, doorway_center=0.0, doorway_half_width=1.0, doorway_height=2.5) -> StaticMesh`
- `commit_geometry() -> None`
- `get_last_direct_params(source_id)`
- `process(sources_data) -> np.ndarray`

## 常量

### DirectEffect flags

- `DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION`
- `DIRECT_EFFECT_APPLY_AIR_ABSORPTION`
- `DIRECT_EFFECT_APPLY_DIRECTIVITY`
- `DIRECT_EFFECT_APPLY_OCCLUSION`
- `DIRECT_EFFECT_APPLY_TRANSMISSION`

### 几何遮挡模式

- `SCENE_OCCLUSION_RAYCAST`
- `SCENE_OCCLUSION_VOLUMETRIC`

## 异常

- `SteamAudioError`
- `InitializationError`
- `AudioProcessingError`
- `InvalidParameterError`
- `ResourceError`
