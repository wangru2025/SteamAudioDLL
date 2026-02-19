#include "phonon_wrapper.h"
#include <sstream>

PhononWrapper& PhononWrapper::instance() {
    static PhononWrapper instance;
    return instance;
}

PhononWrapper::~PhononWrapper() {
    shutdown();
}

bool PhononWrapper::initialize(int sample_rate, int frame_size) {
    if (context_) {
        last_error_ = "Already initialized";
        return false;
    }
    
    // Create context
    IPLContextSettings context_settings{};
    context_settings.version = STEAMAUDIO_VERSION;
    
    if (iplContextCreate(&context_settings, &context_) != IPL_STATUS_SUCCESS) {
        last_error_ = "Failed to create Phonon context";
        return false;
    }
    
    // Setup audio settings
    audio_settings_.samplingRate = sample_rate;
    audio_settings_.frameSize = frame_size;
    
    // Create HRTF
    IPLHRTFSettings hrtf_settings{};
    hrtf_settings.type = IPL_HRTFTYPE_DEFAULT;
    hrtf_settings.volume = 1.0f;
    
    if (iplHRTFCreate(context_, &audio_settings_, &hrtf_settings, &hrtf_) != IPL_STATUS_SUCCESS) {
        iplContextRelease(&context_);
        context_ = nullptr;
        last_error_ = "Failed to create HRTF";
        return false;
    }
    
    hrtf_enabled_ = true;
    return true;
}

void PhononWrapper::shutdown() {
    if (hrtf_) {
        iplHRTFRelease(&hrtf_);
        hrtf_ = nullptr;
    }
    
    if (context_) {
        iplContextRelease(&context_);
        context_ = nullptr;
    }
    
    hrtf_enabled_ = false;
}

bool PhononWrapper::is_initialized() const {
    return context_ != nullptr;
}

bool PhononWrapper::set_hrtf_enabled(bool enabled) {
    if (!context_) {
        last_error_ = "Phonon not initialized";
        return false;
    }
    
    hrtf_enabled_ = enabled;
    return true;
}
