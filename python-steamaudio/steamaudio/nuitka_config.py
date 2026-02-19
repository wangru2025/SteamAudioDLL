"""Nuitka configuration for steamaudio.

This file helps Nuitka properly include Steam Audio DLL files.
"""

import os
from pathlib import Path

# Get the steamaudio package directory
steamaudio_dir = Path(__file__).parent

# DLL directory
dll_dir = steamaudio_dir / "bindings" / "dll"

# Collect DLL files for Nuitka
data_files = []
if dll_dir.exists():
    for file in dll_dir.glob("*.dll"):
        data_files.append((str(file), "steamaudio/bindings/dll/"))
    for file in dll_dir.glob("*.so"):
        data_files.append((str(file), "steamaudio/bindings/dll/"))
    for file in dll_dir.glob("*.dylib"):
        data_files.append((str(file), "steamaudio/bindings/dll/"))

# Nuitka options
nuitka_options = {
    "data_files": data_files,
    "include_packages": [
        "steamaudio",
        "steamaudio.core",
        "steamaudio.spatial",
        "steamaudio.processor",
        "steamaudio.effects",
        "steamaudio.bindings",
    ],
}
