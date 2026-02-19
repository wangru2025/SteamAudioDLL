"""PyInstaller hook for steamaudio.

This hook ensures that Steam Audio DLL files are included when using PyInstaller.
"""

from PyInstaller.utils.hooks import get_module_file_attribute
import os

# Get the steamaudio package directory
steamaudio_dir = os.path.dirname(get_module_file_attribute("steamaudio"))

# DLL directory
dll_dir = os.path.join(steamaudio_dir, "bindings", "dll")

# Collect DLL files
binaries = []
if os.path.exists(dll_dir):
    for file in os.listdir(dll_dir):
        if file.endswith(('.dll', '.so', '.dylib')):
            binaries.append((os.path.join(dll_dir, file), "steamaudio/bindings/dll"))

# Hidden imports
hiddenimports = [
    'steamaudio.core',
    'steamaudio.spatial',
    'steamaudio.processor',
    'steamaudio.effects',
    'steamaudio.bindings',
]
