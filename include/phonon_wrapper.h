#pragma once

#include <phonon.h>
#include <memory>
#include <string>

class PhononWrapper {
public:
    static PhononWrapper& instance();
    
    bool initialize(int sample_rate, int frame_size);
    void shutdown();
    bool is_initialized() const;
    
    IPLContext get_context() const { return context_; }
    IPLHRTF get_hrtf() const { return hrtf_; }
    const IPLAudioSettings& get_audio_settings() const { return audio_settings_; }
    
    bool set_hrtf_enabled(bool enabled);
    bool get_hrtf_enabled() const { return hrtf_enabled_; }
    
    const std::string& get_last_error() const { return last_error_; }
    
private:
    PhononWrapper() = default;
    ~PhononWrapper();
    
    PhononWrapper(const PhononWrapper&) = delete;
    PhononWrapper& operator=(const PhononWrapper&) = delete;
    
    IPLContext context_ = nullptr;
    IPLHRTF hrtf_ = nullptr;
    IPLAudioSettings audio_settings_ = {};
    bool hrtf_enabled_ = false;
    std::string last_error_;
};
