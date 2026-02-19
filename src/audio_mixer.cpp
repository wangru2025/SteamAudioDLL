#include "audio_mixer.h"
#include "phonon_wrapper.h"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <algorithm>

// ============================================================================
// AudioSource Implementation
// ============================================================================

AudioSource::AudioSource(int source_id, int input_channels)
    : source_id_(source_id), input_channels_(input_channels) {
    
    auto& phonon = PhononWrapper::instance();
    const auto& audio_settings = phonon.get_audio_settings();
    
    // Allocate Phonon audio buffers
    if (iplAudioBufferAllocate(phonon.get_context(), input_channels, audio_settings.frameSize, &input_buffer_) != IPL_STATUS_SUCCESS) {
        throw std::runtime_error("Failed to allocate input audio buffer for source");
    }
    
    if (iplAudioBufferAllocate(phonon.get_context(), 2, audio_settings.frameSize, &output_buffer_) != IPL_STATUS_SUCCESS) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        throw std::runtime_error("Failed to allocate output audio buffer for source");
    }
    
    initialize_effects();
}

AudioSource::~AudioSource() {
    cleanup_effects();
    
    auto& phonon = PhononWrapper::instance();
    if (phonon.is_initialized()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &output_buffer_);
    }
}

bool AudioSource::initialize_effects() {
    auto& phonon = PhononWrapper::instance();
    
    if (!phonon.is_initialized()) {
        return false;
    }
    
    IPLContext context = phonon.get_context();
    auto audio_settings = phonon.get_audio_settings();
    
    // Create binaural effect
    IPLBinauralEffectSettings binaural_settings{};
    binaural_settings.hrtf = phonon.get_hrtf();
    
    if (iplBinauralEffectCreate(context, &audio_settings, &binaural_settings, &binaural_effect_) != IPL_STATUS_SUCCESS) {
        return false;
    }
    
    // Initialize binaural parameters
    binaural_params_ = {};
    binaural_params_.hrtf = phonon.get_hrtf();
    binaural_params_.interpolation = IPL_HRTFINTERPOLATION_NEAREST;
    binaural_params_.spatialBlend = 1.0f;
    
    return true;
}

void AudioSource::cleanup_effects() {
    if (binaural_effect_) {
        iplBinauralEffectRelease(&binaural_effect_);
        binaural_effect_ = nullptr;
    }
}

Vector3 AudioSource::calculate_direction(const SpatializationParams& params) {
    Vector3 direction;
    direction.x = params.sound_pos.x - params.listener_pos.x;
    direction.y = params.sound_pos.y - params.listener_pos.y;
    direction.z = params.sound_pos.z - params.listener_pos.z;
    
    // Normalize
    float length = std::sqrt(direction.x * direction.x + direction.y * direction.y + direction.z * direction.z);
    if (length > 0.001f) {
        direction.x /= length;
        direction.y /= length;
        direction.z /= length;
    } else {
        // When listener and source are at same position, use default forward direction
        direction.x = 0.0f;
        direction.y = 0.0f;
        direction.z = 1.0f;
    }
    
    return direction;
}

float AudioSource::calculate_distance(const SpatializationParams& params) {
    float dx = params.sound_pos.x - params.listener_pos.x;
    float dy = params.sound_pos.y - params.listener_pos.y;
    float dz = params.sound_pos.z - params.listener_pos.z;
    
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

bool AudioSource::process(
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int& output_frame_count,
    const SpatializationParams& params) {
    
    auto& phonon = PhononWrapper::instance();
    if (!phonon.is_initialized() || !binaural_effect_) {
        return false;
    }
    
    const auto& audio_settings = phonon.get_audio_settings();
    
    // Process in chunks matching the frame size
    int total_processed = 0;
    
    while (total_processed < input_frame_count) {
        int frames_to_process = std::min((int)audio_settings.frameSize, input_frame_count - total_processed);
        
        // Deinterleave input
        iplAudioBufferDeinterleave(
            phonon.get_context(),
            (float*)input_data + total_processed * input_channels_,
            &input_buffer_
        );
        
        input_buffer_.numSamples = frames_to_process;
        output_buffer_.numSamples = frames_to_process;
        
        // Update spatialization parameters
        Vector3 direction = calculate_direction(params);
        float distance = calculate_distance(params);
        
        binaural_params_.direction.x = direction.x;
        binaural_params_.direction.y = direction.y;
        binaural_params_.direction.z = direction.z;
        
        // Spatial blend based on distance
        float volume_attenuation = 1.0f;
        if (distance > 0.1f) {
            // Inverse square law: volume decreases with distance squared
            volume_attenuation = 1.0f / (1.0f + distance * distance / 100.0f);
        }
        
        // Always use full spatial blend for direction
        binaural_params_.spatialBlend = 1.0f;
        
        // Apply volume attenuation to input before processing
        for (int i = 0; i < input_buffer_.numSamples; ++i) {
            for (int ch = 0; ch < input_channels_; ++ch) {
                input_buffer_.data[ch][i] *= volume_attenuation;
            }
        }
        
        // Apply binaural effect
        iplBinauralEffectApply(binaural_effect_, &binaural_params_, &input_buffer_, &output_buffer_);
        
        // Interleave output
        iplAudioBufferInterleave(
            phonon.get_context(),
            &output_buffer_,
            output_data + total_processed * 2
        );
        
        total_processed += frames_to_process;
    }
    
    output_frame_count = input_frame_count;
    return true;
}

// ============================================================================
// AudioMixer Implementation
// ============================================================================

AudioMixer::AudioMixer(int max_sources)
    : max_sources_(max_sources) {
    if (max_sources <= 0) {
        throw std::invalid_argument("max_sources must be greater than 0");
    }
}

AudioMixer::~AudioMixer() {
    sources_.clear();
    mix_buffer_.clear();
}

bool AudioMixer::add_source(int source_id, int input_channels) {
    if (sources_.find(source_id) != sources_.end()) {
        return false; // Source already exists
    }
    
    if (sources_.size() >= max_sources_) {
        return false; // Mixer is full
    }
    
    try {
        sources_[source_id] = std::make_unique<AudioSource>(source_id, input_channels);
        return true;
    } catch (const std::exception&) {
        sources_.erase(source_id);
        return false;
    }
}

bool AudioMixer::remove_source(int source_id) {
    auto it = sources_.find(source_id);
    if (it == sources_.end()) {
        return false;
    }
    
    sources_.erase(it);
    return true;
}

bool AudioMixer::has_source(int source_id) const {
    return sources_.find(source_id) != sources_.end();
}

bool AudioMixer::initialize_mix_buffer(int frame_count) {
    int required_size = frame_count * 2; // Stereo output
    if (mix_buffer_.size() < required_size) {
        mix_buffer_.resize(required_size, 0.0f);
    }
    return true;
}

bool AudioMixer::process(
    const float* const* input_data_array,
    const int* input_frame_counts,
    int num_sources,
    float* output_data,
    int& output_frame_count,
    const SpatializationParams* params_array) {
    
    if (!input_data_array || !input_frame_counts || !params_array || !output_data) {
        return false;
    }
    
    if (num_sources <= 0 || num_sources > sources_.size()) {
        return false;
    }
    
    // Determine the maximum frame count
    int max_frames = 0;
    for (int i = 0; i < num_sources; ++i) {
        max_frames = std::max(max_frames, input_frame_counts[i]);
    }
    
    if (max_frames <= 0) {
        return false;
    }
    
    // Initialize mix buffer
    if (!initialize_mix_buffer(max_frames)) {
        return false;
    }
    
    // Clear mix buffer
    std::fill(mix_buffer_.begin(), mix_buffer_.begin() + max_frames * 2, 0.0f);
    
    // Process each source and accumulate to mix buffer
    std::vector<float> source_output(max_frames * 2, 0.0f);
    int source_index = 0;
    
    for (auto& [source_id, source] : sources_) {
        if (source_index >= num_sources) {
            break;
        }
        
        int frame_count = input_frame_counts[source_index];
        int output_frame_count_temp = 0;
        
        // Process this source
        if (!source->process(
            input_data_array[source_index],
            frame_count,
            source_output.data(),
            output_frame_count_temp,
            params_array[source_index])) {
            source_index++;
            continue;
        }
        
        // Mix into output buffer (simple addition with normalization)
        for (int i = 0; i < output_frame_count_temp * 2; ++i) {
            mix_buffer_[i] += source_output[i];
        }
        
        source_index++;
    }
    
    // Normalize mixed output to prevent clipping
    float max_amplitude = 0.0f;
    for (int i = 0; i < max_frames * 2; ++i) {
        max_amplitude = std::max(max_amplitude, std::abs(mix_buffer_[i]));
    }
    
    float normalization_factor = 1.0f;
    if (max_amplitude > 1.0f) {
        normalization_factor = 1.0f / max_amplitude;
    }
    
    // Copy to output with normalization
    for (int i = 0; i < max_frames * 2; ++i) {
        output_data[i] = mix_buffer_[i] * normalization_factor;
    }
    
    output_frame_count = max_frames;
    return true;
}
