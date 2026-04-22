#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
    #ifdef STEAMAUDIO_BUILDING_DLL
        #define STEAMAUDIO_API __declspec(dllexport)
    #else
        #define STEAMAUDIO_API __declspec(dllimport)
    #endif
#else
    #define STEAMAUDIO_API
#endif

/* Opaque handle types */
typedef void* SteamAudioHandle;
typedef void* AudioProcessorHandle;

/* Error codes */
typedef enum {
    STEAM_AUDIO_OK = 0,
    STEAM_AUDIO_ERROR_INIT_FAILED = 1,
    STEAM_AUDIO_ERROR_INVALID_PARAM = 2,
    STEAM_AUDIO_ERROR_OUT_OF_MEMORY = 3,
    STEAM_AUDIO_ERROR_NOT_INITIALIZED = 4,
    STEAM_AUDIO_ERROR_PROCESSING_FAILED = 5
} SteamAudioError;

/* Audio format */
typedef struct {
    int sample_rate;
    int frame_size;
    int channels;
} AudioFormat;

/* 3D position and direction */
typedef struct {
    float x;
    float y;
    float z;
} Vector3;

/* Spatialization parameters */
typedef struct {
    Vector3 listener_pos;
    Vector3 listener_forward;
    Vector3 listener_up;
    Vector3 sound_pos;
    float min_distance;
    float max_distance;
    float rolloff;
    float directional_attenuation;
} SpatializationParams;

/* ===== Core Initialization ===== */

/* Initialize Steam Audio system */
STEAMAUDIO_API SteamAudioError steam_audio_init(int sample_rate, int frame_size);

/* Shutdown Steam Audio system */
STEAMAUDIO_API void steam_audio_shutdown();

/* Check if Steam Audio is initialized */
STEAMAUDIO_API int steam_audio_is_initialized();

/* ===== Audio Processor ===== */

/* Create audio processor for a single sound source */
STEAMAUDIO_API AudioProcessorHandle audio_processor_create(int input_channels, int output_channels);

/* Destroy audio processor */
STEAMAUDIO_API void audio_processor_destroy(AudioProcessorHandle handle);

/* Process audio with spatialization */
STEAMAUDIO_API SteamAudioError audio_processor_process(
    AudioProcessorHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count,
    const SpatializationParams* params
);

/* ===== Multi-Source Mixer ===== */

/* Opaque handle for multi-source mixer */
typedef void* AudioMixerHandle;

/* Create a multi-source mixer that can process multiple sound sources */
STEAMAUDIO_API AudioMixerHandle audio_mixer_create(int max_sources);

/* Destroy multi-source mixer */
STEAMAUDIO_API void audio_mixer_destroy(AudioMixerHandle handle);

/* Add a sound source to the mixer */
STEAMAUDIO_API SteamAudioError audio_mixer_add_source(
    AudioMixerHandle mixer_handle,
    int source_id,
    int input_channels
);

/* Remove a sound source from the mixer */
STEAMAUDIO_API SteamAudioError audio_mixer_remove_source(
    AudioMixerHandle mixer_handle,
    int source_id
);

/* Process multiple audio sources with spatialization and mix them */
STEAMAUDIO_API SteamAudioError audio_mixer_process(
    AudioMixerHandle mixer_handle,
    const int* source_ids,                   /* Source IDs for each input buffer */
    const float* const* input_data_array,  /* Array of input buffers, one per source */
    const int* input_frame_counts,         /* Frame count for each source */
    int num_sources,                       /* Number of sources in this batch */
    float* output_data,                    /* Mixed stereo output */
    int* output_frame_count,
    const SpatializationParams* params_array  /* Spatialization params for each source */
);

/* Get number of active sources in mixer */
STEAMAUDIO_API int audio_mixer_get_source_count(AudioMixerHandle mixer_handle);

/* Get maximum number of sources the mixer can handle */
STEAMAUDIO_API int audio_mixer_get_max_sources(AudioMixerHandle mixer_handle);

/* ===== HRTF Control ===== */

/* Enable/disable HRTF */
STEAMAUDIO_API SteamAudioError steam_audio_set_hrtf_enabled(int enabled);

/* Check if HRTF is enabled */
STEAMAUDIO_API int steam_audio_get_hrtf_enabled();

/* ===== Reverb Control ===== */

/* Enable/disable reverb */
STEAMAUDIO_API SteamAudioError steam_audio_set_reverb_enabled(int enabled);

/* Set reverb parameters */
STEAMAUDIO_API SteamAudioError steam_audio_set_reverb_params(
    float room_size,
    float damping,
    float width,
    float wet_level,
    float dry_level
);

/* ===== Room Reverb (Parametric) ===== */

/* Opaque handle for room reverb */
typedef void* RoomReverbHandle;

/* Room presets */
typedef enum {
    ROOM_PRESET_SMALL_ROOM = 0,      /* Small room (2x2x2m) */
    ROOM_PRESET_MEDIUM_ROOM = 1,     /* Medium room (5x4x3m) */
    ROOM_PRESET_LARGE_ROOM = 2,      /* Large room (10x8x4m) */
    ROOM_PRESET_SMALL_HALL = 3,      /* Small hall (15x10x5m) */
    ROOM_PRESET_LARGE_HALL = 4,      /* Large hall (30x20x10m) */
    ROOM_PRESET_CATHEDRAL = 5,       /* Cathedral (50x40x20m) */
    ROOM_PRESET_OUTDOOR = 6,         /* Outdoor (no reverb) */
} RoomPreset;

/* Create a room reverb effect with parametric reverb */
STEAMAUDIO_API RoomReverbHandle room_reverb_create();

/* Destroy room reverb */
STEAMAUDIO_API void room_reverb_destroy(RoomReverbHandle handle);

/* Set room reverb from preset */
STEAMAUDIO_API SteamAudioError room_reverb_set_preset(
    RoomReverbHandle handle,
    RoomPreset preset
);

/* Set room reverb parameters */
STEAMAUDIO_API SteamAudioError room_reverb_set_params(
    RoomReverbHandle handle,
    float room_width,      /* Room width in meters */
    float room_height,     /* Room height in meters */
    float room_depth,      /* Room depth in meters */
    float wall_absorption, /* Wall absorption coefficient (0.0-1.0) */
    float reverb_time      /* Reverb decay time in seconds (RT60) */
);

/* Get room reverb parameters */
STEAMAUDIO_API SteamAudioError room_reverb_get_params(
    RoomReverbHandle handle,
    float* room_width,
    float* room_height,
    float* room_depth,
    float* wall_absorption,
    float* reverb_time
);

/* Process audio through room reverb */
STEAMAUDIO_API SteamAudioError room_reverb_process(
    RoomReverbHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count
);

/* ===== Direct Effect (Occlusion & Transmission) ===== */

/* Opaque handle for direct effect */
typedef void* DirectEffectHandle;

/* Direct effect flags */
typedef enum {
    DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION = 1 << 0,
    DIRECT_EFFECT_APPLY_AIR_ABSORPTION = 1 << 1,
    DIRECT_EFFECT_APPLY_DIRECTIVITY = 1 << 2,
    DIRECT_EFFECT_APPLY_OCCLUSION = 1 << 3,
    DIRECT_EFFECT_APPLY_TRANSMISSION = 1 << 4,
} DirectEffectFlags;

/* Create a direct effect for occlusion and transmission */
STEAMAUDIO_API DirectEffectHandle direct_effect_create();

/* Destroy direct effect */
STEAMAUDIO_API void direct_effect_destroy(DirectEffectHandle handle);

/* Set direct effect parameters */
STEAMAUDIO_API SteamAudioError direct_effect_set_params(
    DirectEffectHandle handle,
    float distance,              /* Distance from source to listener */
    float occlusion,             /* Occlusion factor (0.0-1.0) */
    float transmission_low,      /* Transmission at low freq (0.0-1.0) */
    float transmission_mid,      /* Transmission at mid freq (0.0-1.0) */
    float transmission_high,     /* Transmission at high freq (0.0-1.0) */
    int flags                    /* DirectEffectFlags */
);

/* Process audio through direct effect */
STEAMAUDIO_API SteamAudioError direct_effect_process(
    DirectEffectHandle handle,
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int* output_frame_count
);

/* ===== Utility ===== */

/* Get last error message */
STEAMAUDIO_API const char* steam_audio_get_error_message();

/* Get version string */
STEAMAUDIO_API const char* steam_audio_get_version();

#ifdef __cplusplus
}
#endif
