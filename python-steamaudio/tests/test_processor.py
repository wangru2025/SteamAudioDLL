"""Tests for audio processor."""

import pytest
import numpy as np
import steamaudio
from unittest.mock import Mock, patch, MagicMock


class TestAudioProcessor:
    """Test AudioProcessor class."""
    
    def test_processor_creation_without_context(self):
        """Test that processor creation fails without context."""
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.AudioProcessor(input_channels=1)
    
    def test_invalid_input_channels(self):
        """Test invalid input channels."""
        with pytest.raises(steamaudio.InvalidParameterError):
            steamaudio.AudioProcessor(input_channels=3)
    
    def test_invalid_input_channels_zero(self):
        """Test zero input channels."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            with patch('steamaudio.bindings.loader.get_library'):
                with pytest.raises(steamaudio.InvalidParameterError):
                    steamaudio.AudioProcessor(input_channels=0)
    
    def test_processor_with_context_manager(self):
        """Test processor as context manager."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                with steamaudio.AudioProcessor(input_channels=1) as processor:
                    assert processor is not None
                
                # Verify destroy was called
                mock_lib.audio_processor_destroy.assert_called_once()
    
    def test_process_mono_audio(self):
        """Test processing mono audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # Create test audio
                audio = np.random.randn(1024).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                # Mock the process call to set output_frame_count
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                output = processor.process(audio, params)
                
                # Verify output shape
                assert output.shape == (1024, 2)
                assert output.dtype == np.float32
    
    def test_process_stereo_audio(self):
        """Test processing stereo audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=2)
                
                # Create test audio (stereo)
                audio = np.random.randn(1024, 2).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents.value = 1024
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                output = processor.process(audio, params)
                
                assert output.shape == (1024, 2)
                assert output.dtype == np.float32
    
    def test_process_invalid_shape(self):
        """Test processing with invalid audio shape."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # 3D array should fail
                audio = np.random.randn(1024, 2, 2).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    processor.process(audio, params)
    
    def test_process_channel_mismatch(self):
        """Test processing with channel mismatch."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # 2-channel audio for 1-channel processor
                audio = np.random.randn(1024, 2).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    processor.process(audio, params)
    
    def test_process_empty_audio(self):
        """Test processing empty audio."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                audio = np.array([], dtype=np.float32)
                params = steamaudio.SpatializationParams()
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    processor.process(audio, params)
    
    def test_process_after_destroy(self):
        """Test processing after processor is destroyed."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                processor._cleanup()
                
                audio = np.random.randn(1024).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                with pytest.raises(steamaudio.AudioProcessingError):
                    processor.process(audio, params)
    
    def test_process_list_input(self):
        """Test processing with list input."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                
                # List input
                audio = [0.1, 0.2, 0.3, 0.4]
                params = steamaudio.SpatializationParams()
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents.value = 4
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                output = processor.process(audio, params)
                
                assert output.shape == (4, 2)
                assert output.dtype == np.float32


class TestAudioMixer:
    """Test AudioMixer class."""
    
    def test_mixer_creation_without_context(self):
        """Test that mixer creation fails without context."""
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.AudioMixer(max_sources=8)
    
    def test_invalid_max_sources(self):
        """Test invalid max_sources."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            with patch('steamaudio.bindings.loader.get_library'):
                with pytest.raises(steamaudio.InvalidParameterError):
                    steamaudio.AudioMixer(max_sources=0)
    
    def test_invalid_max_sources_too_large(self):
        """Test max_sources too large."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            with patch('steamaudio.bindings.loader.get_library'):
                with pytest.raises(steamaudio.InvalidParameterError):
                    steamaudio.AudioMixer(max_sources=257)
    
    def test_mixer_with_context_manager(self):
        """Test mixer as context manager."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                with steamaudio.AudioMixer(max_sources=8) as mixer:
                    assert mixer is not None
                
                # Verify destroy was called
                mock_lib.audio_mixer_destroy.assert_called_once()
    
    def test_add_source(self):
        """Test adding a source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                assert mixer.get_source_count() == 1
                mock_lib.audio_mixer_add_source.assert_called_once()
    
    def test_add_duplicate_source(self):
        """Test adding duplicate source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.add_source(0, input_channels=1)
    
    def test_add_source_invalid_channels(self):
        """Test adding source with invalid channels."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.add_source(0, input_channels=3)
    
    def test_remove_source(self):
        """Test removing a source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_remove_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer.remove_source(0)
                
                assert mixer.get_source_count() == 0
                mock_lib.audio_mixer_remove_source.assert_called_once()
    
    def test_remove_nonexistent_source(self):
        """Test removing nonexistent source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.remove_source(0)
    
    def test_process_multiple_sources(self):
        """Test processing multiple sources."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=1)
                
                audio1 = np.random.randn(1024).astype(np.float32)
                audio2 = np.random.randn(1024).astype(np.float32)
                
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
                assert output.dtype == np.float32
    
    def test_process_empty_sources(self):
        """Test processing with empty sources."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.process({}, {})
    
    def test_process_missing_source(self):
        """Test processing with missing source."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                audio = np.random.randn(1024).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                sources_data = {1: audio}  # Source 1 not added
                params_dict = {1: params}
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.process(sources_data, params_dict)
    
    def test_process_channel_mismatch(self):
        """Test processing with channel mismatch."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                
                # 2-channel audio for 1-channel source
                audio = np.random.randn(1024, 2).astype(np.float32)
                params = steamaudio.SpatializationParams()
                
                sources_data = {0: audio}
                params_dict = {0: params}
                
                with pytest.raises(steamaudio.InvalidParameterError):
                    mixer.process(sources_data, params_dict)
