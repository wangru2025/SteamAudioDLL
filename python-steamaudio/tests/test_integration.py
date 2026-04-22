"""Integration tests for Steam Audio library."""

import pytest
import numpy as np
import steamaudio
from unittest.mock import patch, MagicMock


class TestContextIntegration:
    """Integration tests for Context."""
    
    def test_context_initialization_and_shutdown(self):
        """Test context initialization and shutdown."""
        assert not steamaudio.Context.is_initialized()
        
        with patch('steamaudio.bindings.loader.get_library') as mock_get_lib:
            mock_lib = MagicMock()
            mock_lib.steam_audio_init.return_value = None
            mock_lib.steam_audio_shutdown.return_value = None
            mock_get_lib.return_value = mock_lib
            
            with steamaudio.Context(sample_rate=44100, frame_size=256):
                assert steamaudio.Context.is_initialized()
                mock_lib.steam_audio_init.assert_called_once_with(44100, 256)
            
            assert not steamaudio.Context.is_initialized()
            mock_lib.steam_audio_shutdown.assert_called_once()
    
    def test_context_get_version(self):
        """Test getting version."""
        with patch('steamaudio.bindings.loader.get_library') as mock_get_lib:
            mock_lib = MagicMock()
            mock_lib.steam_audio_get_version.return_value = b"1.0.0"
            mock_get_lib.return_value = mock_lib
            
            version = steamaudio.Context.get_version()
            assert version == "1.0.0"
    
    def test_context_hrtf_control(self):
        """Test HRTF control."""
        with patch('steamaudio.bindings.loader.get_library') as mock_get_lib:
            mock_lib = MagicMock()
            mock_lib.steam_audio_init.return_value = None
            mock_lib.steam_audio_shutdown.return_value = None
            mock_lib.steam_audio_set_hrtf_enabled.return_value = None
            mock_lib.steam_audio_get_hrtf_enabled.return_value = 1
            mock_get_lib.return_value = mock_lib
            
            with steamaudio.Context():
                steamaudio.Context.set_hrtf_enabled(True)
                mock_lib.steam_audio_set_hrtf_enabled.assert_called_with(1)
                
                enabled = steamaudio.Context.get_hrtf_enabled()
                assert enabled is True


class TestProcessorIntegration:
    """Integration tests for AudioProcessor."""
    
    def test_processor_full_workflow(self):
        """Test full processor workflow."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # Create test audio
                audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
                
                # Create parameters
                params = steamaudio.SpatializationParams()
                params.listener_pos = steamaudio.Vector3(0, 0, 0)
                params.sound_pos = steamaudio.Vector3(5, 0, 0)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents.value = frames
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                output = processor.process(audio, params)
                
                assert output.shape == (44100, 2)
                assert output.dtype == np.float32


class TestMixerIntegration:
    """Integration tests for AudioMixer."""
    
    def test_mixer_full_workflow(self):
        """Test full mixer workflow."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                # Add sources
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=1)
                
                # Create test audio
                audio1 = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
                audio2 = np.sin(2 * np.pi * 880 * np.arange(44100) / 44100).astype(np.float32)
                
                # Create parameters
                params1 = steamaudio.SpatializationParams()
                params1.listener_pos = steamaudio.Vector3(0, 0, 0)
                params1.sound_pos = steamaudio.Vector3(5, 0, 0)
                
                params2 = steamaudio.SpatializationParams()
                params2.listener_pos = steamaudio.Vector3(0, 0, 0)
                params2.sound_pos = steamaudio.Vector3(-5, 0, 0)
                
                sources_data = {0: audio1, 1: audio2}
                params_dict = {0: params1, 1: params2}
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 44100
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params_dict)
                
                assert output.shape == (44100, 2)
                assert output.dtype == np.float32


class TestEffectsIntegration:
    """Integration tests for effects."""
    
    def test_reverb_full_workflow(self):
        """Test full reverb workflow."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_set_preset.return_value = None
            mock_lib.room_reverb_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                reverb = steamaudio.RoomReverb()
                
                # Set preset
                reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
                
                # Create test audio
                audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = frames
                    return None
                
                mock_lib.room_reverb_process.side_effect = mock_process
                
                output = reverb.process(audio)
                
                assert output.shape == (44100,)
                assert output.dtype == np.float32
    
    def test_direct_effect_full_workflow(self):
        """Test full direct effect workflow."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            mock_lib.direct_effect_set_params.return_value = None
            mock_lib.direct_effect_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                effect = steamaudio.DirectEffect()
                
                # Set parameters
                effect.set_params(
                    distance=5.0,
                    occlusion=0.5,
                    transmission_low=0.8,
                    transmission_mid=0.6,
                    transmission_high=0.4
                )
                
                # Create test audio
                audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = frames
                    return None
                
                mock_lib.direct_effect_process.side_effect = mock_process
                
                output = effect.process(audio)
                
                assert output.shape == (44100,)
                assert output.dtype == np.float32


class TestComplexWorkflow:
    """Integration tests for complex workflows."""
    
    def test_processor_with_moving_source(self):
        """Test processor with moving sound source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # Create test audio
                audio = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents.value = frames
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                # Process with moving source
                for i in range(10):
                    params = steamaudio.SpatializationParams()
                    params.listener_pos = steamaudio.Vector3(0, 0, 0)
                    params.sound_pos = steamaudio.Vector3(i, 0, 0)
                    
                    output = processor.process(audio, params)
                    assert output.shape == (1024, 2)
    
    def test_mixer_with_dynamic_sources(self):
        """Test mixer with dynamic source addition/removal."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_remove_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                # Add and process
                mixer.add_source(0, input_channels=1)
                audio1 = np.random.randn(1024).astype(np.float32)
                params1 = steamaudio.SpatializationParams()
                
                output = mixer.process({0: audio1}, {0: params1})
                assert output.shape == (1024, 2)
                
                # Add another source
                mixer.add_source(1, input_channels=1)
                audio2 = np.random.randn(1024).astype(np.float32)
                params2 = steamaudio.SpatializationParams()
                
                output = mixer.process({0: audio1, 1: audio2}, {0: params1, 1: params2})
                assert output.shape == (1024, 2)
                
                # Remove first source
                mixer.remove_source(0)
                output = mixer.process({1: audio2}, {1: params2})
                assert output.shape == (1024, 2)
    
    def test_effect_chain(self):
        """Test chaining multiple effects."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.direct_effect_create.return_value = 3000000
            mock_lib.direct_effect_set_params.return_value = None
            mock_lib.direct_effect_process.return_value = None
            mock_lib.room_reverb_create.return_value = 2000000
            mock_lib.room_reverb_set_preset.return_value = None
            mock_lib.room_reverb_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                # Create effects
                direct = steamaudio.DirectEffect()
                reverb = steamaudio.RoomReverb()
                
                # Set parameters
                direct.set_params(distance=5.0, occlusion=0.3)
                reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
                
                # Create test audio
                audio = np.sin(2 * np.pi * 440 * np.arange(44100) / 44100).astype(np.float32)
                
                def mock_direct_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = frames
                    return None
                
                def mock_reverb_process(handle, input_ptr, frames, output_ptr, output_frames):
                    output_frames.contents.value = frames
                    return None
                
                mock_lib.direct_effect_process.side_effect = mock_direct_process
                mock_lib.room_reverb_process.side_effect = mock_reverb_process
                
                # Apply effects in chain
                output1 = direct.process(audio)
                output2 = reverb.process(output1)
                
                assert output1.shape == (44100,)
                assert output2.shape == (44100,)
