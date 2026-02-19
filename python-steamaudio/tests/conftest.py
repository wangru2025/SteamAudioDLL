"""Pytest configuration and fixtures."""

import pytest
import numpy as np
import steamaudio


@pytest.fixture
def sample_audio_mono():
    """Generate sample mono audio."""
    return np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)


@pytest.fixture
def sample_audio_stereo():
    """Generate sample stereo audio."""
    mono = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
    return np.stack([mono, mono], axis=1).astype(np.float32)


@pytest.fixture
def sample_audio_chunk():
    """Generate sample audio chunk."""
    return np.random.randn(1024).astype(np.float32)


@pytest.fixture
def spatialization_params():
    """Create sample spatialization parameters."""
    params = steamaudio.SpatializationParams()
    params.listener_pos = steamaudio.Vector3(0, 0, 0)
    params.listener_forward = steamaudio.Vector3(0, 0, 1)
    params.listener_up = steamaudio.Vector3(0, 1, 0)
    params.sound_pos = steamaudio.Vector3(5, 0, 0)
    return params


@pytest.fixture
def vector3_origin():
    """Create origin vector."""
    return steamaudio.Vector3(0, 0, 0)


@pytest.fixture
def vector3_unit_x():
    """Create unit X vector."""
    return steamaudio.Vector3(1, 0, 0)


@pytest.fixture
def vector3_unit_y():
    """Create unit Y vector."""
    return steamaudio.Vector3(0, 1, 0)


@pytest.fixture
def vector3_unit_z():
    """Create unit Z vector."""
    return steamaudio.Vector3(0, 0, 1)
