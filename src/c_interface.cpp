#include "c_interface.h"
#include "phonon_wrapper.h"
#include "audio_processor.h"
#include "audio_mixer.h"
#include "geometry_scene.h"
#include "direct_simulator.h"
#include "room_reverb.h"
#include "direct_effect.h"
#include "reflection_effect.h"
#include <map>
#include <mutex>
#include <memory>

// Global state
static std::map<AudioProcessorHandle, std::unique_ptr<AudioProcessor>> g_processors;
static std::map<AudioMixerHandle, std::unique_ptr<AudioMixer>> g_mixers;
static std::map<GeometrySceneHandle, std::unique_ptr<GeometryScene>> g_geometry_scenes;
static std::map<StaticMeshHandle, std::unique_ptr<StaticMesh>> g_static_meshes;
static std::map<DirectSimulatorHandle, std::unique_ptr<DirectSimulator>> g_direct_simulators;
static std::map<RoomReverbHandle, std::unique_ptr<RoomReverb>> g_reverbs;
static std::map<DirectEffectHandle, std::unique_ptr<DirectEffect>> g_direct_effects;
static std::map<ReflectionEffectHandle, std::unique_ptr<ReflectionEffect>> g_reflection_effects;
static std::mutex g_processors_mutex;
static std::mutex g_mixers_mutex;
static std::mutex g_geometry_scenes_mutex;
static std::mutex g_static_meshes_mutex;
static std::mutex g_direct_simulators_mutex;
static std::mutex g_reverbs_mutex;
static std::mutex g_direct_effects_mutex;
static std::mutex g_reflection_effects_mutex;
static std::string g_last_error;

// Handle generation
static AudioProcessorHandle g_next_processor_handle = reinterpret_cast<AudioProcessorHandle>(1);
static AudioMixerHandle g_next_mixer_handle = reinterpret_cast<AudioMixerHandle>(1000000);
static GeometrySceneHandle g_next_geometry_scene_handle = reinterpret_cast<GeometrySceneHandle>(2000000);
static StaticMeshHandle g_next_static_mesh_handle = reinterpret_cast<StaticMeshHandle>(3000000);
static DirectSimulatorHandle g_next_direct_simulator_handle = reinterpret_cast<DirectSimulatorHandle>(4000000);
static RoomReverbHandle g_next_reverb_handle = reinterpret_cast<RoomReverbHandle>(5000000);
static DirectEffectHandle g_next_direct_effect_handle = reinterpret_cast<DirectEffectHandle>(6000000);
static ReflectionEffectHandle g_next_reflection_effect_handle = reinterpret_cast<ReflectionEffectHandle>(7000000);

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

ReflectionEffectHandle allocate_reflection_effect_handle() {
    ReflectionEffectHandle handle = g_next_reflection_effect_handle;
    g_next_reflection_effect_handle = reinterpret_cast<ReflectionEffectHandle>(reinterpret_cast<uintptr_t>(g_next_reflection_effect_handle) + 1);
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
        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        g_direct_simulators.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_static_meshes_mutex);
        g_static_meshes.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_geometry_scenes_mutex);
        g_geometry_scenes.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_reverbs_mutex);
        g_reverbs.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
        g_direct_effects.clear();
    }
    {
        std::lock_guard<std::mutex> lock(g_reflection_effects_mutex);
        g_reflection_effects.clear();
    }
    PhononWrapper::instance().shutdown();
}

GeometrySceneHandle allocate_geometry_scene_handle() {
    GeometrySceneHandle handle = g_next_geometry_scene_handle;
    g_next_geometry_scene_handle = reinterpret_cast<GeometrySceneHandle>(reinterpret_cast<uintptr_t>(g_next_geometry_scene_handle) + 1);
    return handle;
}

StaticMeshHandle allocate_static_mesh_handle() {
    StaticMeshHandle handle = g_next_static_mesh_handle;
    g_next_static_mesh_handle = reinterpret_cast<StaticMeshHandle>(reinterpret_cast<uintptr_t>(g_next_static_mesh_handle) + 1);
    return handle;
}

DirectSimulatorHandle allocate_direct_simulator_handle() {
    DirectSimulatorHandle handle = g_next_direct_simulator_handle;
    g_next_direct_simulator_handle = reinterpret_cast<DirectSimulatorHandle>(reinterpret_cast<uintptr_t>(g_next_direct_simulator_handle) + 1);
    return handle;
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

static IPLMaterial to_ipl_material(const AcousticMaterial& material) {
    IPLMaterial result{};
    result.absorption[0] = material.absorption_low;
    result.absorption[1] = material.absorption_mid;
    result.absorption[2] = material.absorption_high;
    result.scattering = material.scattering;
    result.transmission[0] = material.transmission_low;
    result.transmission[1] = material.transmission_mid;
    result.transmission[2] = material.transmission_high;
    return result;
}

/* ===== Geometry Scene Implementation ===== */

STEAMAUDIO_API GeometrySceneHandle geometry_scene_create() {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }

        GeometrySceneHandle handle = allocate_geometry_scene_handle();
        {
            std::lock_guard<std::mutex> lock(g_geometry_scenes_mutex);
            g_geometry_scenes[handle] = std::make_unique<GeometryScene>();
        }

        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void geometry_scene_destroy(GeometrySceneHandle handle) {
    std::lock_guard<std::mutex> lock(g_geometry_scenes_mutex);
    g_geometry_scenes.erase(handle);
}

STEAMAUDIO_API SteamAudioError geometry_scene_commit(GeometrySceneHandle handle) {
    try {
        std::lock_guard<std::mutex> lock(g_geometry_scenes_mutex);
        auto it = g_geometry_scenes.find(handle);
        if (it == g_geometry_scenes.end()) {
            g_last_error = "Invalid geometry scene handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        it->second->commit();
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API StaticMeshHandle geometry_scene_add_static_mesh(
    GeometrySceneHandle scene_handle,
    const Vector3* vertices,
    int num_vertices,
    const TriangleIndices* triangles,
    int num_triangles,
    const int* material_indices,
    int num_materials,
    const AcousticMaterial* materials) {

    try {
        if (!vertices || !triangles || !material_indices || !materials) {
            g_last_error = "Null pointer argument";
            return nullptr;
        }

        std::lock_guard<std::mutex> scene_lock(g_geometry_scenes_mutex);
        auto scene_it = g_geometry_scenes.find(scene_handle);
        if (scene_it == g_geometry_scenes.end()) {
            g_last_error = "Invalid geometry scene handle";
            return nullptr;
        }

        std::vector<IPLVector3> ipl_vertices(num_vertices);
        for (int i = 0; i < num_vertices; ++i) {
            ipl_vertices[i] = {vertices[i].x, vertices[i].y, vertices[i].z};
        }

        std::vector<IPLTriangle> ipl_triangles(num_triangles);
        for (int i = 0; i < num_triangles; ++i) {
            ipl_triangles[i].indices[0] = triangles[i].indices[0];
            ipl_triangles[i].indices[1] = triangles[i].indices[1];
            ipl_triangles[i].indices[2] = triangles[i].indices[2];
        }

        std::vector<IPLint32> ipl_material_indices(material_indices, material_indices + num_triangles);
        std::vector<IPLMaterial> ipl_materials(num_materials);
        for (int i = 0; i < num_materials; ++i) {
            ipl_materials[i] = to_ipl_material(materials[i]);
        }

        StaticMeshHandle mesh_handle = allocate_static_mesh_handle();
        {
            std::lock_guard<std::mutex> mesh_lock(g_static_meshes_mutex);
            g_static_meshes[mesh_handle] = std::make_unique<StaticMesh>(
                scene_it->second->get(),
                ipl_vertices,
                ipl_triangles,
                ipl_material_indices,
                ipl_materials
            );
        }

        return mesh_handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void geometry_static_mesh_destroy(StaticMeshHandle handle) {
    std::lock_guard<std::mutex> lock(g_static_meshes_mutex);
    g_static_meshes.erase(handle);
}

STEAMAUDIO_API SteamAudioError geometry_static_mesh_set_material(
    GeometrySceneHandle scene_handle,
    StaticMeshHandle mesh_handle,
    int material_index,
    const AcousticMaterial* material) {

    try {
        if (!material) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> scene_lock(g_geometry_scenes_mutex);
        auto scene_it = g_geometry_scenes.find(scene_handle);
        if (scene_it == g_geometry_scenes.end()) {
            g_last_error = "Invalid geometry scene handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> mesh_lock(g_static_meshes_mutex);
        auto mesh_it = g_static_meshes.find(mesh_handle);
        if (mesh_it == g_static_meshes.end()) {
            g_last_error = "Invalid static mesh handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        mesh_it->second->set_material(scene_it->second->get(), material_index, to_ipl_material(*material));
        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

/* ===== Direct Simulation Implementation ===== */

STEAMAUDIO_API DirectSimulatorHandle direct_simulator_create(
    GeometrySceneHandle scene_handle,
    int max_sources) {

    try {
        std::lock_guard<std::mutex> scene_lock(g_geometry_scenes_mutex);
        auto scene_it = g_geometry_scenes.find(scene_handle);
        if (scene_it == g_geometry_scenes.end()) {
            g_last_error = "Invalid geometry scene handle";
            return nullptr;
        }

        DirectSimulatorHandle handle = allocate_direct_simulator_handle();
        {
            std::lock_guard<std::mutex> sim_lock(g_direct_simulators_mutex);
            g_direct_simulators[handle] = std::make_unique<DirectSimulator>(scene_it->second->get(), max_sources);
        }

        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void direct_simulator_destroy(DirectSimulatorHandle handle) {
    std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
    g_direct_simulators.erase(handle);
}

STEAMAUDIO_API SteamAudioError direct_simulator_add_source(
    DirectSimulatorHandle handle,
    int source_id) {

    try {
        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->add_source(source_id)) {
            g_last_error = "Failed to add simulation source";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_remove_source(
    DirectSimulatorHandle handle,
    int source_id) {

    try {
        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->remove_source(source_id)) {
            g_last_error = "Simulation source not found";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_set_listener(
    DirectSimulatorHandle handle,
    const DirectListenerParams* params) {

    try {
        if (!params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->set_listener(*params)) {
            g_last_error = "Failed to set listener parameters";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_set_source(
    DirectSimulatorHandle handle,
    int source_id,
    const DirectSourceParams* params) {

    try {
        if (!params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->set_source(source_id, *params)) {
            g_last_error = "Failed to set source parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_run_direct(
    DirectSimulatorHandle handle) {

    try {
        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->run_direct()) {
            g_last_error = "Failed to run direct simulation";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_set_reflection_settings(
    DirectSimulatorHandle handle,
    const ReflectionSimulationSettings* settings) {

    try {
        if (!settings) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->set_reflection_settings(*settings)) {
            g_last_error = "Failed to set reflection simulation settings";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_run_reflections(
    DirectSimulatorHandle handle) {

    try {
        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->run_reflections()) {
            g_last_error = "Failed to run reflection simulation";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError direct_simulator_get_direct_params(
    DirectSimulatorHandle handle,
    int source_id,
    DirectSimulationParams* params) {

    try {
        if (!params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_direct_simulators_mutex);
        auto it = g_direct_simulators.find(handle);
        if (it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        IPLDirectEffectParams direct_params{};
        if (!it->second->get_direct_params(source_id, direct_params)) {
            g_last_error = "Failed to get direct simulation parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        params->flags = static_cast<int>(direct_params.flags);
        params->transmission_type = static_cast<int>(direct_params.transmissionType);
        params->distance_attenuation = direct_params.distanceAttenuation;
        params->air_absorption[0] = direct_params.airAbsorption[0];
        params->air_absorption[1] = direct_params.airAbsorption[1];
        params->air_absorption[2] = direct_params.airAbsorption[2];
        params->directivity = direct_params.directivity;
        params->occlusion = direct_params.occlusion;
        params->transmission[0] = direct_params.transmission[0];
        params->transmission[1] = direct_params.transmission[1];
        params->transmission[2] = direct_params.transmission[2];

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API ReflectionEffectHandle reflection_effect_create(
    int max_order,
    float max_duration) {
    try {
        if (!PhononWrapper::instance().is_initialized()) {
            g_last_error = "Steam Audio not initialized";
            return nullptr;
        }

        ReflectionEffectHandle handle = allocate_reflection_effect_handle();
        {
            std::lock_guard<std::mutex> lock(g_reflection_effects_mutex);
            g_reflection_effects[handle] = std::make_unique<ReflectionEffect>(max_order, max_duration);
        }

        return handle;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return nullptr;
    }
}

STEAMAUDIO_API void reflection_effect_destroy(ReflectionEffectHandle handle) {
    std::lock_guard<std::mutex> lock(g_reflection_effects_mutex);
    g_reflection_effects.erase(handle);
}

STEAMAUDIO_API SteamAudioError reflection_effect_set_listener(
    ReflectionEffectHandle handle,
    const DirectListenerParams* params) {

    try {
        if (!params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_reflection_effects_mutex);
        auto it = g_reflection_effects.find(handle);
        if (it == g_reflection_effects.end()) {
            g_last_error = "Invalid reflection effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->set_listener(*params)) {
            g_last_error = "Failed to set reflection listener";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError reflection_effect_set_simulation_output(
    ReflectionEffectHandle effect_handle,
    DirectSimulatorHandle simulator_handle,
    int source_id) {

    try {
        std::lock_guard<std::mutex> sim_lock(g_direct_simulators_mutex);
        auto sim_it = g_direct_simulators.find(simulator_handle);
        if (sim_it == g_direct_simulators.end()) {
            g_last_error = "Invalid direct simulator handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        IPLReflectionEffectParams reflection_params{};
        if (!sim_it->second->get_reflection_params(source_id, reflection_params)) {
            g_last_error = "Failed to get reflection simulation parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> effect_lock(g_reflection_effects_mutex);
        auto effect_it = g_reflection_effects.find(effect_handle);
        if (effect_it == g_reflection_effects.end()) {
            g_last_error = "Invalid reflection effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!effect_it->second->set_simulation_params(reflection_params)) {
            g_last_error = "Failed to set reflection simulation parameters";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
}

STEAMAUDIO_API SteamAudioError reflection_effect_process(
    ReflectionEffectHandle handle,
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

        std::lock_guard<std::mutex> lock(g_reflection_effects_mutex);
        auto it = g_reflection_effects.find(handle);
        if (it == g_reflection_effects.end()) {
            g_last_error = "Invalid reflection effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        if (!it->second->process(input_data, input_frame_count, output_data, *output_frame_count)) {
            g_last_error = "Reflection effect processing failed";
            return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
        }

        return STEAM_AUDIO_OK;
    } catch (const std::exception& e) {
        g_last_error = e.what();
        return STEAM_AUDIO_ERROR_PROCESSING_FAILED;
    }
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

STEAMAUDIO_API SteamAudioError direct_effect_set_simulation_params(
    DirectEffectHandle handle,
    const DirectSimulationParams* params) {

    try {
        if (!params) {
            g_last_error = "Null pointer argument";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        std::lock_guard<std::mutex> lock(g_direct_effects_mutex);
        auto it = g_direct_effects.find(handle);
        if (it == g_direct_effects.end()) {
            g_last_error = "Invalid direct effect handle";
            return STEAM_AUDIO_ERROR_INVALID_PARAM;
        }

        IPLDirectEffectParams direct_params{};
        direct_params.flags = static_cast<IPLDirectEffectFlags>(params->flags);
        direct_params.transmissionType = static_cast<IPLTransmissionType>(params->transmission_type);
        direct_params.distanceAttenuation = params->distance_attenuation;
        direct_params.airAbsorption[0] = params->air_absorption[0];
        direct_params.airAbsorption[1] = params->air_absorption[1];
        direct_params.airAbsorption[2] = params->air_absorption[2];
        direct_params.directivity = params->directivity;
        direct_params.occlusion = params->occlusion;
        direct_params.transmission[0] = params->transmission[0];
        direct_params.transmission[1] = params->transmission[1];
        direct_params.transmission[2] = params->transmission[2];

        if (!it->second->set_simulation_params(direct_params)) {
            g_last_error = "Failed to set direct simulation parameters";
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
