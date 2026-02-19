# 更新日志

本项目的所有重要更改都将记录在此文件中。

格式基于[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-02-18

### 新增
- SteamAudioDLL初始版本发布
- 支持最多256个并发音源的多源音频混音器
- 基于HRTF的空间音频处理
- 包含7个预设配置的房间混响（小房间、中等房间、大房间、小厅、大厅、大教堂、室外）
- 使用Sabine公式计算RT60的参数化混响
- 频率相关吸收（低/中/高频段）
- 遮挡和传输效果的直接效果支持
- 使用平方反比律的距离衰减
- 跨语言兼容的C接口
- Python ctypes绑定
- 交互式3D音频演示应用（wxPython）
- 全局按键捕获的keyboard库集成
- 便携式DLL分发的静态运行时链接
- 完整的文档和示例

### 功能
- **AudioMixer**：管理多个并发音源，每个音源独立空间化
- **RoomReverb**：带预设房间配置的参数化混响
- **DirectEffect**：遮挡和传输效果处理
- **AudioProcessor**：向后兼容的单源处理器
- **PhononWrapper**：Steam Audio上下文和初始化管理

### 技术细节
- C++17实现
- MinGW编译器支持
- Steam Audio SDK集成
- 256样本块处理（44.1kHz时为5.8ms）
- 实时音频处理管道

### 文档
- README.md包含功能概述和使用示例
- 所有C接口函数的API文档
- 交互式演示及源代码
- 贡献指南
- 许可证和致谢文档

### 已知限制
- 仅限Windows（MinGW构建）
- 需要Steam Audio SDK
- 单线程音频处理（线程安全混音器）
- 固定块大小256个样本

## 未来版本计划

### 计划v1.1.0
- [ ] 基于几何的反射计算
- [ ] 实时房间参数调整UI
- [ ] Ambisonics支持
- [ ] 卷积混响选项
- [ ] 性能分析工具

### 计划v2.0.0
- [ ] 跨平台支持（Linux、macOS）
- [ ] MSVC编译器支持
- [ ] 麦克风阵列支持
- [ ] 高级空间音频格式
- [ ] GPU加速

---

更多信息，请参阅[README.md](README.md)和[CONTRIBUTING.md](CONTRIBUTING.md)。
