#pragma once

#include <phonon.h>
#include <memory>
#include <vector>
#include "c_interface.h"

class AudioProcessor {
public:
    AudioProcessor(int input_channels, int output_channels);
    ~AudioProcessor();
    
    int get_input_channels() const { return input_channels_; }
    int get_output_channels() const { return output_channels_; }
    
    bool process(
        const float* input_data,
        int input_frame_count,
        float* output_data,
        int& output_frame_count,
        const SpatializationParams& params
    );
    
    bool set_reverb_enabled(bool enabled);
    bool get_reverb_enabled() const { return reverb_enabled_; }
    
    bool set_reverb_params(
        float room_size,
        float damping,
        float width,
        float wet_level,
        float dry_level
    );
    
private:
    int input_channels_;
    int output_channels_;
    
    IPLBinauralEffect binaural_effect_ = nullptr;
    IPLAudioBuffer input_buffer_ = {};
    IPLAudioBuffer output_buffer_ = {};
    
    bool reverb_enabled_ = false;
    
    IPLBinauralEffectParams binaural_params_ = {};
    
    bool initialize_effects();
    void cleanup_effects();
    
    Vector3 calculate_direction(const SpatializationParams& params);
    float calculate_distance(const SpatializationParams& params);
};
