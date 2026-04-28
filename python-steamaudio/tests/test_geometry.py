"""Tests for geometry scene and direct simulation APIs."""

import ctypes
from unittest.mock import MagicMock, patch

import pytest
import steamaudio


class TestGeometryScene:
    def test_scene_creation_without_context(self):
        with pytest.raises(steamaudio.AudioProcessingError):
            steamaudio.GeometryScene()

    def test_scene_creation_and_commit(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                scene.commit()
                mock_lib.geometry_scene_commit.assert_called_once_with(2000000)

    def test_add_static_mesh(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.geometry_scene_add_static_mesh.return_value = 3000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                mesh = scene.add_static_mesh(
                    vertices=[
                        steamaudio.Vector3(0, 0, 0),
                        steamaudio.Vector3(1, 0, 0),
                        steamaudio.Vector3(0, 1, 0),
                    ],
                    triangles=[(0, 1, 2)],
                    material_indices=[0],
                    materials=[steamaudio.Material.preset("concrete")],
                )
                assert mesh is not None
                mock_lib.geometry_scene_add_static_mesh.assert_called_once()

    def test_add_static_mesh_rejects_out_of_range_material_index(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                with pytest.raises(steamaudio.InvalidParameterError, match="out of range"):
                    scene.add_static_mesh(
                        vertices=[
                            steamaudio.Vector3(0, 0, 0),
                            steamaudio.Vector3(1, 0, 0),
                            steamaudio.Vector3(0, 1, 0),
                        ],
                        triangles=[(0, 1, 2)],
                        material_indices=[1],
                        materials=[steamaudio.Material.preset("concrete")],
                    )


class TestDirectSimulator:
    def test_simulator_create_and_get_params(self):
        with patch("steamaudio.core.context.Context.is_initialized", return_value=True):
            mock_lib = MagicMock()
            mock_lib.geometry_scene_create.return_value = 2000000
            mock_lib.direct_simulator_create.return_value = 4000000

            def fill_params(handle, source_id, params):
                params.contents.flags = steamaudio.DIRECT_EFFECT_APPLY_OCCLUSION
                params.contents.occlusion = 0.75
                return None

            mock_lib.direct_simulator_get_direct_params.side_effect = fill_params

            with patch("steamaudio.bindings.loader.get_library", return_value=mock_lib):
                scene = steamaudio.GeometryScene()
                simulator = steamaudio.DirectSimulator(scene)
                simulator.add_source(7)
                simulator.set_listener(steamaudio.Vector3(0, 0, 0))
                simulator.set_source(
                    7,
                    steamaudio.Vector3(2, 0, 0),
                    direct_flags=steamaudio.DIRECT_EFFECT_APPLY_OCCLUSION,
                )
                simulator.run_direct()
                params = simulator.get_direct_params(7)
                assert params.occlusion == pytest.approx(0.75)
