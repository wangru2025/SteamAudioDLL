#include "room_reverb.h"
#include "phonon_wrapper.h"
#include <cmath>
#include <algorithm>

RoomReverb::RoomReverb() {
    initialize_effects();
}

RoomReverb::~RoomReverb() {
    cleanup_effects();
}

void RoomReverb::calculate_reverb_times() {
    // Sabine's formula: RT60 = 0.161 * V / (A * alpha)
    // where V = volume, A = surface area, alpha = absorption coefficient
    
    float volume = room_width_ * room_height_ * room_depth_;
    float surface_area = 2.0f * (room_width_ * room_height_ + 
                                 room_height_ * room_depth_ + 
                                 room_depth_ * room_width_);
    
    // Absorption varies by frequency band
    // Low frequencies: less absorption (longer reverb)
    // Mid frequencies: normal absorption
    // High frequencies: more absorption (shorter reverb)
    
    float absorption_low = wall_absorption_ * 0.7f;
    float absorption_mid = wall_absorption_;
    float absorption_high = wall_absorption_ * 1.3f;
    
    // Clamp absorption to valid range
    absorption_low = std::max(0.01f, std::min(0.99f, absorption_low));
    absorption_mid = std::max(0.01f, std::min(0.99f, absorption_mid));
    absorption_high = std::max(0.01f, std::min(0.99f, absorption_high));
    
    // Calculate RT60 for each band
    reverb_times_[0] = 0.161f * volume / (surface_area * absorption_low);
    reverb_times_[1] = 0.161f * volume / (surface_area * absorption_mid);
    reverb_times_[2] = 0.161f * volume / (surface_area * absorption_high);
    
    // Scale by user-specified reverb time
    for (int i = 0; i < 3; ++i) {
        reverb_times_[i] *= (reverb_time_ / 1.0f);
        // Clamp to reasonable range (0.1 to 10 seconds)
        reverb_times_[i] = std::max(0.1f, std::min(10.0f, reverb_times_[i]));
    }
}

bool RoomReverb::initialize_effects() {
    auto& phonon = PhononWrapper::instance();
    
    if (!phonon.is_initialized()) {
        return false;
    }
    
    IPLContext context = phonon.get_context();
    auto audio_settings = phonon.get_audio_settings();
    
    // Create reflection effect for parametric reverb
    IPLReflectionEffectSettings reflection_settings{};
    reflection_settings.type = IPL_REFLECTIONEFFECTTYPE_PARAMETRIC;
    reflection_settings.numChannels = 1;
    
    if (iplReflectionEffectCreate(context, &audio_settings, &reflection_settings, &reflection_effect_) != IPL_STATUS_SUCCESS) {
        return false;
    }
    
    // Allocate audio buffers
    if (iplAudioBufferAllocate(context, 1, audio_settings.frameSize, &input_buffer_) != IPL_STATUS_SUCCESS) {
        iplReflectionEffectRelease(&reflection_effect_);
        return false;
    }
    
    if (iplAudioBufferAllocate(context, 1, audio_settings.frameSize, &output_buffer_) != IPL_STATUS_SUCCESS) {
        iplAudioBufferFree(context, &input_buffer_);
        iplReflectionEffectRelease(&reflection_effect_);
        return false;
    }
    
    // Initialize reflection parameters
    reflection_params_ = {};
    calculate_reverb_times();
    
    for (int i = 0; i < 3; ++i) {
        reflection_params_.reverbTimes[i] = reverb_times_[i];
    }
    
    return true;
}

void RoomReverb::cleanup_effects() {
    auto& phonon = PhononWrapper::instance();
    
    if (reflection_effect_) {
        iplReflectionEffectRelease(&reflection_effect_);
        reflection_effect_ = nullptr;
    }
    
    if (phonon.is_initialized()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &output_buffer_);
    }
}

bool RoomReverb::set_preset(int preset) {
    switch (preset) {
        case 0: // ROOM_PRESET_SMALL_ROOM
            return set_params(2.0f, 2.0f, 2.0f, 0.4f, 0.3f);
        case 1: // ROOM_PRESET_MEDIUM_ROOM
            return set_params(5.0f, 4.0f, 3.0f, 0.5f, 0.6f);
        case 2: // ROOM_PRESET_LARGE_ROOM
            return set_params(10.0f, 8.0f, 4.0f, 0.5f, 1.0f);
        case 3: // ROOM_PRESET_SMALL_HALL
            return set_params(15.0f, 10.0f, 5.0f, 0.6f, 1.5f);
        case 4: // ROOM_PRESET_LARGE_HALL
            return set_params(30.0f, 20.0f, 10.0f, 0.6f, 2.5f);
        case 5: // ROOM_PRESET_CATHEDRAL
            return set_params(50.0f, 40.0f, 20.0f, 0.7f, 4.0f);
        case 6: // ROOM_PRESET_OUTDOOR
            return set_params(1000.0f, 1000.0f, 1000.0f, 0.1f, 0.1f);
        default:
            return false;
    }
}

bool RoomReverb::set_params(
    float room_width,
    float room_height,
    float room_depth,
    float wall_absorption,
    float reverb_time) {
    
    // Validate parameters
    if (room_width <= 0.1f || room_height <= 0.1f || room_depth <= 0.1f) {
        return false;
    }
    
    if (wall_absorption < 0.0f || wall_absorption > 1.0f) {
        return false;
    }
    
    if (reverb_time < 0.1f || reverb_time > 10.0f) {
        return false;
    }
    
    room_width_ = room_width;
    room_height_ = room_height;
    room_depth_ = room_depth;
    wall_absorption_ = wall_absorption;
    reverb_time_ = reverb_time;
    
    // Recalculate reverb times
    calculate_reverb_times();
    
    // Update reflection parameters
    for (int i = 0; i < 3; ++i) {
        reflection_params_.reverbTimes[i] = reverb_times_[i];
    }
    
    return true;
}

bool RoomReverb::get_params(
    float& room_width,
    float& room_height,
    float& room_depth,
    float& wall_absorption,
    float& reverb_time) const {
    
    room_width = room_width_;
    room_height = room_height_;
    room_depth = room_depth_;
    wall_absorption = wall_absorption_;
    reverb_time = reverb_time_;
    
    return true;
}

bool RoomReverb::process(
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int& output_frame_count) {
    
    auto& phonon = PhononWrapper::instance();
    
    if (!phonon.is_initialized() || !reflection_effect_) {
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
        
        // Apply reflection effect (parametric reverb)
        // For parametric reverb, mixer is nullptr
        iplReflectionEffectApply(reflection_effect_, &reflection_params_, &input_buffer_, &output_buffer_, nullptr);
        
        // Copy output
        for (int i = 0; i < frames_to_process; ++i) {
            output_data[total_processed + i] = output_buffer_.data[0][i];
        }
        
        total_processed += frames_to_process;
    }
    
    output_frame_count = input_frame_count;
    return true;
}
