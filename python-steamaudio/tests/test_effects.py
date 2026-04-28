"""Tests for audio effects."""

import pytest
import numpy as np
import steamaudio
from unittest.mock import Mock, patch, MagicMock
import ctypes


class TestRoomReverb:
    """Test RoomReverb class."""
    
    def test_reverb_creation_without_context(self):
        """Test that reverb creation fails without context."""
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.RoomReverb()
    
    def test_reverb_with_context_manager(self):
        """Test reverb as context manager."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                with steamaudio.RoomReverb() as reverb:
                    assert reverb is not None
                
                # Verify destroy was called
                mock_lib.room_reverb_destroy.assert_called_once()
    
    def test_set_preset_small_room(self):
        """Test setting small room preset."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_set_preset.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                reverb.set_preset(steamaudio.RoomReverb.PRESET_SMALL_ROOM)
                
                mock_lib.room_reverb_set_preset.assert_called_once_with(
                    2000000, steamaudio.RoomReverb.PRESET_SMALL_ROOM
                )
    
    def test_set_preset_cathedral(self):
        """Test setting cathedral preset."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_set_preset.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                reverb.set_preset(steamaudio.RoomReverb.PRESET_CATHEDRAL)
                
                mock_lib.room_reverb_set_preset.assert_called_once()
    
    def test_set_invalid_preset(self):
        """Test setting invalid preset."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.set_preset(99)
    
    def test_set_params_valid(self):
        """Test setting valid parameters."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_set_params.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                reverb.set_params(
                    room_width=5.0,
                    room_height=3.0,
                    room_depth=4.0,
                    wall_absorption=0.5,
                    reverb_time=0.8
                )
                
                mock_lib.room_reverb_set_params.assert_called_once()
    
    def test_set_params_invalid_width(self):
        """Test setting invalid room width."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.set_params(
                        room_width=0.05,  # Too small
                        room_height=3.0,
                        room_depth=4.0,
                        wall_absorption=0.5,
                        reverb_time=0.8
                    )
    
    def test_set_params_invalid_absorption(self):
        """Test setting invalid absorption."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.set_params(
                        room_width=5.0,
                        room_height=3.0,
                        room_depth=4.0,
                        wall_absorption=1.5,  # Out of range
                        reverb_time=0.8
                    )
    
    def test_set_params_invalid_reverb_time(self):
        """Test setting invalid reverb time."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.set_params(
                        room_width=5.0,
                        room_height=3.0,
                        room_depth=4.0,
                        wall_absorption=0.5,
                        reverb_time=15.0  # Too large
                    )
    
    def test_get_params(self):
        """Test getting parameters."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            def mock_get_params(handle, w, h, d, a, t):
                w.contents.value = 5.0
                h.contents.value = 3.0
                d.contents.value = 4.0
                a.contents.value = 0.5
                t.contents.value = 0.8
                return None
            
            mock_lib.room_reverb_get_params.side_effect = mock_get_params
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                params = reverb.get_params()
                
                assert params['room_width'] == 5.0
                assert params['room_height'] == 3.0
                assert params['room_depth'] == 4.0
                assert params['wall_absorption'] == 0.5
                assert params['reverb_time'] == pytest.approx(0.8)
    
    def test_process_audio(self):
        """Test processing audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                audio = np.random.randn(1024).astype(np.float32)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.room_reverb_process.side_effect = mock_process
                
                output = reverb.process(audio)
                
                assert output.shape == (1024,)
                assert output.dtype == np.float32
    
    def test_process_invalid_shape(self):
        """Test processing with invalid shape."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                # 2D array should fail
                audio = np.random.randn(1024, 2).astype(np.float32)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.process(audio)
    
    def test_process_empty_audio(self):
        """Test processing empty audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                audio = np.array([], dtype=np.float32)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    reverb.process(audio)


class TestDirectEffect:
    """Test DirectEffect class."""
    
    def test_effect_creation_without_context(self):
        """Test that effect creation fails without context."""
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.DirectEffect()
    
    def test_effect_with_context_manager(self):
        """Test effect as context manager."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                with steamaudio.DirectEffect() as effect:
                    assert effect is not None
                
                # Verify destroy was called
                mock_lib.direct_effect_destroy.assert_called_once()
    
    def test_set_params_valid(self):
        """Test setting valid parameters."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            mock_lib.direct_effect_set_params.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                effect.set_params(
                    distance=5.0,
                    occlusion=0.5,
                    transmission_low=0.8,
                    transmission_mid=0.6,
                    transmission_high=0.4
                )
                
                mock_lib.direct_effect_set_params.assert_called_once()
    
    def test_set_params_invalid_distance(self):
        """Test setting invalid distance."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    effect.set_params(
                        distance=0.05,  # Too small
                        occlusion=0.5
                    )
    
    def test_set_params_invalid_occlusion(self):
        """Test setting invalid occlusion."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    effect.set_params(
                        distance=5.0,
                        occlusion=1.5  # Out of range
                    )
    
    def test_set_params_invalid_transmission(self):
        """Test setting invalid transmission."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    effect.set_params(
                        distance=5.0,
                        transmission_low=-0.1  # Out of range
                    )
    
    def test_process_audio(self):
        """Test processing audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            mock_lib.direct_effect_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                audio = np.random.randn(1024).astype(np.float32)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.direct_effect_process.side_effect = mock_process
                
                output = effect.process(audio)
                
                assert output.shape == (1024,)
                assert output.dtype == np.float32
    
    def test_process_invalid_shape(self):
        """Test processing with invalid shape."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                # 2D array should fail
                audio = np.random.randn(1024, 2).astype(np.float32)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    effect.process(audio)
    
    def test_process_empty_audio(self):
        """Test processing empty audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                audio = np.array([], dtype=np.float32)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    effect.process(audio)
    
    def test_process_list_input(self):
        """Test processing with list input."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            mock_lib.direct_effect_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                audio = [0.1, 0.2, 0.3, 0.4]
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = 4
                    return None
                
                mock_lib.direct_effect_process.side_effect = mock_process
                
                output = effect.process(audio)
                
                assert output.shape == (4,)
                assert output.dtype == np.float32


class TestReflectionEffect:
    """Test ReflectionEffect class."""

    def test_effect_creation_without_context(self):
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.ReflectionEffect()

    def test_effect_creation(self):
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.ReflectionEffect(max_order=1, max_duration=1.5)
                assert effect is not None

    def test_set_listener_and_simulation_output(self):
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.ReflectionEffect()
                simulator = MagicMock()
                simulator._handle = 4000000

                effect.set_listener(steamaudio.Vector3(0, 0, 0))
                effect.set_simulation_output(simulator, 3)

                mock_lib.reflection_effect_set_listener.assert_called_once()
                mock_lib.reflection_effect_set_simulation_output.assert_called_once_with(
                    7000000,
                    4000000,
                    3,
                )

    def test_process_audio(self):
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.reflection_effect_create.return_value = 7000000

            def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                output_frames.contents.value = frames
                return None

            mock_lib.reflection_effect_process.side_effect = mock_process

            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.ReflectionEffect()
                audio = np.random.randn(128).astype(np.float32)
                output = effect.process(audio)

                assert output.shape == (128, 2)
                assert output.dtype == np.float32
