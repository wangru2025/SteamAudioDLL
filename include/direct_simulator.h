#pragma once

#include <phonon.h>
#include <unordered_map>
#include "c_interface.h"

class DirectSimulator {
public:
    DirectSimulator(IPLScene scene, int max_sources);
    ~DirectSimulator();

    bool add_source(int source_id);
    bool remove_source(int source_id);
    bool set_listener(const DirectListenerParams& params);
    bool set_source(int source_id, const DirectSourceParams& params);
    bool run_direct();
    bool set_reflection_settings(const ReflectionSimulationSettings& settings);
    bool run_reflections();
    bool get_direct_params(int source_id, IPLDirectEffectParams& params);
    bool get_reflection_params(int source_id, IPLReflectionEffectParams& params);

private:
    struct SourceState {
        IPLSource source = nullptr;
    };

    IPLScene scene_ = nullptr;
    IPLSimulator simulator_ = nullptr;
    IPLSimulationSharedInputs shared_inputs_ = {};
    std::unordered_map<int, SourceState> sources_;
    bool pending_commit_ = false;

    void commit_if_needed();
    IPLCoordinateSpace3 to_coordinate_space(const CoordinateSpace& space) const;
};
