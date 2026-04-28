#pragma once

#include <phonon.h>
#include <memory>
#include "c_interface.h"

class DirectEffect {
public:
    DirectEffect();
    ~DirectEffect();
    
    bool set_params(
        float distance,
        float occlusion,
        float transmission_low,
        float transmission_mid,
        float transmission_high,
        int flags
    );
    
    bool process(
        const float* input_data,
        int input_frame_count,
        float* output_data,
        int& output_frame_count
    );

    bool set_simulation_params(const IPLDirectEffectParams& params);
    
private:
    // Direct effect parameters
    float distance_ = 1.0f;
    float occlusion_ = 0.0f;
    float transmission_low_ = 1.0f;
    float transmission_mid_ = 1.0f;
    float transmission_high_ = 1.0f;
    int flags_ = 0;
    
    // Steam Audio objects
    IPLDirectEffect direct_effect_ = nullptr;
    IPLDirectEffectParams direct_params_ = {};
    IPLAudioBuffer input_buffer_ = {};
    IPLAudioBuffer output_buffer_ = {};
    
    // Air absorption model
    IPLAirAbsorptionModel air_absorption_model_ = {};
    
    bool initialize_effects();
    void cleanup_effects();
};
