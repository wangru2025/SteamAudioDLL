"""Setup configuration for steamaudio package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="steamaudio",
    version="1.0.0",
    author="Steam Audio Contributors",
    description="Python bindings for Steam Audio - 3D audio spatialization library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wangru2025/SteamAudioDLL",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ],
        "audio": [
            "soundfile>=0.10.0",
            "pyaudio>=0.2.11",
        ],
    },
    include_package_data=True,
    package_data={
        "steamaudio": [
            "bindings/dll/*.dll",
            "bindings/dll/*.so",
            "bindings/dll/*.dylib",
        ],
    },
)
