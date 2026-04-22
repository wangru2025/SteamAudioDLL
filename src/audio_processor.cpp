#include "audio_processor.h"
#include "phonon_wrapper.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <stdexcept>

AudioProcessor::AudioProcessor(int input_channels, int output_channels)
    : input_channels_(input_channels), output_channels_(output_channels) {
    
    auto& phonon = PhononWrapper::instance();
    const auto& audio_settings = phonon.get_audio_settings();
    
    // Allocate Phonon audio buffers using their API
    if (iplAudioBufferAllocate(phonon.get_context(), input_channels, audio_settings.frameSize, &input_buffer_) != IPL_STATUS_SUCCESS) {
        throw std::runtime_error("Failed to allocate input audio buffer");
    }
    
    if (iplAudioBufferAllocate(phonon.get_context(), output_channels, audio_settings.frameSize, &output_buffer_) != IPL_STATUS_SUCCESS) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        throw std::runtime_error("Failed to allocate output audio buffer");
    }
    
    if (!initialize_effects()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &output_buffer_);
        throw std::runtime_error("Failed to initialize binaural effect");
    }
}

AudioProcessor::~AudioProcessor() {
    cleanup_effects();
    
    auto& phonon = PhononWrapper::instance();
    if (phonon.is_initialized()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &output_buffer_);
    }
}

bool AudioProcessor::initialize_effects() {
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

void AudioProcessor::cleanup_effects() {
    if (binaural_effect_) {
        iplBinauralEffectRelease(&binaural_effect_);
        binaural_effect_ = nullptr;
    }
}

Vector3 AudioProcessor::calculate_direction(const SpatializationParams& params) {
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

float AudioProcessor::calculate_distance(const SpatializationParams& params) {
    float dx = params.sound_pos.x - params.listener_pos.x;
    float dy = params.sound_pos.y - params.listener_pos.y;
    float dz = params.sound_pos.z - params.listener_pos.z;
    
    return std::sqrt(dx * dx + dy * dy + dz * dz);
}

bool AudioProcessor::process(
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

        input_buffer_.numSamples = frames_to_process;
        output_buffer_.numSamples = frames_to_process;

        for (int ch = 0; ch < input_channels_; ++ch) {
            std::fill(input_buffer_.data[ch], input_buffer_.data[ch] + frames_to_process, 0.0f);
        }

        for (int i = 0; i < frames_to_process; ++i) {
            for (int ch = 0; ch < input_channels_; ++ch) {
                input_buffer_.data[ch][i] = input_data[(total_processed + i) * input_channels_ + ch];
            }
        }
        
        // Update spatialization parameters
        Vector3 direction = calculate_direction(params);
        float distance = calculate_distance(params);
        
        binaural_params_.direction.x = direction.x;
        binaural_params_.direction.y = direction.y;
        binaural_params_.direction.z = direction.z;
        
        // Spatial blend based on distance - apply distance attenuation
        // Use volume attenuation instead of spatial blend for far distances
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
        
        if (phonon.get_hrtf_enabled()) {
            iplBinauralEffectApply(binaural_effect_, &binaural_params_, &input_buffer_, &output_buffer_);

            iplAudioBufferInterleave(
                phonon.get_context(),
                &output_buffer_,
                output_data + total_processed * 2
            );
        } else {
            for (int i = 0; i < frames_to_process; ++i) {
                if (input_channels_ == 1) {
                    const float sample = input_buffer_.data[0][i];
                    output_data[(total_processed + i) * 2] = sample;
                    output_data[(total_processed + i) * 2 + 1] = sample;
                } else {
                    output_data[(total_processed + i) * 2] = input_buffer_.data[0][i];
                    output_data[(total_processed + i) * 2 + 1] = input_buffer_.data[1][i];
                }
            }
        }
        
        total_processed += frames_to_process;
    }
    
    output_frame_count = input_frame_count;
    return true;
}

bool AudioProcessor::set_reverb_enabled(bool enabled) {
    reverb_enabled_ = enabled;
    return true;
}

bool AudioProcessor::set_reverb_params(
    float room_size,
    float damping,
    float width,
    float wet_level,
    float dry_level) {
    
    // Store reverb parameters for future use
    // This is a placeholder for reverb implementation
    (void)room_size;
    (void)damping;
    (void)width;
    (void)wet_level;
    (void)dry_level;
    return true;
}
