# SteamAudioDLL贡献指南

感谢你对SteamAudioDLL的贡献兴趣！本文档提供了贡献指南和说明。

## 行为准则

- 保持尊重和包容
- 关注代码，而不是个人
- 帮助他人学习和成长
- 建设性地报告问题

## 快速开始

1. Fork本仓库
2. 克隆你的fork：`git clone https://github.com/wangru2025/SteamAudioDLL.git`
3. 创建功能分支：`git checkout -b feature/your-feature-name`
4. 进行修改
5. 充分测试
6. 提交清晰的提交信息
7. 推送到你的fork
8. 创建Pull Request

## 开发环境设置

### 前置条件
- CMake 3.20+
- MinGW编译器（g++）
- Python 3.8+（用于测试）
- Steam Audio SDK

### 开发编译

```bash
cd SteamAudioDLL
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .
```

### 运行测试

```bash
cd python
python interactive_3d.py
```

## 代码风格指南

### C++代码

- 使用C++17标准
- 遵循Google C++风格指南约定
- 使用有意义的变量名
- 为复杂逻辑添加注释
- 保持函数专注和简洁
- 适当使用`const`和`constexpr`

示例：
```cpp
// 好的
bool process_audio_chunk(
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int& output_frame_count) {
    
    if (!input_data || !output_data) {
        return false;
    }
    
    // 处理...
    return true;
}
```

### Python代码

- 遵循PEP 8风格指南
- 尽可能使用类型提示
- 为函数添加文档字符串
- 保持行长度在100字符以内

示例：
```python
def process_audio(
    audio_data: np.ndarray,
    sample_rate: int) -> np.ndarray:
    """
    使用空间效果处理音频数据。
    
    参数：
        audio_data: 输入音频样本
        sample_rate: 采样率（Hz）
        
    返回：
        处理后的音频样本
    """
    # 实现...
    return processed_data
```

## 提交信息

使用清晰、描述性的提交信息：

```
[类别] 简要描述

更长的解释（如果需要）。解释改变了什么以及为什么。

- 多个更改的项目符号
- 保持简洁但信息丰富

修复 #123
```

类别：
- `[功能]` - 新功能
- `[修复]` - 错误修复
- `[文档]` - 文档更新
- `[重构]` - 代码重构
- `[测试]` - 测试添加/更新
- `[构建]` - 构建系统更改

## Pull Request流程

1. 如需要，更新文档
2. 为新功能添加测试
3. 确保所有测试通过
4. 更新CHANGELOG.md
5. 提供清晰的PR描述
6. 链接相关问题

### PR描述模板

```markdown
## 描述
简要描述更改

## 更改类型
- [ ] 错误修复
- [ ] 新功能
- [ ] 破坏性更改
- [ ] 文档更新

## 测试
描述你如何测试更改

## 检查清单
- [ ] 代码遵循风格指南
- [ ] 文档已更新
- [ ] 测试已添加/更新
- [ ] 没有新的警告
```

## 报告问题

### 错误报告

包括：
- 清晰的错误描述
- 重现步骤
- 预期行为
- 实际行为
- 系统信息（OS、编译器版本等）
- 错误信息或日志

### 功能请求

包括：
- 清晰的功能描述
- 用例和动机
- 可能的实现方法
- 任何相关示例

## 文档

- 为用户面向的更改更新README.md
- 为复杂逻辑添加代码注释
- 更新API文档
- 为新功能包含示例

## 测试

- 为新功能编写测试
- 确保现有测试通过
- 如可能，在多个平台上测试
- 在测试中包含边界情况

## 性能考虑

- 在更改前后进行性能分析
- 避免不必要的分配
- 使用高效的算法
- 记录性能影响

## 许可证

通过贡献，你同意你的贡献将在与项目相同的zlib许可证下获得许可。

## 问题？

- 检查现有问题和讨论
- 阅读文档
- 在新问题中提问，标记为`[问题]`

## 致谢

贡献者将在以下位置被认可：
- CONTRIBUTORS.md文件
- 发布说明
- 项目文档

感谢为SteamAudioDLL做出贡献！
