#include "direct_simulator.h"
#include "phonon_wrapper.h"
#include <stdexcept>

namespace {
constexpr IPLVector3 kDefaultAhead{0.0f, 0.0f, -1.0f};
constexpr IPLVector3 kDefaultUp{0.0f, 1.0f, 0.0f};
constexpr IPLVector3 kDefaultRight{1.0f, 0.0f, 0.0f};
}

DirectSimulator::DirectSimulator(IPLScene scene, int max_sources) {
    auto& phonon = PhononWrapper::instance();
    if (!phonon.is_initialized()) {
        throw std::runtime_error("Steam Audio not initialized");
    }

    scene_ = iplSceneRetain(scene);

    IPLSimulationSettings settings{};
    settings.flags = IPL_SIMULATIONFLAGS_DIRECT;
    settings.sceneType = IPL_SCENETYPE_DEFAULT;
    settings.reflectionType = IPL_REFLECTIONEFFECTTYPE_PARAMETRIC;
    settings.maxNumOcclusionSamples = 16;
    settings.maxNumSources = max_sources;
    settings.numThreads = 1;
    settings.rayBatchSize = 64;
    settings.samplingRate = phonon.get_audio_settings().samplingRate;
    settings.frameSize = phonon.get_audio_settings().frameSize;

    if (iplSimulatorCreate(phonon.get_context(), &settings, &simulator_) != IPL_STATUS_SUCCESS) {
        if (scene_) {
            iplSceneRelease(&scene_);
            scene_ = nullptr;
        }
        throw std::runtime_error("Failed to create direct simulator");
    }

    iplSimulatorSetScene(simulator_, scene_);
    pending_commit_ = true;

    shared_inputs_ = {};
    shared_inputs_.listener.origin = {0.0f, 0.0f, 0.0f};
    shared_inputs_.listener.ahead = kDefaultAhead;
    shared_inputs_.listener.up = kDefaultUp;
    shared_inputs_.listener.right = kDefaultRight;
}

DirectSimulator::~DirectSimulator() {
    for (auto& [_, state] : sources_) {
        if (state.source) {
            iplSourceRelease(&state.source);
        }
    }
    sources_.clear();

    if (simulator_) {
        iplSimulatorRelease(&simulator_);
    }

    if (scene_) {
        iplSceneRelease(&scene_);
    }
}

bool DirectSimulator::add_source(int source_id) {
    if (sources_.find(source_id) != sources_.end()) {
        return false;
    }

    IPLSourceSettings settings{};
    settings.flags = IPL_SIMULATIONFLAGS_DIRECT;

    SourceState state{};
    if (iplSourceCreate(simulator_, &settings, &state.source) != IPL_STATUS_SUCCESS) {
        return false;
    }

    iplSourceAdd(state.source, simulator_);
    sources_[source_id] = state;
    pending_commit_ = true;
    return true;
}

bool DirectSimulator::remove_source(int source_id) {
    auto it = sources_.find(source_id);
    if (it == sources_.end()) {
        return false;
    }

    iplSourceRemove(it->second.source, simulator_);
    iplSourceRelease(&it->second.source);
    sources_.erase(it);
    pending_commit_ = true;
    return true;
}

bool DirectSimulator::set_listener(const DirectListenerParams& params) {
    if (!simulator_) {
        return false;
    }

    shared_inputs_.listener = to_coordinate_space(params.listener);
    iplSimulatorSetSharedInputs(simulator_, IPL_SIMULATIONFLAGS_DIRECT, &shared_inputs_);
    return true;
}

bool DirectSimulator::set_source(int source_id, const DirectSourceParams& params) {
    auto it = sources_.find(source_id);
    if (it == sources_.end()) {
        return false;
    }

    IPLSimulationInputs inputs{};
    inputs.flags = IPL_SIMULATIONFLAGS_DIRECT;
    inputs.directFlags = static_cast<IPLDirectSimulationFlags>(params.direct_flags);
    if ((inputs.directFlags & IPL_DIRECTSIMULATIONFLAGS_TRANSMISSION) &&
        !(inputs.directFlags & IPL_DIRECTSIMULATIONFLAGS_OCCLUSION)) {
        inputs.directFlags = static_cast<IPLDirectSimulationFlags>(
            inputs.directFlags | IPL_DIRECTSIMULATIONFLAGS_OCCLUSION);
    }

    inputs.source = to_coordinate_space(params.source);
    inputs.distanceAttenuationModel.type = IPL_DISTANCEATTENUATIONTYPE_INVERSEDISTANCE;
    inputs.distanceAttenuationModel.minDistance = (params.min_distance > 0.0f) ? params.min_distance : 1.0f;
    inputs.airAbsorptionModel.type = IPL_AIRABSORPTIONTYPE_DEFAULT;
    inputs.directivity = {};
    inputs.directivity.dipoleWeight = 0.0f;
    inputs.directivity.dipolePower = 1.0f;
    inputs.occlusionType = (params.occlusion_type == SCENE_OCCLUSION_VOLUMETRIC)
        ? IPL_OCCLUSIONTYPE_VOLUMETRIC
        : IPL_OCCLUSIONTYPE_RAYCAST;
    inputs.occlusionRadius = (params.occlusion_radius > 0.0f) ? params.occlusion_radius : 1.0f;
    inputs.numOcclusionSamples = (params.num_occlusion_samples > 0) ? params.num_occlusion_samples : 16;
    inputs.numTransmissionRays = (params.num_transmission_rays > 0) ? params.num_transmission_rays : 8;

    iplSourceSetInputs(it->second.source, IPL_SIMULATIONFLAGS_DIRECT, &inputs);
    return true;
}

bool DirectSimulator::run_direct() {
    if (!simulator_) {
        return false;
    }

    commit_if_needed();
    iplSimulatorRunDirect(simulator_);
    return true;
}

bool DirectSimulator::get_direct_params(int source_id, IPLDirectEffectParams& params) {
    auto it = sources_.find(source_id);
    if (it == sources_.end()) {
        return false;
    }

    IPLSimulationOutputs outputs{};
    iplSourceGetOutputs(it->second.source, IPL_SIMULATIONFLAGS_DIRECT, &outputs);
    params = outputs.direct;
    return true;
}

void DirectSimulator::commit_if_needed() {
    if (!pending_commit_) {
        return;
    }

    iplSimulatorCommit(simulator_);
    pending_commit_ = false;
}

IPLCoordinateSpace3 DirectSimulator::to_coordinate_space(const CoordinateSpace& space) const {
    IPLCoordinateSpace3 result{};
    result.origin = {space.origin.x, space.origin.y, space.origin.z};

    IPLVector3 ahead = {space.ahead.x, space.ahead.y, space.ahead.z};
    IPLVector3 up = {space.up.x, space.up.y, space.up.z};
    if ((ahead.x == 0.0f) && (ahead.y == 0.0f) && (ahead.z == 0.0f)) {
        ahead = kDefaultAhead;
    }
    if ((up.x == 0.0f) && (up.y == 0.0f) && (up.z == 0.0f)) {
        up = kDefaultUp;
    }

    IPLVector3 right{};
    right.x = ahead.y * up.z - ahead.z * up.y;
    right.y = ahead.z * up.x - ahead.x * up.z;
    right.z = ahead.x * up.y - ahead.y * up.x;

    result.ahead = ahead;
    result.up = up;
    result.right = right;
    return result;
}
