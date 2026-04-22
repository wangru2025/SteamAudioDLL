#include "c_interface.h"
#include "phonon_wrapper.h"
#include "audio_processor.h"
#include "audio_mixer.h"
#include "room_reverb.h"
#include "direct_effect.h"
#include <map>
#include <mutex>
#include <memory>

// Global state
static std::map<AudioProcessorHandle, std::unique_ptr<AudioProcessor>> g_processors;
static std::map<AudioMixerHandle, std::unique_ptr<AudioMixer>> g_mixers;
static std::map<RoomReverbHandle, std::unique_ptr<RoomReverb>> g_reverbs;
static std::map<DirectEffectHandle, std::unique_ptr<DirectEffect>> g_direct_effects;
static std::mutex g_processors_mutex;
static std::mutex g_mixers_mutex;
static std::mutex g_reverbs_mutex;
static std::mutex g_direct_effects_mutex;
static std::string g_last_error;

// Handle generation
static AudioProcessorHandle g_next_processor_handle = reinterpret_cast<AudioProcessorHandle>(1);
static AudioMixerHandle g_next_mixer_handle = reinterpret_cast<AudioMixerHandle>(1000000);
static RoomReverbHandle g_next_reverb_handle = reinterpret_cast<RoomReverbHandle>(2000000);
static DirectEffectHandle g_next_direct_effect_handle = reinterpret_cast<DirectEffectHandle>(3000000);

extern "C" {

AudioProcessorHandle allocate_handle() {
    AudioProcessorHandle handle = g_next_processor_handle;
    g_next_processor_handle = reinterpret_cast<AudioProcessorHandle>(reinterpret_cast<uintptr_t>(g_next_processor_handle) + 1);
    return handle;
}

AudioMixerHandle allocate_mixer_handle() {
    AudioMixerHandle handle = g_next_mixer_handle;
    g_next_mixer_handle = reinterpret_cast<AudioMixerHandle>(reinterpret_cast<uintptr_t>(g_next_mixer_handle) + 1);
    return handle;
}

RoomReverbHandle allocate_reverb_handle() {
    RoomReverbHandle handle = g_next_reverb_handle;
    g_next_reverb_handle = reinterpret_cast<RoomReverbHandle>(reinterpret_cast<uintptr_t>(g_next_reverb_handle) + 1);
    return handle;
}

DirectEffectHandle allocate_direct_effect_handle() {
    DirectEffectHandle handle = g_next_direct_effect_handle;
    g_next_direct_effect_handle = reinterpret_cast<DirectEffectHandle>(reinterpret_cast<uintptr_t>(g_next_direct_effect_handle) + 1);
    return handle;
}

/* ===== Core Initialization ===== */

STEAMAUDIO_API SteamAudioError steam_audio_init(int sample_rate, int frame_size) {
    try {
        if (!PhononWrapper::instance().initialize(sample_rate, frame_size)) {
            g_last_error = PhononWrapper::instance().get_last_error();
            return STEAM_AUDIO_ERROR_INIT_FAILED;
        }
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_INIT_FAILED;
    }
}

STEAMAUDIO_API void steam_audio_shutdown() {
    {
        std::lock_guard<std::mutex> lock(g_processors_mutex);
        g_processors.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_mixers_mutex);
        g_mixers.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        g_reverbs.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
        g_direct_effects.clear();
    }
    PhononWrapper::instance().shutdown();
}

STEAMAUDIO_API int steam_audio_is_initialized() {
    return PhononWrapper::instance().is_initialized() ? 1 : 0;
}

/* ===== Audio Processor ===== */

STEAMAUDIO_API AudioProcessorHandle audio_processor_create(int input_channels, int output_channels) {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }
        
        if (input_channels < 1 || input_channels > 2 || output_channels != 2) {
            g_last_error = "Invalid channel configuration";
            return nullptr;
        }
        
        AudioProcessorHandle handle = allocate_handle();
        
        {
            std::lock_guard<std::mutex> lock(g_processors_mutex);
            g_processors[handle] = std::make_unique<AudioProcessor>(input_channels, output_channels);
        }
        
        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void audio_processor_destroy(AudioProcessorHandle handle) {
    std::lock_guard<std::mutex> lock(g_processors_mutex);
    g_processors.erase(handle);
}

STEAMAUDIO_API SteamAudioError audio_processor_process(
    AudioProcessorHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count,
    const SpatializationParams* params) {
    
    try {
        if (!input_data || !output_data || !output_frame_count || !params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_processors_mutex);
        auto it = g_processors.find(handle);
        if (it == g_processors.end()) {
            g_last_error = "Invalid processor handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->process(input_data, input_frame_count, output_data, *output_frame_count, *params)) {
            g_last_error = "Processing failed";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

/* ===== HRTF Control ===== */

STEAMAUDIO_API SteamAudioError steam_audio_set_hrtf_enabled(int enabled) {
    try {
        if (!PhononWrapper::instance().set_hrtf_enabled(enabled != 0)) {
            g_last_error = PhononWrapper::instance().get_last_error();
            return STEAM_AUDIO_ERROR_INIT_FAILED;
        }
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_INIT_FAILED;
    }
}

STEAMAUDIO_API int steam_audio_get_hrtf_enabled() {
    return PhononWrapper::instance().get_hrtf_enabled() ? 1 : 0;
}

/* ===== Reverb Control ===== */

STEAMAUDIO_API SteamAudioError steam_audio_set_reverb_enabled(int enabled) {
    (void)enabled;
    g_last_error = "Global reverb API is not implemented. Use room_reverb_* APIs instead.";
    return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
}

STEAMAUDIO_API SteamAudioError steam_audio_set_reverb_params(
    float room_size,
    float damping,
    float width,
    float wet_level,
    float dry_level) {
    
    (void)room_size;
    (void)damping;
    (void)width;
    (void)wet_level;
    (void)dry_level;
    g_last_error = "Global reverb API is not implemented. Use room_reverb_* APIs instead.";
    return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
}

/* ===== Utility ===== */

STEAMAUDIO_API const char* steam_audio_get_error_message() {
    return g_last_error.c_str();
}

STEAMAUDIO_API const char* steam_audio_get_version() {
    return "1.0.0";
}


/* ===== Multi-Source Mixer Implementation ===== */

STEAMAUDIO_API AudioMixerHandle audio_mixer_create(int max_sources) {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }
        
        if (max_sources < 1 || max_sources > 256) {
            g_last_error = "Invalid max_sources (must be 1-256)";
            return nullptr;
        }
        
        AudioMixerHandle handle = allocate_mixer_handle();
        
        {
            std::lock_guard<std::mutex> lock(g_mixers_mutex);
            g_mixers[handle] = std::make_unique<AudioMixer>(max_sources);
        }
        
        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void audio_mixer_destroy(AudioMixerHandle handle) {
    std::lock_guard<std::mutex> lock(g_mixers_mutex);
    g_mixers.erase(handle);
}

STEAMAUDIO_API SteamAudioError audio_mixer_add_source(
    AudioMixerHandle mixer_handle,
    int source_id,
    int input_channels) {
    
    try {
        if (input_channels < 1 || input_channels > 2) {
            g_last_error = "Invalid input_channels (must be 1 or 2)";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_mixers_mutex);
        auto it = g_mixers.find(mixer_handle);
        if (it == g_mixers.end()) {
            g_last_error = "Invalid mixer handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->add_source(source_id, input_channels)) {
            g_last_error = "Failed to add source (mixer full or source already exists)";
            return STEAM_AUDIO_ERROR_OUT_OF_MEMORY;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError audio_mixer_remove_source(
    AudioMixerHandle mixer_handle,
    int source_id) {
    
    try {
        std::lock_guard<std::mutex> lock(g_mixers_mutex);
        auto it = g_mixers.find(mixer_handle);
        if (it == g_mixers.end()) {
            g_last_error = "Invalid mixer handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->remove_source(source_id)) {
            g_last_error = "Source not found in mixer";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError audio_mixer_process(
    AudioMixerHandle mixer_handle,
    const int* source_ids,
    const float* const* input_data_array,
    const int* input_frame_counts,
    int num_sources,
    float* output_data,
    int* output_frame_count,
    const SpatializationParams* params_array) {
    
    try {
        if (!source_ids || !input_data_array || !input_frame_counts || !output_data || !output_frame_count || !params_array) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (num_sources < 1) {
            g_last_error = "num_sources must be at least 1";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_mixers_mutex);
        auto it = g_mixers.find(mixer_handle);
        if (it == g_mixers.end()) {
            g_last_error = "Invalid mixer handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->process(
            source_ids,
            input_data_array,
            input_frame_counts,
            num_sources,
            output_data,
            *output_frame_count,
            params_array)) {
            g_last_error = "Mixer processing failed";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API int audio_mixer_get_source_count(AudioMixerHandle mixer_handle) {
    std::lock_guard<std::mutex> lock(g_mixers_mutex);
    auto it = g_mixers.find(mixer_handle);
    if (it == g_mixers.end()) {
        return -1;
    }
    return it->second->get_source_count();
}

STEAMAUDIO_API int audio_mixer_get_max_sources(AudioMixerHandle mixer_handle) {
    std::lock_guard<std::mutex> lock(g_mixers_mutex);
    auto it = g_mixers.find(mixer_handle);
    if (it == g_mixers.end()) {
        return -1;
    }
    return it->second->get_max_sources();
}


/* ===== Room Reverb Implementation ===== */

STEAMAUDIO_API RoomReverbHandle room_reverb_create() {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }
        
        RoomReverbHandle handle = allocate_reverb_handle();
        
        {
            std::lock_guard<std::mutex> lock(g_reverbs_mutex);
            g_reverbs[handle] = std::make_unique<RoomReverb>();
        }
        
        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void room_reverb_destroy(RoomReverbHandle handle) {
    std::lock_guard<std::mutex> lock(g_reverbs_mutex);
    g_reverbs.erase(handle);
}

STEAMAUDIO_API SteamAudioError room_reverb_set_params(
    RoomReverbHandle handle,
    float room_width,
    float room_height,
    float room_depth,
    float wall_absorption,
    float reverb_time) {
    
    try {
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        auto it = g_reverbs.find(handle);
        if (it == g_reverbs.end()) {
            g_last_error = "Invalid reverb handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->set_params(room_width, room_height, room_depth, wall_absorption, reverb_time)) {
            g_last_error = "Failed to set reverb parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError room_reverb_get_params(
    RoomReverbHandle handle,
    float* room_width,
    float* room_height,
    float* room_depth,
    float* wall_absorption,
    float* reverb_time) {
    
    try {
        if (!room_width || !room_height || !room_depth || !wall_absorption || !reverb_time) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        auto it = g_reverbs.find(handle);
        if (it == g_reverbs.end()) {
            g_last_error = "Invalid reverb handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->get_params(*room_width, *room_height, *room_depth, *wall_absorption, *reverb_time)) {
            g_last_error = "Failed to get reverb parameters";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError room_reverb_process(
    RoomReverbHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count) {
    
    try {
        if (!input_data || !output_data || !output_frame_count) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (input_frame_count <= 0) {
            g_last_error = "Invalid frame count";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        auto it = g_reverbs.find(handle);
        if (it == g_reverbs.end()) {
            g_last_error = "Invalid reverb handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->process(input_data, input_frame_count, output_data, *output_frame_count)) {
            g_last_error = "Reverb processing failed";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}


/* ===== Room Reverb Preset Implementation ===== */

STEAMAUDIO_API SteamAudioError room_reverb_set_preset(
    RoomReverbHandle handle,
    RoomPreset preset) {
    
    try {
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        auto it = g_reverbs.find(handle);
        if (it == g_reverbs.end()) {
            g_last_error = "Invalid reverb handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->set_preset(preset)) {
            g_last_error = "Failed to set reverb preset";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

/* ===== Direct Effect Implementation ===== */

STEAMAUDIO_API DirectEffectHandle direct_effect_create() {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }
        
        DirectEffectHandle handle = allocate_direct_effect_handle();
        
        {
            std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
            g_direct_effects[handle] = std::make_unique<DirectEffect>();
        }
        
        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void direct_effect_destroy(DirectEffectHandle handle) {
    std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
    g_direct_effects.erase(handle);
}

STEAMAUDIO_API SteamAudioError direct_effect_set_params(
    DirectEffectHandle handle,
    float distance,
    float occlusion,
    float transmission_low,
    float transmission_mid,
    float transmission_high,
    int flags) {
    
    try {
        std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
        auto it = g_direct_effects.find(handle);
        if (it == g_direct_effects.end()) {
            g_last_error = "Invalid direct effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->set_params(distance, occlusion, transmission_low, transmission_mid, transmission_high, flags)) {
            g_last_error = "Failed to set direct effect parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_effect_process(
    DirectEffectHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count) {
    
    try {
        if (!input_data || !output_data || !output_frame_count) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (input_frame_count <= 0) {
            g_last_error = "Invalid frame count";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
        auto it = g_direct_effects.find(handle);
        if (it == g_direct_effects.end()) {
            g_last_error = "Invalid direct effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }
        
        if (!it->second->process(input_data, input_frame_count, output_data, *output_frame_count)) {
            g_last_error = "Direct effect processing failed";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }
        
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}


} // extern "C"
