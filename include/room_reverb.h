#pragma once

#include <phonon.h>
#include <memory>
#include <vector>
#include "c_interface.h"

class RoomReverb {
public:
    RoomReverb();
    ~RoomReverb();
    
    bool set_preset(int preset);
    
    bool set_params(
        float room_width,
        float room_height,
        float room_depth,
        float wall_absorption,
        float reverb_time
    );
    
    bool get_params(
        float& room_width,
        float& room_height,
        float& room_depth,
        float& wall_absorption,
        float& reverb_time
    ) const;
    
    bool process(
        const float* input_data,
        int input_frame_count,
        float* output_data,
        int& output_frame_count
    );
    
private:
    // Room parameters
    float room_width_ = 10.0f;
    float room_height_ = 3.0f;
    float room_depth_ = 10.0f;
    float wall_absorption_ = 0.5f;
    float reverb_time_ = 1.0f;
    
    // Steam Audio objects
    IPLReflectionEffect reflection_effect_ = nullptr;
    IPLReflectionEffectParams reflection_params_ = {};
    IPLAudioBuffer input_buffer_ = {};
    IPLAudioBuffer output_buffer_ = {};
    
    // Reverb times for 3 frequency bands (low, mid, high)
    float reverb_times_[3] = {1.0f, 1.0f, 1.0f};
    
    bool initialize_effects();
    void cleanup_effects();
    void calculate_reverb_times();
};
