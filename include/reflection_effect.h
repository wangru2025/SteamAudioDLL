#pragma once

#include <phonon.h>
#include "c_interface.h"

class ReflectionEffect {
public:
    ReflectionEffect(int max_order, float max_duration);
    ~ReflectionEffect();

    bool set_listener(const DirectListenerParams& params);
    bool set_simulation_params(const IPLReflectionEffectParams& params);
    bool process(
        const float* input_data,
        int input_frame_count,
        float* output_data,
        int& output_frame_count
    );

private:
    int max_order_ = 2;
    float max_duration_ = 2.0f;
    int max_ir_size_ = 0;
    int max_ir_channels_ = 0;
    int current_order_ = 2;

    IPLReflectionEffect reflection_effect_ = nullptr;
    IPLAmbisonicsDecodeEffect decode_effect_ = nullptr;
    IPLReflectionEffectParams reflection_params_ = {};
    IPLCoordinateSpace3 listener_ = {};
    IPLAudioBuffer input_buffer_ = {};
    IPLAudioBuffer reflections_buffer_ = {};
    IPLAudioBuffer stereo_buffer_ = {};

    bool initialize_effects();
    void cleanup_effects();
    static IPLCoordinateSpace3 to_coordinate_space(const CoordinateSpace& space);
};
