#pragma once

#include <phonon.h>
#include <memory>
#include <unordered_map>
#include <vector>
#include "c_interface.h"

class AudioSource {
public:
    AudioSource(int source_id, int input_channels);
    ~AudioSource();
    
    int get_id() const { return source_id_; }
    int get_input_channels() const { return input_channels_; }
    
    bool process(
        const float* input_data,
        int input_frame_count,
        float* output_data,
        int& output_frame_count,
        const SpatializationParams& params
    );
    
private:
    int source_id_;
    int input_channels_;
    
    IPLBinauralEffect binaural_effect_ = nullptr;
    IPLAudioBuffer input_buffer_ = {};
    IPLAudioBuffer output_buffer_ = {};
    IPLBinauralEffectParams binaural_params_ = {};
    
    bool initialize_effects();
    void cleanup_effects();
    
    Vector3 calculate_direction(const SpatializationParams& params);
    float calculate_distance(const SpatializationParams& params);
};

class AudioMixer {
public:
    AudioMixer(int max_sources);
    ~AudioMixer();
    
    int get_max_sources() const { return max_sources_; }
    int get_source_count() const { return static_cast<int>(sources_.size()); }
    
    bool add_source(int source_id, int input_channels);
    bool remove_source(int source_id);
    bool has_source(int source_id) const;
    
    bool process(
        const int* source_ids,
        const float* const* input_data_array,
        const int* input_frame_counts,
        int num_sources,
        float* output_data,
        int& output_frame_count,
        const SpatializationParams* params_array
    );
    
private:
    int max_sources_;
    std::unordered_map<int, std::unique_ptr<AudioSource>> sources_;
    std::vector<float> mix_buffer_;
    
    bool initialize_mix_buffer(int frame_count);
};
