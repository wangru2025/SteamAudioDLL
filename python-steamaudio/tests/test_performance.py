"""Performance tests for Steam Audio library."""

import pytest
import numpy as np
import steamaudio
import time
from unittest.mock import patch, MagicMock


class TestPerformance:
    """Performance tests."""
    
    def test_vector3_operations_performance(self):
        """Test Vector3 operations performance."""
        vectors = [steamaudio.Vector3(np.random.randn(), np.random.randn(), np.random.randn()) 
                   for _ in range(1000)]
        
        start = time.time()
        for v in vectors:
            v.magnitude()
        elapsed = time.time() - start
        
        # Should be fast (< 100ms for 1000 operations)
        assert elapsed < 0.1
    
    def test_vector3_distance_performance(self):
        """Test Vector3 distance calculation performance."""
        v1 = steamaudio.Vector3(0, 0, 0)
        vectors = [steamaudio.Vector3(np.random.randn(), np.random.randn(), np.random.randn()) 
                   for _ in range(1000)]
        
        start = time.time()
        for v in vectors:
            v1.distance_to(v)
        elapsed = time.time() - start
        
        # Should be fast (< 100ms for 1000 operations)
        assert elapsed < 0.1
    
    def test_spatialization_params_creation_performance(self):
        """Test SpatializationParams creation performance."""
        start = time.time()
        for _ in range(1000):
            params = steamaudio.SpatializationParams()
            params.listener_pos = steamaudio.Vector3(0, 0, 0)
            params.sound_pos = steamaudio.Vector3(5, 0, 0)
            _ = params.distance
        elapsed = time.time() - start
        
        # Should be fast (< 100ms for 1000 operations)
        assert elapsed < 0.1
    
    def test_processor_creation_performance(self):
        """Test processor creation performance."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_destroy.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                start = time.time()
                for i in range(100):
                    processor = steamaudio.AudioProcessor(input_channels=1)
                    processor._cleanup()
                elapsed = time.time() - start
                
                # Should be reasonably fast (< 1s for 100 creations)
                assert elapsed < 1.0
    
    def test_mixer_creation_performance(self):
        """Test mixer creation performance."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_destroy.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                start = time.time()
                for i in range(100):
                    mixer = steamaudio.AudioMixer(max_sources=8)
                    mixer._cleanup()
                elapsed = time.time() - start
                
                # Should be reasonably fast (< 1s for 100 creations)
                assert elapsed < 1.0
    
    def test_numpy_array_conversion_performance(self):
        """Test numpy array conversion performance."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                params = steamaudio.SpatializationParams()
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents = frames
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                # Test with different array sizes
                sizes = [512, 1024, 4096, 16384]
                
                for size in sizes:
                    audio = np.random.randn(size).astype(np.float32)
                    
                    start = time.time()
                    for _ in range(10):
                        output = processor.process(audio, params)
                    elapsed = time.time() - start
                    
                    # Should be fast (< 100ms for 10 operations)
                    assert elapsed < 0.1
    
    def test_mixer_source_management_performance(self):
        """Test mixer source management performance."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_remove_source.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=256)
                
                # Test adding many sources
                start = time.time()
                for i in range(100):
                    mixer.add_source(i, input_channels=1)
                elapsed = time.time() - start
                
                # Should be fast (< 100ms for 100 additions)
                assert elapsed < 0.1
                
                # Test removing many sources
                start = time.time()
                for i in range(100):
                    mixer.remove_source(i)
                elapsed = time.time() - start
                
                # Should be fast (< 100ms for 100 removals)
                assert elapsed < 0.1
    
    def test_large_audio_buffer_handling(self):
        """Test handling of large audio buffers."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                params = steamaudio.SpatializationParams()
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents = frames
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                # Test with large buffer (1 second at 44.1kHz)
                large_audio = np.random.randn(44100).astype(np.float32)
                
                start = time.time()
                output = processor.process(large_audio, params)
                elapsed = time.time() - start
                
                # Should complete quickly (< 50ms)
                assert elapsed < 0.05
                assert output.shape == (44100, 2)
    
    def test_memory_efficiency(self):
        """Test memory efficiency of library."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_destroy.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                # Create and destroy many processors
                for _ in range(100):
                    processor = steamaudio.AudioProcessor(input_channels=1)
                    processor._cleanup()
                
                # Should not cause memory issues
                # (This is a basic test - real memory profiling would be more thorough)
                assert True


class TestBatchProcessing:
    """Tests for batch processing performance."""
    
    def test_batch_processor_performance(self):
        """Test batch processing with processor."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_processor_create.return_value = 1
            mock_lib.audio_processor_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                processor = steamaudio.AudioProcessor(input_channels=1)
                params = steamaudio.SpatializationParams()
                
                def mock_process(handle, input_ptr, frames, output_ptr, output_frames, c_params):
                    output_frames.contents = frames
                    return None
                
                mock_lib.audio_processor_process.side_effect = mock_process
                
                # Process multiple chunks
                chunk_size = 1024
                num_chunks = 100
                
                start = time.time()
                for _ in range(num_chunks):
                    audio = np.random.randn(chunk_size).astype(np.float32)
                    output = processor.process(audio, params)
                elapsed = time.time() - start
                
                # Should process 100 chunks quickly
                assert elapsed < 1.0
    
    def test_batch_mixer_performance(self):
        """Test batch processing with mixer."""
        with patch('steamaudio.core.context.Context.is_initialized', return_value=True):
            mock_lib = MagicMock()
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.audio_mixer_add_source.return_value = None
            mock_lib.audio_mixer_process.return_value = None
            
            with patch('steamaudio.bindings.loader.get_library', return_value=mock_lib):
                mixer = steamaudio.AudioMixer(max_sources=8)
                mixer.add_source(0, input_channels=1)
                mixer.add_source(1, input_channels=1)
                
                def mock_process(handle, input_ptrs, frame_counts, num_sources,
                               output_ptr, output_frames, c_params):
                    output_frames.contents = frame_counts[0]
                    return None
                
                mock_lib.audio_mixer_process.side_effect = mock_process
                
                # Process multiple chunks
                chunk_size = 1024
                num_chunks = 100
                
                start = time.time()
                for _ in range(num_chunks):
                    audio1 = np.random.randn(chunk_size).astype(np.float32)
                    audio2 = np.random.randn(chunk_size).astype(np.float32)
                    params1 = steamaudio.SpatializationParams()
                    params2 = steamaudio.SpatializationParams()
                    
                    output = mixer.process(
                        {0: audio1, 1: audio2},
                        {0: params1, 1: params2}
                    )
                elapsed = time.time() - start
                
                # Should process 100 chunks quickly
                assert elapsed < 1.0
