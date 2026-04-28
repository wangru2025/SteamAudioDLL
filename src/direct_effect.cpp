#include "direct_effect.h"
#include "phonon_wrapper.h"
#include <cmath>
#include <algorithm>
#include <stdexcept>

DirectEffect::DirectEffect() {
    if (!initialize_effects()) {
        throw std::runtime_error("Failed to initialize direct effect");
    }
}

DirectEffect::~DirectEffect() {
    cleanup_effects();
}

bool DirectEffect::initialize_effects() {
    auto& phonon = PhononWrapper::instance();
    
    if (!phonon.is_initialized()) {
        return false;
    }
    
    IPLContext context = phonon.get_context();
    auto audio_settings = phonon.get_audio_settings();
    
    // Create direct effect
    IPLDirectEffectSettings direct_settings{};
    direct_settings.numChannels = 1;
    
    if (iplDirectEffectCreate(context, &audio_settings, &direct_settings, &direct_effect_) != IPL_STATUS_SUCCESS) {
        return false;
    }
    
    // Allocate audio buffers
    if (iplAudioBufferAllocate(context, 1, audio_settings.frameSize, &input_buffer_) != IPL_STATUS_SUCCESS) {
        iplDirectEffectRelease(&direct_effect_);
        return false;
    }
    
    if (iplAudioBufferAllocate(context, 1, audio_settings.frameSize, &output_buffer_) != IPL_STATUS_SUCCESS) {
        iplAudioBufferFree(context, &input_buffer_);
        iplDirectEffectRelease(&direct_effect_);
        return false;
    }
    
    // Initialize direct parameters
    direct_params_ = {};
    direct_params_.flags = static_cast<IPLDirectEffectFlags>(
        IPL_DIRECTEFFECTFLAGS_APPLYDISTANCEATTENUATION |
        IPL_DIRECTEFFECTFLAGS_APPLYAIRABSORPTION
    );
    direct_params_.directivity = 1.0f;
    direct_params_.occlusion = 0.0f;
    
    // Initialize air absorption (3 bands)
    for (int i = 0; i < 3; ++i) {
        direct_params_.airAbsorption[i] = 1.0f;
        direct_params_.transmission[i] = 1.0f;
    }
    
    // Initialize air absorption model
    air_absorption_model_ = {};
    air_absorption_model_.type = IPL_AIRABSORPTIONTYPE_DEFAULT;
    
    return true;
}

void DirectEffect::cleanup_effects() {
    auto& phonon = PhononWrapper::instance();
    
    if (direct_effect_) {
        iplDirectEffectRelease(&direct_effect_);
        direct_effect_ = nullptr;
    }
    
    if (phonon.is_initialized()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &output_buffer_);
    }
}

bool DirectEffect::set_params(
    float distance,
    float occlusion,
    float transmission_low,
    float transmission_mid,
    float transmission_high,
    int flags) {
    
    // Validate parameters
    if (distance < 0.1f) {
        distance = 0.1f;
    }
    
    occlusion = std::max(0.0f, std::min(1.0f, occlusion));
    transmission_low = std::max(0.0f, std::min(1.0f, transmission_low));
    transmission_mid = std::max(0.0f, std::min(1.0f, transmission_mid));
    transmission_high = std::max(0.0f, std::min(1.0f, transmission_high));
    
    distance_ = distance;
    occlusion_ = occlusion;
    transmission_low_ = transmission_low;
    transmission_mid_ = transmission_mid;
    transmission_high_ = transmission_high;
    flags_ = flags;
    
    // Update direct parameters
    direct_params_.distanceAttenuation = 1.0f / (1.0f + distance_ * distance_ / 100.0f);
    direct_params_.occlusion = occlusion_;
    direct_params_.transmission[0] = transmission_low_;
    direct_params_.transmission[1] = transmission_mid_;
    direct_params_.transmission[2] = transmission_high_;
    
    // Set flags
    direct_params_.flags = static_cast<IPLDirectEffectFlags>(flags_);

    return true;
}

bool DirectEffect::set_simulation_params(const IPLDirectEffectParams& params) {
    direct_params_ = params;
    return true;
}

bool DirectEffect::process(
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int& output_frame_count) {
    
    auto& phonon = PhononWrapper::instance();
    
    if (!phonon.is_initialized() || !direct_effect_) {
        return false;
    }
    
    const auto& audio_settings = phonon.get_audio_settings();
    
    // Process in chunks
    int total_processed = 0;
    
    while (total_processed < input_frame_count) {
        int frames_to_process = std::min((int)audio_settings.frameSize, input_frame_count - total_processed);
        
        // Copy input to buffer
        for (int i = 0; i < frames_to_process; ++i) {
            input_buffer_.data[0][i] = input_data[total_processed + i];
        }
        
        input_buffer_.numSamples = frames_to_process;
        output_buffer_.numSamples = frames_to_process;
        
        // Apply direct effect
        iplDirectEffectApply(direct_effect_, &direct_params_, &input_buffer_, &output_buffer_);
        
        // Copy output
        for (int i = 0; i < frames_to_process; ++i) {
            output_data[total_processed + i] = output_buffer_.data[0][i];
        }
        
        total_processed += frames_to_process;
    }
    
    output_frame_count = input_frame_count;
    return true;
}
