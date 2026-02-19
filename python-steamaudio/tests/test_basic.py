"""Basic functionality tests."""

import pytest
import numpy as np
import steamaudio


class TestVector3:
    """Test Vector3 class."""
    
    def test_creation(self):
        """Test Vector3 creation."""
        v = steamaudio.Vector3(1, 2, 3)
        assert v.x == 1
        assert v.y == 2
        assert v.z == 3
    
    def test_default_values(self):
        """Test Vector3 default values."""
        v = steamaudio.Vector3()
        assert v.x == 0
        assert v.y == 0
        assert v.z == 0
    
    def test_addition(self):
        """Test vector addition."""
        v1 = steamaudio.Vector3(1, 2, 3)
        v2 = steamaudio.Vector3(4, 5, 6)
        v3 = v1 + v2
        assert v3.x == 5
        assert v3.y == 7
        assert v3.z == 9
    
    def test_subtraction(self):
        """Test vector subtraction."""
        v1 = steamaudio.Vector3(5, 7, 9)
        v2 = steamaudio.Vector3(1, 2, 3)
        v3 = v1 - v2
        assert v3.x == 4
        assert v3.y == 5
        assert v3.z == 6
    
    def test_scalar_multiplication(self):
        """Test scalar multiplication."""
        v = steamaudio.Vector3(1, 2, 3)
        v2 = v * 2
        assert v2.x == 2
        assert v2.y == 4
        assert v2.z == 6
    
    def test_magnitude(self):
        """Test vector magnitude."""
        v = steamaudio.Vector3(3, 4, 0)
        assert v.magnitude() == 5.0
    
    def test_distance(self):
        """Test distance calculation."""
        v1 = steamaudio.Vector3(0, 0, 0)
        v2 = steamaudio.Vector3(3, 4, 0)
        assert v1.distance_to(v2) == 5.0
    
    def test_normalize(self):
        """Test vector normalization."""
        v = steamaudio.Vector3(3, 4, 0)
        v_norm = v.normalize()
        assert abs(v_norm.magnitude() - 1.0) < 1e-6
    
    def test_dot_product(self):
        """Test dot product."""
        v1 = steamaudio.Vector3(1, 0, 0)
        v2 = steamaudio.Vector3(0, 1, 0)
        assert v1.dot(v2) == 0.0
    
    def test_cross_product(self):
        """Test cross product."""
        v1 = steamaudio.Vector3(1, 0, 0)
        v2 = steamaudio.Vector3(0, 1, 0)
        v3 = v1.cross(v2)
        assert v3.x == 0
        assert v3.y == 0
        assert v3.z == 1


class TestSpatializationParams:
    """Test SpatializationParams class."""
    
    def test_creation(self):
        """Test SpatializationParams creation."""
        params = steamaudio.SpatializationParams()
        assert params.listener_pos is not None
        assert params.sound_pos is not None
    
    def test_distance_property(self):
        """Test distance property."""
        params = steamaudio.SpatializationParams()
        params.listener_pos = steamaudio.Vector3(0, 0, 0)
        params.sound_pos = steamaudio.Vector3(3, 4, 0)
        assert params.distance == 5.0
    
    def test_direction_property(self):
        """Test direction property."""
        params = steamaudio.SpatializationParams()
        params.listener_pos = steamaudio.Vector3(0, 0, 0)
        params.sound_pos = steamaudio.Vector3(1, 0, 0)
        direction = params.direction
        assert abs(direction.x - 1.0) < 1e-6
        assert abs(direction.y) < 1e-6
        assert abs(direction.z) < 1e-6
    
    def test_to_dict(self):
        """Test to_dict method."""
        params = steamaudio.SpatializationParams()
        d = params.to_dict()
        assert 'listener_pos' in d
        assert 'sound_pos' in d
        assert 'distance' in d


class TestExceptions:
    """Test exception classes."""
    
    def test_steam_audio_error(self):
        """Test SteamAudioError."""
        with pytest.raises(steamaudio.SteamAudioError):
            raise steamaudio.SteamAudioError("Test error")
    
    def test_initialization_error(self):
        """Test InitializationError."""
        with pytest.raises(steamaudio.InitializationError):
            raise steamaudio.InitializationError("Init failed")
    
    def test_audio_processing_error(self):
        """Test AudioProcessingError."""
        with pytest.raises(steamaudio.AudioProcessingError):
            raise steamaudio.AudioProcessingError("Processing failed")


class TestContext:
    """Test Context class."""
    
    def test_context_not_initialized_by_default(self):
        """Test that context is not initialized by default."""
        assert not steamaudio.Context.is_initialized()
    
    def test_invalid_sample_rate(self):
        """Test invalid sample rate."""
        with pytest.raises(ValueError):
            steamaudio.Context(sample_rate=-1)
    
    def test_invalid_frame_size(self):
        """Test invalid frame size."""
        with pytest.raises(ValueError):
            steamaudio.Context(frame_size=0)
