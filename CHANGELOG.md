# 更新日志

本项目的重要变更记录在此。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，版本遵循语义化版本。

## [1.1.0] - 2026-04-28

### 新增

- 增加几何场景与材质相关的 C 接口
- 增加 `GeometryScene`、`StaticMesh`、`Material` Python API
- 增加 `DirectSimulator` Python API
- 增加 `AudioEnvironment` 的高层几何 helper，包括房间、箱体、门洞墙和统一提交入口
- 增加 `AudioEnvironment.update_sources(...)` 批量声源更新接口
- 增加基于场景的直达声模拟示例
- 演示应用加入几何场景、隔墙、门洞与实时几何设置

### 改进

- 构建后自动同步运行 Python 所需的 DLL 到 `python-steamaudio/steamaudio/bindings/dll/`
- 演示应用补充混响和几何的快捷键控制
- 演示应用和真实库测试改为优先使用 `AudioEnvironment` 高层几何接口，减少直接访问底层 `scene`
- 重写 README、Python 包 README 和 API 文档

## [1.0.0] - 2026-02-18

### 新增

- SteamAudioDLL 初始版本
- 单源空间化处理
- 多源音频混音
- 参数化房间混响
- 直达声效果处理
- C 接口封装
- Python ctypes 绑定
- 交互式 3D 音频演示
- 基础测试与文档
