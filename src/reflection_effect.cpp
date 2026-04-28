#include "reflection_effect.h"
#include "phonon_wrapper.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace {
constexpr IPLVector3 kDefaultAhead{0.0f, 0.0f, -1.0f};
constexpr IPLVector3 kDefaultUp{0.0f, 1.0f, 0.0f};
constexpr IPLVector3 kDefaultRight{1.0f, 0.0f, 0.0f};
}

ReflectionEffect::ReflectionEffect(int max_order, float max_duration)
    : max_order_(std::max(0, max_order))
    , max_duration_(std::max(0.1f, max_duration)) {
    if (!initialize_effects()) {
        throw std::runtime_error("Failed to initialize reflection effect");
    }
}

ReflectionEffect::~ReflectionEffect() {
    cleanup_effects();
}

bool ReflectionEffect::initialize_effects() {
    auto& phonon = PhononWrapper::instance();
    if (!phonon.is_initialized()) {
        return false;
    }

    IPLContext context = phonon.get_context();
    const auto& audio_settings = phonon.get_audio_settings();
    max_ir_size_ = std::max(audio_settings.frameSize, static_cast<int>(audio_settings.samplingRate * max_duration_));
    max_ir_channels_ = (max_order_ + 1) * (max_order_ + 1);
    current_order_ = max_order_;

    IPLReflectionEffectSettings reflection_settings{};
    reflection_settings.type = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    reflection_settings.irSize = max_ir_size_;
    reflection_settings.numChannels = max_ir_channels_;
    if (iplReflectionEffectCreate(context, const_cast<IPLAudioSettings*>(&audio_settings), &reflection_settings, &reflection_effect_) != IPL_STATUS_SUCCESS) {
        return false;
    }

    IPLAmbisonicsDecodeEffectSettings decode_settings{};
    decode_settings.speakerLayout = IPLSpeakerLayout{IPL_SPEAKERLAYOUTTYPE_STEREO};
    decode_settings.hrtf = phonon.get_hrtf();
    decode_settings.maxOrder = max_order_;
    if (iplAmbisonicsDecodeEffectCreate(context, const_cast<IPLAudioSettings*>(&audio_settings), &decode_settings, &decode_effect_) != IPL_STATUS_SUCCESS) {
        iplReflectionEffectRelease(&reflection_effect_);
        reflection_effect_ = nullptr;
        return false;
    }

    if (iplAudioBufferAllocate(context, 1, audio_settings.frameSize, &input_buffer_) != IPL_STATUS_SUCCESS) {
        cleanup_effects();
        return false;
    }
    if (iplAudioBufferAllocate(context, max_ir_channels_, audio_settings.frameSize, &reflections_buffer_) != IPL_STATUS_SUCCESS) {
        cleanup_effects();
        return false;
    }
    if (iplAudioBufferAllocate(context, 2, audio_settings.frameSize, &stereo_buffer_) != IPL_STATUS_SUCCESS) {
        cleanup_effects();
        return false;
    }

    reflection_params_ = {};
    reflection_params_.type = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    reflection_params_.numChannels = max_ir_channels_;
    reflection_params_.irSize = max_ir_size_;
    listener_.origin = {0.0f, 0.0f, 0.0f};
    listener_.ahead = kDefaultAhead;
    listener_.up = kDefaultUp;
    listener_.right = kDefaultRight;
    return true;
}

void ReflectionEffect::cleanup_effects() {
    auto& phonon = PhononWrapper::instance();
    if (phonon.is_initialized()) {
        iplAudioBufferFree(phonon.get_context(), &input_buffer_);
        iplAudioBufferFree(phonon.get_context(), &reflections_buffer_);
        iplAudioBufferFree(phonon.get_context(), &stereo_buffer_);
    }
    if (decode_effect_) {
        iplAmbisonicsDecodeEffectRelease(&decode_effect_);
        decode_effect_ = nullptr;
    }
    if (reflection_effect_) {
        iplReflectionEffectRelease(&reflection_effect_);
        reflection_effect_ = nullptr;
    }
}

bool ReflectionEffect::set_listener(const DirectListenerParams& params) {
    listener_ = to_coordinate_space(params.listener);
    return true;
}

bool ReflectionEffect::set_simulation_params(const IPLReflectionEffectParams& params) {
    reflection_params_ = params;
    reflection_params_.type = IPL_REFLECTIONEFFECTTYPE_CONVOLUTION;
    reflection_params_.numChannels = std::min(params.numChannels, max_ir_channels_);
    reflection_params_.irSize = std::min(params.irSize, max_ir_size_);
    current_order_ = std::max(0, static_cast<int>(std::lround(std::sqrt(static_cast<float>(std::max(1, reflection_params_.numChannels))) - 1.0f)));
    current_order_ = std::min(current_order_, max_order_);
    return true;
}

bool ReflectionEffect::process(
    const float* input_data,
    int input_frame_count,
    float* output_data,
    int& output_frame_count) {

    auto& phonon = PhononWrapper::instance();
    if (!phonon.is_initialized() || !reflection_effect_ || !decode_effect_) {
        return false;
    }

    const auto& audio_settings = phonon.get_audio_settings();
    int total_processed = 0;

    while (total_processed < input_frame_count) {
        int frames_to_process = std::min(static_cast<int>(audio_settings.frameSize), input_frame_count - total_processed);

        for (int i = 0; i < frames_to_process; ++i) {
            input_buffer_.data[0][i] = input_data[total_processed + i];
        }

        input_buffer_.numSamples = frames_to_process;
        reflections_buffer_.numSamples = frames_to_process;
        stereo_buffer_.numSamples = frames_to_process;

        iplReflectionEffectApply(
            reflection_effect_,
            &reflection_params_,
            &input_buffer_,
            &reflections_buffer_,
            nullptr
        );

        IPLAmbisonicsDecodeEffectParams decode_params{};
        decode_params.order = current_order_;
        decode_params.hrtf = phonon.get_hrtf();
        decode_params.orientation = listener_;
        decode_params.binaural = phonon.get_hrtf_enabled() ? IPL_TRUE : IPL_FALSE;

        iplAmbisonicsDecodeEffectApply(
            decode_effect_,
            &decode_params,
            &reflections_buffer_,
            &stereo_buffer_
        );

        for (int i = 0; i < frames_to_process; ++i) {
            output_data[(total_processed + i) * 2 + 0] = stereo_buffer_.data[0][i];
            output_data[(total_processed + i) * 2 + 1] = stereo_buffer_.data[1][i];
        }

        total_processed += frames_to_process;
    }

    output_frame_count = input_frame_count;
    return true;
}

IPLCoordinateSpace3 ReflectionEffect::to_coordinate_space(const CoordinateSpace& space) {
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
