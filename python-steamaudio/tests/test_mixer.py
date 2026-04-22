"""Tests for audio mixer."""

import pytest
import numpy as np
import steamaudio
from unittest.mock import Mock, patch, MagicMock


class TestAudioMixerAdvanced:
    """Advanced tests for AudioMixer class."""
    
    def test_mixer_full(self):
        """Test mixer when full."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=2)
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=1)
                
                # Try to add third source when full
                with pytest.raises(steamaudio.AudioProcessingError):
                    mixer.add_source(2, input_channels=1)
    
    def test_mixer_multiple_add_remove_cycles(self):
        """Test multiple add/remove cycles."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_remove_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                # Add and remove multiple times
                for i in range(3):
                    mixer.add_source(i, input_channels=1)
                    assert mixer.get_source_count() == 1
                    mixer.remove_source(i)
                    assert mixer.get_source_count() == 0
    
    def test_mixer_process_different_frame_counts(self):
        """Test processing sources with different frame counts."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=1)
                
                # Different frame counts
                audio1 = np.random.randn(512).astype(np.float32)
                audio2 = np.random.randn(1024).astype(np.float32)
                
                params1 = steamaudio.SpatializationParams()
                params2 = steamaudio.SpatializationParams()
                
                sources_data = {0: audio1, 1: audio2}
                params = {0: params1, 1: params2}
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    # Should use max frame count
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params)
                
                # Output should be max frame count
                assert output.shape == (1024, 2)
    
    def test_mixer_process_stereo_sources(self):
        """Test processing stereo sources."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=2)
                mixer.add_source(1, input_channels=2)
                
                # Stereo audio
                audio1 = np.random.randn(1024, 2).astype(np.float32)
                audio2 = np.random.randn(1024, 2).astype(np.float32)
                
                params1 = steamaudio.SpatializationParams()
                params2 = steamaudio.SpatializationParams()
                
                sources_data = {0: audio1, 1: audio2}
                params = {0: params1, 1: params2}
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params)
                
                assert output.shape == (1024, 2)
    
    def test_mixer_process_mixed_channels(self):
        """Test processing with mixed channel counts."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=2)
                
                audio1 = np.random.randn(1024).astype(np.float32)
                audio2 = np.random.randn(1024, 2).astype(np.float32)
                
                params1 = steamaudio.SpatializationParams()
                params2 = steamaudio.SpatializationParams()
                
                sources_data = {0: audio1, 1: audio2}
                params = {0: params1, 1: params2}
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params)
                
                assert output.shape == (1024, 2)
    
    def test_mixer_process_after_destroy(self):
        """Test processing after mixer is destroyed."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer._cleanup()
                
                audio = np.random.randn(1024).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                sources_data = {0: audio}
                params_dict = {0: params}
                
                with pytest.raises(steamaudio.AudioProcessingError):
                    mixer.process(sources_data, params_dict)
    
    def test_mixer_get_source_count(self):
        """Test getting source count."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_remove_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                assert mixer.get_source_count() == 0
                
                mixer.add_source(0, input_channels=1)
                assert mixer.get_source_count() == 1
                
                mixer.add_source(1, input_channels=1)
                assert mixer.get_source_count() == 2
                
                mixer.remove_source(0)
                assert mixer.get_source_count() == 1
    
    def test_mixer_process_with_list_input(self):
        """Test processing with list input."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                # List input
                audio = [0.1, 0.2, 0.3, 0.4]
                params = steamaudio.SpatializationParams()
                
                sources_data = {0: audio}
                params_dict = {0: params}
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 4
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params_dict)
                
                assert output.shape == (4, 2)
    
    def test_mixer_process_empty_frame_count(self):
        """Test processing with empty frame count."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                audio = np.array([], dtype=np.float32)
                params = steamaudio.SpatializationParams()
                
                sources_data = {0: audio}
                params_dict = {0: params}
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.process(sources_data, params_dict)
    
    def test_mixer_process_invalid_audio_shape(self):
        """Test processing with invalid audio shape."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                # 3D array
                audio = np.random.randn(1024, 2, 2).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                sources_data = {0: audio}
                params_dict = {0: params}
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.process(sources_data, params_dict)
    
    def test_mixer_large_number_of_sources(self):
        """Test mixer with large number of sources."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=256)
                
                # Add many sources
                for i in range(100):
                    mixer.add_source(i, input_channels=1)
                
                assert mixer.get_source_count() == 100
                
                # Process with many sources
                sources_data = {}
                params_dict = {}
                
                for i in range(100):
                    sources_data[i] = np.random.randn(512).astype(np.float32)
                    params_dict[i] = steamaudio.SpatializationParams()
                
                def mock_process(handle, source_ids, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents.value = 512
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                output = mixer.process(sources_data, params_dict)
                
                assert output.shape == (512, 2)
