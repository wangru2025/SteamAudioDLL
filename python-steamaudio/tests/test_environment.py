"""Tests for high-level audio environment APIs."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import steamaudio


class TestMaterialRegistry:
    def test_default_registry_contains_expected_materials(self):
        registry = steamaudio.MaterialRegistry.defaults()
        assert "concrete" in registry.list()
        material = registry.get("concrete")
        assert isinstance(material, steamaudio.Material)

    def test_register_and_resolve_custom_material(self):
        registry = steamaudio.MaterialRegistry()
        registry.register(
            "soft_wall",
            steamaudio.Material(0.2, 0.3, 0.4, 0.1, 0.0, 0.0, 0.0),
        )
        resolved = registry.resolve("soft_wall")
        assert resolved.absorption_mid == pytest.approx(0.3)


class TestGeometryHelpers:
    def test_add_box_delegates_to_static_mesh(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.geometry_scene_add_static_mesh.return_value = 3000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                mesh = scene.add_box(
                    steamaudio.Vector3(-1, -1, -1),
                    steamaudio.Vector3(1, 1, 1),
                    "concrete",
                )
                assert mesh is not None
                mock_lib.geometry_scene_add_static_mesh.assert_called_once()

    def test_add_room_delegates_to_static_mesh(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.geometry_scene_add_static_mesh.return_value = 3000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                scene.add_room(10.0, 3.0, 8.0, "plaster")
                mock_lib.geometry_scene_add_static_mesh.assert_called_once()

    def test_add_wall_with_doorway_delegates_to_static_mesh(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.geometry_scene_add_static_mesh.return_value = 3000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                scene.add_wall_with_doorway("x", 0.0, -5.0, 5.0, 3.0, "brick")
                mock_lib.geometry_scene_add_static_mesh.assert_called_once()


class TestAudioEnvironment:
    def test_environment_settings_are_available_as_main_entry_point(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                settings = steamaudio.EnvironmentSettings(
                    geometry=steamaudio.GeometrySettings(enabled=False),
                    direct=steamaudio.DirectSoundSettings(enabled=True),
                    indirect=steamaudio.IndirectSoundSettings(
                        enabled=True,
                        quality="high",
                        mix_level=0.6,
                    ),
                )
                env = steamaudio.AudioEnvironment(settings=settings)

                assert env.settings is settings
                assert env.geometry_enabled is False
                assert env.reflections_enabled is True
                assert env.settings.indirect.quality == "high"
                assert env.settings.indirect.mix_level == pytest.approx(0.6)

    def test_indirect_quality_presets_resolve_and_allow_overrides(self):
        settings = steamaudio.IndirectSoundSettings(quality="low")
        resolved = settings.resolved()
        assert resolved["num_rays"] == 256
        assert resolved["num_bounces"] == 8

        settings.num_rays = 777
        settings.duration = 1.25
        resolved = settings.resolved()
        assert resolved["num_rays"] == 777
        assert resolved["duration"] == pytest.approx(1.25)

    def test_environment_legacy_flags_do_not_override_explicit_settings_by_default(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                settings = steamaudio.EnvironmentSettings(
                    geometry=steamaudio.GeometrySettings(enabled=False),
                    indirect=steamaudio.IndirectSoundSettings(enabled=True),
                )
                env = steamaudio.AudioEnvironment(settings=settings)
                assert env.geometry_enabled is False
                assert env.reflections_enabled is True

    def test_environment_add_source_and_process(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.direct_effect_create.return_value = 6000000
            mock_lib.reflection_effect_create.return_value = 7000000

            def fill_params(handle, source_id, params):
                params.contents.occlusion = 0.5
                params.contents.distance_attenuation = 0.8
                return None

            mock_lib.direct_simulator_get_direct_params.side_effect = fill_params

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(max_sources=2)
                env.add_source(
                    1,
                    steamaudio.SourceConfig(position=steamaudio.Vector3(5, 0, 0)),
                )
                env.set_listener(steamaudio.Vector3(0, 0, 0))

                audio = np.zeros(32, dtype=np.float32)
                with patch.object(env._effects[1], "process", return_value=audio) as process_mock:
                    with patch.object(env.mixer, "process", return_value=np.zeros((32, 2), dtype=np.float32)) as mixer_mock:
                        output = env.process({1: audio})
                        assert output.shape == (32, 2)
                        process_mock.assert_called_once()
                        mixer_mock.assert_called_once()

    def test_environment_geometry_toggle_bypasses_simulation(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.direct_effect_create.return_value = 6000000
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(max_sources=1, geometry_enabled=False)
                env.add_source(
                    2,
                    steamaudio.SourceConfig(position=steamaudio.Vector3(1, 0, 0)),
                )
                with patch.object(env.mixer, "process", return_value=np.zeros((8, 2), dtype=np.float32)):
                    env.process({2: np.zeros(8, dtype=np.float32)})
                mock_lib.direct_simulator_run_direct.assert_not_called()

    def test_environment_geometry_helpers_delegate_to_scene(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment()
                env.scene.add_box = MagicMock(return_value="box")
                env.scene.add_room = MagicMock(return_value="room")
                env.scene.add_wall_with_doorway = MagicMock(return_value="wall")
                env.scene.commit = MagicMock()

                assert env.add_box((-1, -1, -1), (1, 1, 1), "concrete") == "box"
                assert env.add_room(10.0, 3.0, 8.0, "plaster") == "room"
                assert (
                    env.add_wall_with_doorway("x", 0.0, -5.0, 5.0, 3.0, "brick")
                    == "wall"
                )
                env.commit_geometry()

                env.scene.add_box.assert_called_once_with(
                    (-1, -1, -1),
                    (1, 1, 1),
                    "concrete",
                )
                env.scene.add_room.assert_called_once_with(
                    10.0,
                    3.0,
                    8.0,
                    "plaster",
                    floor_material=None,
                    ceiling_material=None,
                    center=steamaudio.Vector3(0.0, 0.0, 0.0),
                )
                env.scene.add_wall_with_doorway.assert_called_once_with(
                    "x",
                    0.0,
                    -5.0,
                    5.0,
                    3.0,
                    "brick",
                    doorway_center=0.0,
                    doorway_half_width=1.0,
                    doorway_height=2.5,
                )
                env.scene.commit.assert_called_once_with()

    def test_environment_update_sources_supports_partial_and_replace(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.direct_effect_create.return_value = 6000000
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(max_sources=2)
                env.add_source(
                    1,
                    steamaudio.SourceConfig(position=steamaudio.Vector3(1, 0, 0)),
                )
                env.add_source(
                    2,
                    steamaudio.SourceConfig(position=steamaudio.Vector3(2, 0, 0)),
                )

                env.update_sources(
                    {
                        1: {"position": steamaudio.Vector3(3, 0, 0), "min_distance": 0.5},
                        2: steamaudio.SourceConfig(
                            position=steamaudio.Vector3(4, 0, 0),
                            min_distance=2.0,
                            input_channels=1,
                        ),
                    }
                )

                assert env._sources[1].position == steamaudio.Vector3(3, 0, 0)
                assert env._sources[1].min_distance == pytest.approx(0.5)
                assert env._sources[2].position == steamaudio.Vector3(4, 0, 0)
                assert env._sources[2].min_distance == pytest.approx(2.0)

    def test_environment_rejects_input_channel_update(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.direct_effect_create.return_value = 6000000
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(max_sources=1)
                env.add_source(
                    1,
                    steamaudio.SourceConfig(
                        position=steamaudio.Vector3(1, 0, 0),
                        input_channels=1,
                    ),
                )

                with pytest.raises(steamaudio.InvalidParameterError, match="cannot be changed"):
                    env.update_source(1, input_channels=2)

                with pytest.raises(steamaudio.InvalidParameterError, match="cannot be changed"):
                    env.update_sources(
                        {
                            1: steamaudio.SourceConfig(
                                position=steamaudio.Vector3(2, 0, 0),
                                input_channels=2,
                            )
                        }
                    )

    def test_environment_rejects_invalid_input_channels_on_add(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.reflection_effect_create.return_value = 7000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(max_sources=1)
                with pytest.raises(steamaudio.InvalidParameterError, match="must be 1 or 2"):
                    env.add_source(
                        1,
                        steamaudio.SourceConfig(
                            position=steamaudio.Vector3(1, 0, 0),
                            input_channels=3,
                        ),
                    )

    def test_environment_reflections_mix_into_output(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000
            mock_lib.direct_effect_create.return_value = 6000000
            mock_lib.reflection_effect_create.return_value = 7000000

            def fill_params(handle, source_id, params):
                params.contents.occlusion = 0.2
                params.contents.distance_attenuation = 0.9
                return None

            mock_lib.direct_simulator_get_direct_params.side_effect = fill_params

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                env = steamaudio.AudioEnvironment(
                    max_sources=1,
                    reflections_enabled=True,
                )
                env.add_source(
                    1,
                    steamaudio.SourceConfig(position=steamaudio.Vector3(5, 0, 0)),
                )
                env.set_listener(steamaudio.Vector3(0, 0, 0))
                env._reflection_effect_signature = (1, 1.5)

                direct_mix = np.ones((16, 2), dtype=np.float32)
                reflected = np.full((16, 2), 0.25, dtype=np.float32)
                audio = np.zeros(16, dtype=np.float32)

                with patch.object(env._effects[1], "process", return_value=audio):
                    with patch.object(env.mixer, "process", return_value=direct_mix):
                        with patch.object(
                            env._reflection_effects[1],
                            "process",
                            return_value=reflected,
                        ):
                            output = env.process({1: audio})

                np.testing.assert_allclose(output, direct_mix + reflected)
                mock_lib.direct_simulator_run_reflections.assert_called_once_with(4000000)

    def test_environment_can_override_settings_with_legacy_flags(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000
            mock_lib.audio_mixer_create.return_value = 1000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                settings = steamaudio.EnvironmentSettings(
                    geometry=steamaudio.GeometrySettings(enabled=False),
                    indirect=steamaudio.IndirectSoundSettings(enabled=False),
                )
                env = steamaudio.AudioEnvironment(
                    settings=settings,
                    geometry_enabled=True,
                    reflections_enabled=True,
                )
                assert env.geometry_enabled is True
                assert env.reflections_enabled is True
