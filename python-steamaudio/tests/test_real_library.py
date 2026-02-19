"""Tests using the real Steam Audio library."""

import pytest
import numpy as np
import steamaudio


class TestRealLibraryContext:
    """Test Context with real library."""
    
    def test_context_initialization(self):
        """Test context initialization with real library."""
        assert not steamaudio.Context.is_initialized()
        
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            assert steamaudio.Context.is_initialized()
        
        assert not steamaudio.Context.is_initialized()
    
    def test_context_get_version(self):
        """Test getting version from real library."""
        version = steamaudio.Context.get_version()
        assert version is not None
        assert len(version) > 0
    
    def test_context_hrtf_control(self):
        """Test HRTF control with real library."""
        with steamaudio.Context():
            steamaudio.Context.set_hrtf_enabled(True)
            assert steamaudio.Context.get_hrtf_enabled() is True
            
            steamaudio.Context.set_hrtf_enabled(False)
            assert steamaudio.Context.get_hrtf_enabled() is False


class TestRealLibraryProcessor:
    """Test AudioProcessor with real library."""
    
    def test_processor_creation(self):
        """Test processor creation with real library."""
        with steamaudio.Context():
            processor = steamaudio.AudioProcessor(input_channels=1)
            assert processor is not None
    
    def test_processor_mono_processing(self):
        """Test processing mono audio with real library."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            processor = steamaudio.AudioProcessor(input_channels=1)
            
            # Create test audio (440 Hz sine wave)
            audio = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
            
            params = steamaudio.SpatializationParams()
            params.listener_pos = steamaudio.Vector3(0, 0, 0)
            params.sound_pos = steamaudio.Vector3(5, 0, 0)
            
            output = processor.process(audio, params)
            
            assert output.shape == (1024, 2)
            assert output.dtype == np.float32
    
    def test_processor_stereo_processing(self):
        """Test processing stereo audio with real library."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            processor = steamaudio.AudioProcessor(input_channels=2)
            
            # Create stereo test audio
            mono = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
            audio = np.stack([mono, mono], axis=1).astype(np.float32)
            
            params = steamaudio.SpatializationParams()
            params.listener_pos = steamaudio.Vector3(0, 0, 0)
            params.sound_pos = steamaudio.Vector3(5, 0, 0)
            
            output = processor.process(audio, params)
            
            assert output.shape == (1024, 2)
            assert output.dtype == np.float32
    
    def test_processor_with_different_positions(self):
        """Test processor with different sound positions."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            processor = steamaudio.AudioProcessor(input_channels=1)
            audio = np.sin(2 * np.pi * 440 * np.arange(512) / 44100).astype(np.float32)
            
            # Test different positions
            positions = [
                steamaudio.Vector3(5, 0, 0),
                steamaudio.Vector3(-5, 0, 0),
                steamaudio.Vector3(0, 5, 0),
                steamaudio.Vector3(0, 0, 5),
            ]
            
            for pos in positions:
                params = steamaudio.SpatializationParams()
                params.listener_pos = steamaudio.Vector3(0, 0, 0)
                params.sound_pos = pos
                
                output = processor.process(audio, params)
                assert output.shape == (512, 2)


class TestRealLibraryMixer:
    """Test AudioMixer with real library."""
    
    def test_mixer_creation(self):
        """Test mixer creation with real library."""
        with steamaudio.Context():
            mixer = steamaudio.AudioMixer(max_sources=8)
            assert mixer is not None
    
    def test_mixer_add_remove_sources(self):
        """Test adding and removing sources."""
        with steamaudio.Context():
            mixer = steamaudio.AudioMixer(max_sources=8)
            
            mixer.add_source(0, input_channels=1)
            assert mixer.get_source_count() == 1
            
            mixer.add_source(1, input_channels=1)
            assert mixer.get_source_count() == 2
            
            mixer.remove_source(0)
            assert mixer.get_source_count() == 1
    
    def test_mixer_process_multiple_sources(self):
        """Test processing multiple sources."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            mixer = steamaudio.AudioMixer(max_sources=8)
            mixer.add_source(0, input_channels=1)
            mixer.add_source(1, input_channels=1)
            
            # Create test audio
            audio1 = np.sin(2 * np.pi * 440 * np.arange(512) / 44100).astype(np.float32)
            audio2 = np.sin(2 * np.pi * 880 * np.arange(512) / 44100).astype(np.float32)
            
            params1 = steamaudio.SpatializationParams()
            params1.listener_pos = steamaudio.Vector3(0, 0, 0)
            params1.sound_pos = steamaudio.Vector3(5, 0, 0)
            
            params2 = steamaudio.SpatializationParams()
            params2.listener_pos = steamaudio.Vector3(0, 0, 0)
            params2.sound_pos = steamaudio.Vector3(-5, 0, 0)
            
            sources_data = {0: audio1, 1: audio2}
            params_dict = {0: params1, 1: params2}
            
            output = mixer.process(sources_data, params_dict)
            
            assert output.shape == (512, 2)
            assert output.dtype == np.float32


class TestRealLibraryReverb:
    """Test RoomReverb with real library."""
    
    def test_reverb_creation(self):
        """Test reverb creation with real library."""
        with steamaudio.Context():
            reverb = steamaudio.RoomReverb()
            assert reverb is not None
    
    def test_reverb_set_preset(self):
        """Test setting reverb preset."""
        with steamaudio.Context():
            reverb = steamaudio.RoomReverb()
            
            # Test all presets
            presets = [
                steamaudio.RoomReverb.PRESET_SMALL_ROOM,
                steamaudio.RoomReverb.PRESET_MEDIUM_ROOM,
                steamaudio.RoomReverb.PRESET_LARGE_ROOM,
                steamaudio.RoomReverb.PRESET_SMALL_HALL,
                steamaudio.RoomReverb.PRESET_LARGE_HALL,
                steamaudio.RoomReverb.PRESET_CATHEDRAL,
                steamaudio.RoomReverb.PRESET_OUTDOOR,
            ]
            
            for preset in presets:
                reverb.set_preset(preset)
    
    def test_reverb_set_custom_params(self):
        """Test setting custom reverb parameters."""
        with steamaudio.Context():
            reverb = steamaudio.RoomReverb()
            
            reverb.set_params(
                room_width=5.0,
                room_height=3.0,
                room_depth=4.0,
                wall_absorption=0.5,
                reverb_time=0.8
            )
            
            params = reverb.get_params()
            assert abs(params['room_width'] - 5.0) < 1e-5
            assert abs(params['room_height'] - 3.0) < 1e-5
            assert abs(params['room_depth'] - 4.0) < 1e-5
            assert abs(params['wall_absorption'] - 0.5) < 1e-5
            assert abs(params['reverb_time'] - 0.8) < 1e-5
    
    def test_reverb_process_audio(self):
        """Test processing audio through reverb."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            reverb = steamaudio.RoomReverb()
            reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
            
            audio = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
            output = reverb.process(audio)
            
            assert output.shape == (1024,)
            assert output.dtype == np.float32


class TestRealLibraryDirectEffect:
    """Test DirectEffect with real library."""
    
    def test_effect_creation(self):
        """Test direct effect creation with real library."""
        with steamaudio.Context():
            effect = steamaudio.DirectEffect()
            assert effect is not None
    
    def test_effect_set_params(self):
        """Test setting direct effect parameters."""
        with steamaudio.Context():
            effect = steamaudio.DirectEffect()
            
            effect.set_params(
                distance=5.0,
                occlusion=0.5,
                transmission_low=0.8,
                transmission_mid=0.6,
                transmission_high=0.4
            )
    
    def test_effect_process_audio(self):
        """Test processing audio through direct effect."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            effect = steamaudio.DirectEffect()
            effect.set_params(distance=5.0, occlusion=0.3)
            
            audio = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
            output = effect.process(audio)
            
            assert output.shape == (1024,)
            assert output.dtype == np.float32


class TestRealLibraryComplexWorkflow:
    """Test complex workflows with real library."""
    
    def test_full_audio_pipeline(self):
        """Test full audio processing pipeline."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            # Create processor
            processor = steamaudio.AudioProcessor(input_channels=1)
            
            # Create effects
            reverb = steamaudio.RoomReverb()
            reverb.set_preset(steamaudio.RoomReverb.PRESET_MEDIUM_ROOM)
            
            direct = steamaudio.DirectEffect()
            direct.set_params(distance=5.0, occlusion=0.2)
            
            # Create test audio
            audio = np.sin(2 * np.pi * 440 * np.arange(2048) / 44100).astype(np.float32)
            
            # Process through pipeline
            params = steamaudio.SpatializationParams()
            params.listener_pos = steamaudio.Vector3(0, 0, 0)
            params.sound_pos = steamaudio.Vector3(5, 0, 0)
            
            # Spatialize
            spatialized = processor.process(audio, params)
            assert spatialized.shape == (2048, 2)
            
            # Apply direct effect to mono
            direct_out = direct.process(audio)
            assert direct_out.shape == (2048,)
            
            # Apply reverb
            reverb_out = reverb.process(audio)
            assert reverb_out.shape == (2048,)
    
    def test_mixer_with_effects(self):
        """Test mixer combined with effects."""
        with steamaudio.Context(sample_rate=44100, frame_size=256):
            # Create mixer
            mixer = steamaudio.AudioMixer(max_sources=4)
            mixer.add_source(0, input_channels=1)
            mixer.add_source(1, input_channels=1)
            
            # Create reverb
            reverb = steamaudio.RoomReverb()
            reverb.set_preset(steamaudio.RoomReverb.PRESET_SMALL_HALL)
            
            # Create test audio
            audio1 = np.sin(2 * np.pi * 440 * np.arange(1024) / 44100).astype(np.float32)
            audio2 = np.sin(2 * np.pi * 880 * np.arange(1024) / 44100).astype(np.float32)
            
            params1 = steamaudio.SpatializationParams()
            params1.listener_pos = steamaudio.Vector3(0, 0, 0)
            params1.sound_pos = steamaudio.Vector3(5, 0, 0)
            
            params2 = steamaudio.SpatializationParams()
            params2.listener_pos = steamaudio.Vector3(0, 0, 0)
            params2.sound_pos = steamaudio.Vector3(-5, 0, 0)
            
            # Mix sources
            mixed = mixer.process(
                {0: audio1, 1: audio2},
                {0: params1, 1: params2}
            )
            assert mixed.shape == (1024, 2)
            
            # Apply reverb to first channel
            reverb_out = reverb.process(mixed[:, 0])
            assert reverb_out.shape == (1024,)
