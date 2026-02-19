# 打包 Steam Audio 应用

本文档说明如何使用 PyInstaller 和 Nuitka 打包 Steam Audio 应用。

## PyInstaller

### 自动方式（推荐）

PyInstaller 会通过 hook 系统自动检测并包含 Steam Audio DLL 文件：

```bash
pyinstaller --onefile your_script.py
```

Hook 文件 `steamaudio/hooks/hook-steamaudio.py` 会被自动发现并使用。

### 手动配置

如果自动检测不工作，可以手动指定 DLL 文件：

```bash
pyinstaller --onefile \
    --add-data "path/to/steamaudio/bindings/dll:steamaudio/bindings/dll" \
    your_script.py
```

或在 spec 文件中配置：

```python
# your_script.spec
a = Analysis(
    ['your_script.py'],
    datas=[
        ('path/to/steamaudio/bindings/dll', 'steamaudio/bindings/dll'),
    ],
    ...
)
```

## Nuitka

### 使用 Nuitka 打包 Steam Audio

```bash
python -m nuitka \
    --onefile \
    --include-package=steamaudio \
    --include-data-dir=path/to/steamaudio/bindings/dll=steamaudio/bindings/dll \
    your_script.py
```

或创建构建脚本：

```python
# build.py
import subprocess
import sys
from pathlib import Path

steamaudio_dll_dir = Path("path/to/steamaudio/bindings/dll")

cmd = [
    sys.executable, "-m", "nuitka",
    "--onefile",
    "--include-package=steamaudio",
    f"--include-data-dir={steamaudio_dll_dir}=steamaudio/bindings/dll",
    "your_script.py",
]

subprocess.run(cmd)
```

## 验证 DLL 包含

打包后，验证 DLL 文件是否被包含：

### PyInstaller
```bash
# 检查 dist 文件夹
ls dist/your_script/steamaudio/bindings/dll/
```

### Nuitka
```bash
# 检查输出目录
ls your_script.dist/steamaudio/bindings/dll/
```

## 故障排除

### 运行时找不到 DLL

如果出现"找不到 Steam Audio 库"错误：

1. 验证 DLL 在打包应用中的位置是否正确
2. 检查 DLL 目录结构是否匹配：`steamaudio/bindings/dll/`
3. 确保所有依赖项（phonon.dll、libstdc++-6.dll 等）都被包含

### 缺少依赖项

Steam Audio 需要以下依赖项：
- `phonon.dll` - Steam Audio 主库
- `libstdc++-6.dll` - C++ 运行时
- `libgcc_s_seh-1.dll` - GCC 运行时
- `libwinpthread-1.dll` - Windows POSIX 线程

使用 hook 时，这些都会自动包含。

## 示例应用

```python
# example.py
import steamaudio
import numpy as np

with steamaudio.Context(sample_rate=44100, frame_size=256):
    processor = steamaudio.AudioProcessor(input_channels=1)
    
    # 创建测试音频
    audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
    
    # 创建参数
    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)
    params.sound_pos = steamaudio.Vector3(5, 0, 0)
    
    # 处理
    output = processor.process(audio, params)
    print(f"处理后的音频形状: {output.shape}")
```

打包方式：
```bash
pyinstaller --onefile example.py
```

生成的可执行文件将包含所有必要的 Steam Audio DLL。
