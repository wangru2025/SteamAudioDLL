#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用 AudioEnvironment 的交互式 3D 音频演示。"""

from __future__ import annotations

import queue
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyaudio
import pygame
import soundfile as sf
import wx

sys.path.insert(0, str(Path(__file__).parent.parent / "python-steamaudio"))

import steamaudio


ROOM_WIDTH = 40.0
ROOM_HEIGHT = 4.0
ROOM_DEPTH = 30.0

MATERIAL_PRESETS = {
    "灰泥": "plaster",
    "混凝土": "concrete",
    "木材": "wood",
    "玻璃": "glass",
    "金属": "metal",
    "砖墙": "brick",
}

REVERB_PRESETS = [
    ("小房间", steamaudio.RoomReverb.PRESET_SMALL_ROOM),
    ("中等房间", steamaudio.RoomReverb.PRESET_MEDIUM_ROOM),
    ("大房间", steamaudio.RoomReverb.PRESET_LARGE_ROOM),
    ("小礼堂", steamaudio.RoomReverb.PRESET_SMALL_HALL),
    ("大礼堂", steamaudio.RoomReverb.PRESET_LARGE_HALL),
    ("大教堂", steamaudio.RoomReverb.PRESET_CATHEDRAL),
    ("室外", steamaudio.RoomReverb.PRESET_OUTDOOR),
]


@dataclass
class GeometrySettings:
    geometry_enabled: bool = True
    reflections_enabled: bool = True
    transmission_enabled: bool = False
    occlusion_mode: int = steamaudio.SCENE_OCCLUSION_RAYCAST
    occlusion_radius: float = 1.0
    occlusion_samples: int = 16
    transmission_rays: int = 8
    doorway_half_width: float = 1.2
    reflection_num_rays: int = 1024
    reflection_num_bounces: int = 16
    reflection_duration: float = 1.5
    divider_material_key: str = "混凝土"


class GeometrySettingsDialog(wx.Dialog):
    """几何参数设置对话框。"""

    def __init__(self, parent, settings: GeometrySettings):
        super().__init__(parent, title="几何设置", size=(420, 420))

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(0, 2, 8, 8)

        self.geometry_enabled = wx.CheckBox(panel, label="启用几何应用")
        self.geometry_enabled.SetValue(settings.geometry_enabled)
        self.reflections_enabled = wx.CheckBox(panel, label="启用反射")
        self.reflections_enabled.SetValue(settings.reflections_enabled)
        self.transmission_enabled = wx.CheckBox(panel, label="启用透射")
        self.transmission_enabled.SetValue(settings.transmission_enabled)

        self.occlusion_mode = wx.Choice(panel, choices=["射线遮挡", "体积遮挡"])
        self.occlusion_mode.SetSelection(
            0 if settings.occlusion_mode == steamaudio.SCENE_OCCLUSION_RAYCAST else 1
        )
        self.occlusion_radius = wx.SpinCtrlDouble(
            panel, min=0.1, max=5.0, initial=settings.occlusion_radius, inc=0.1
        )
        self.occlusion_samples = wx.SpinCtrl(
            panel, min=1, max=128, initial=settings.occlusion_samples
        )
        self.transmission_rays = wx.SpinCtrl(
            panel, min=1, max=64, initial=settings.transmission_rays
        )
        self.doorway_half_width = wx.SpinCtrlDouble(
            panel, min=0.5, max=8.0, initial=settings.doorway_half_width, inc=0.1
        )
        self.reflection_num_rays = wx.SpinCtrl(
            panel, min=64, max=4096, initial=settings.reflection_num_rays
        )
        self.reflection_num_bounces = wx.SpinCtrl(
            panel, min=1, max=64, initial=settings.reflection_num_bounces
        )
        self.reflection_duration = wx.SpinCtrlDouble(
            panel, min=0.1, max=4.0, initial=settings.reflection_duration, inc=0.1
        )
        self.divider_material = wx.Choice(panel, choices=list(MATERIAL_PRESETS.keys()))
        self.divider_material.SetStringSelection(settings.divider_material_key)

        rows = [
            ("遮挡模式", self.occlusion_mode),
            ("遮挡半径", self.occlusion_radius),
            ("遮挡采样数", self.occlusion_samples),
            ("透射射线数", self.transmission_rays),
            ("门洞半宽", self.doorway_half_width),
            ("反射射线数", self.reflection_num_rays),
            ("反射反弹数", self.reflection_num_bounces),
            ("反射时长", self.reflection_duration),
            ("隔墙材质", self.divider_material),
        ]
        for label, control in rows:
            grid.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            grid.Add(control, 1, wx.EXPAND)

        grid.AddGrowableCol(1, 1)
        sizer.Add(self.geometry_enabled, 0, wx.ALL, 10)
        sizer.Add(self.reflections_enabled, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer.Add(self.transmission_enabled, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 10)

        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        panel.SetSizer(sizer)
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizerAndFit(top_sizer)

    def get_settings(self) -> GeometrySettings:
        return GeometrySettings(
            geometry_enabled=self.geometry_enabled.GetValue(),
            reflections_enabled=self.reflections_enabled.GetValue(),
            transmission_enabled=self.transmission_enabled.GetValue(),
            occlusion_mode=(
                steamaudio.SCENE_OCCLUSION_RAYCAST
                if self.occlusion_mode.GetSelection() == 0
                else steamaudio.SCENE_OCCLUSION_VOLUMETRIC
            ),
            occlusion_radius=self.occlusion_radius.GetValue(),
            occlusion_samples=self.occlusion_samples.GetValue(),
            transmission_rays=self.transmission_rays.GetValue(),
            doorway_half_width=self.doorway_half_width.GetValue(),
            reflection_num_rays=self.reflection_num_rays.GetValue(),
            reflection_num_bounces=self.reflection_num_bounces.GetValue(),
            reflection_duration=self.reflection_duration.GetValue(),
            divider_material_key=self.divider_material.GetStringSelection(),
        )


class AudioThread(threading.Thread):
    """后台线程：负责模拟、处理和播放音频。"""

    def __init__(self, audio_data_list, sample_rate, listener_queue, stop_event, status_callback):
        super().__init__(daemon=True)
        self.audio_data_list = audio_data_list
        self.sample_rate = sample_rate
        self.listener_queue = listener_queue
        self.stop_event = stop_event
        self.status_callback = status_callback
        self.chunk_size = 256
        self.current_positions = [0, 0]
        self.listener_pos = [-12.0, 0.0]
        self.listener_ahead = steamaudio.Vector3(1.0, 0.0, 0.0)
        self.sound_positions = [[-14.0, -6.0], [14.0, 0.0]]
        self.reverb_enabled = False
        self.current_preset = steamaudio.RoomReverb.PRESET_MEDIUM_ROOM
        self.last_occlusion = [0.0, 0.0]
        self.geometry_settings = GeometrySettings()
        self._settings_lock = threading.Lock()
        self._scene_dirty = True
        self.environment = None
        self.reverb = None

    def update_geometry_settings(self, settings: GeometrySettings):
        with self._settings_lock:
            self.geometry_settings = settings
            self._scene_dirty = True

    def toggle_geometry(self):
        with self._settings_lock:
            self.geometry_settings.geometry_enabled = not self.geometry_settings.geometry_enabled
            if self.environment:
                self.environment.settings.geometry.enabled = self.geometry_settings.geometry_enabled
            return self.geometry_settings.geometry_enabled

    def toggle_reflections(self):
        with self._settings_lock:
            self.geometry_settings.reflections_enabled = not self.geometry_settings.reflections_enabled
            if self.environment:
                self.environment.settings.indirect.enabled = self.geometry_settings.reflections_enabled
            return self.geometry_settings.reflections_enabled

    def set_reverb_preset(self, preset: int):
        self.current_preset = preset
        if self.reverb:
            self.reverb.set_preset(preset)

    def snapshot_settings(self):
        with self._settings_lock:
            return GeometrySettings(**self.geometry_settings.__dict__)

    def _rebuild_environment(self, settings: GeometrySettings):
        if self.environment:
            self.environment._cleanup()
        env_settings = steamaudio.EnvironmentSettings(
            geometry=steamaudio.GeometrySettings(enabled=settings.geometry_enabled),
            direct=steamaudio.DirectSoundSettings(enabled=True),
            indirect=steamaudio.IndirectSoundSettings(
                enabled=settings.reflections_enabled,
                quality="medium",
                mix_level=0.45,
                num_rays=settings.reflection_num_rays,
                num_bounces=settings.reflection_num_bounces,
                duration=settings.reflection_duration,
                order=1,
            ),
        )
        self.environment = steamaudio.AudioEnvironment(
            max_sources=8,
            settings=env_settings,
        )
        self.environment.add_room(
            ROOM_WIDTH,
            ROOM_HEIGHT,
            ROOM_DEPTH,
            wall_material="plaster",
        )
        self.environment.add_wall_with_doorway(
            axis="x",
            offset=0.0,
            min_extent=-ROOM_DEPTH / 2,
            max_extent=ROOM_DEPTH / 2,
            height=ROOM_HEIGHT,
            material=MATERIAL_PRESETS[settings.divider_material_key],
            doorway_center=0.0,
            doorway_half_width=settings.doorway_half_width,
            doorway_height=2.5,
        )
        self.environment.commit_geometry()

        for source_id, position in enumerate(self.sound_positions):
            direct_flags = (
                steamaudio.DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION
                | steamaudio.DIRECT_EFFECT_APPLY_AIR_ABSORPTION
                | steamaudio.DIRECT_EFFECT_APPLY_OCCLUSION
            )
            if settings.transmission_enabled:
                direct_flags |= steamaudio.DIRECT_EFFECT_APPLY_TRANSMISSION

            self.environment.add_source(
                source_id,
                steamaudio.SourceConfig(
                    position=steamaudio.Vector3(position[0], 0.0, position[1]),
                    min_distance=0.5,
                    direct_flags=direct_flags,
                    occlusion_type=settings.occlusion_mode,
                    occlusion_radius=settings.occlusion_radius,
                    num_occlusion_samples=settings.occlusion_samples,
                    num_transmission_rays=settings.transmission_rays,
                ),
            )

    def run(self):
        p = None
        stream = None
        try:
            with steamaudio.Context(sample_rate=self.sample_rate, frame_size=self.chunk_size):
                self.reverb = steamaudio.RoomReverb()
                self.reverb.set_preset(self.current_preset)

                p = pyaudio.PyAudio()
                stream = p.open(
                    format=pyaudio.paFloat32,
                    channels=2,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=self.chunk_size,
                )

                last_signature = None

                while not self.stop_event.is_set():
                    try:
                        state = self.listener_queue.get_nowait()
                        self.listener_pos = state["position"]
                        self.listener_ahead = state["ahead"]
                    except queue.Empty:
                        pass

                    settings = self.snapshot_settings()
                    signature = (
                        settings.geometry_enabled,
                        settings.transmission_enabled,
                        settings.occlusion_mode,
                        round(settings.occlusion_radius, 3),
                        settings.occlusion_samples,
                        settings.transmission_rays,
                        round(settings.doorway_half_width, 3),
                        settings.reflections_enabled,
                        settings.reflection_num_rays,
                        settings.reflection_num_bounces,
                        round(settings.reflection_duration, 3),
                        settings.divider_material_key,
                    )
                    if self._scene_dirty or signature != last_signature or self.environment is None:
                        self._scene_dirty = False
                        last_signature = signature
                        self._rebuild_environment(settings)

                    self.environment.set_listener(
                        steamaudio.Vector3(self.listener_pos[0], 0.0, self.listener_pos[1]),
                        ahead=self.listener_ahead,
                    )

                    direct_flags = (
                        steamaudio.DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION
                        | steamaudio.DIRECT_EFFECT_APPLY_AIR_ABSORPTION
                        | steamaudio.DIRECT_EFFECT_APPLY_OCCLUSION
                    )
                    if settings.transmission_enabled:
                        direct_flags |= steamaudio.DIRECT_EFFECT_APPLY_TRANSMISSION
                    self.environment.update_sources(
                        {
                            source_id: {
                                "position": steamaudio.Vector3(position[0], 0.0, position[1]),
                                "direct_flags": direct_flags,
                                "occlusion_type": settings.occlusion_mode,
                                "occlusion_radius": settings.occlusion_radius,
                                "num_occlusion_samples": settings.occlusion_samples,
                                "num_transmission_rays": settings.transmission_rays,
                            }
                            for source_id, position in enumerate(self.sound_positions)
                        }
                    )

                    sources_data = {}
                    for source_id in range(2):
                        start = self.current_positions[source_id]
                        end = min(start + self.chunk_size, len(self.audio_data_list[source_id]))
                        chunk = self.audio_data_list[source_id][start:end]
                        self.current_positions[source_id] = (
                            0 if end >= len(self.audio_data_list[source_id]) else end
                        )
                        if len(chunk) < self.chunk_size:
                            chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)), mode="constant")
                        sources_data[source_id] = chunk.astype(np.float32)

                    output_chunk = self.environment.process(sources_data)

                    for source_id in range(2):
                        params = self.environment.get_last_direct_params(source_id)
                        self.last_occlusion[source_id] = float(params.occlusion) if params else 0.0

                    if self.reverb_enabled:
                        interleaved = output_chunk.flatten("C")
                        reverb_output = self.reverb.process(interleaved)
                        output_chunk = (interleaved * 0.5 + reverb_output * 0.5).reshape(-1, 2)

                    output_chunk = np.clip(output_chunk, -1.0, 1.0)
                    stream.write(output_chunk.astype(np.float32).tobytes())

                    if self.status_callback:
                        self.status_callback(
                            self.listener_pos,
                            self.sound_positions,
                            self.last_occlusion,
                            settings,
                        )
        except Exception as exc:
            print(f"音频线程错误: {exc}")
            import traceback
            traceback.print_exc()
        finally:
            if stream is not None:
                try:
                    if stream.is_active():
                        stream.stop_stream()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
            if p is not None:
                try:
                    p.terminate()
                except Exception:
                    pass
            if self.environment:
                self.environment._cleanup()
                self.environment = None


class ScenePanel(wx.Panel):
    """房间与声源的 2D 俯视图。"""

    PANEL_SIZE = 440

    def __init__(self, parent):
        super().__init__(parent, size=(self.PANEL_SIZE, self.PANEL_SIZE))
        self.listener_pos = [-12.0, 0.0]
        self.listener_ahead = steamaudio.Vector3(1.0, 0.0, 0.0)
        self.sound_positions = [[-14.0, -6.0], [14.0, 0.0]]
        self.occlusion = [0.0, 0.0]
        self.settings = GeometrySettings()
        self.zoom = 10.0
        self.SetBackgroundColour(wx.Colour(24, 24, 28))
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def on_paint(self, _):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(wx.Colour(24, 24, 28)))
        dc.Clear()

        center_x = self.PANEL_SIZE // 2
        center_y = self.PANEL_SIZE // 2

        def to_screen(x, z):
            return int(center_x + x * self.zoom), int(center_y + z * self.zoom)

        left_top = to_screen(-ROOM_WIDTH / 2, -ROOM_DEPTH / 2)
        right_bottom = to_screen(ROOM_WIDTH / 2, ROOM_DEPTH / 2)
        dc.SetPen(wx.Pen(wx.Colour(150, 150, 150), 2))
        dc.DrawRectangle(
            left_top[0],
            left_top[1],
            right_bottom[0] - left_top[0],
            right_bottom[1] - left_top[1],
        )

        door_half_width = self.settings.doorway_half_width
        divider_color = (
            wx.Colour(220, 160, 60) if self.settings.geometry_enabled else wx.Colour(100, 100, 100)
        )
        dc.SetPen(wx.Pen(divider_color, 3))
        dc.DrawLine(*to_screen(0.0, -ROOM_DEPTH / 2), *to_screen(0.0, -door_half_width))
        dc.DrawLine(*to_screen(0.0, door_half_width), *to_screen(0.0, ROOM_DEPTH / 2))
        dc.SetPen(wx.Pen(wx.Colour(70, 180, 120), 3))
        dc.DrawLine(*to_screen(0.0, -door_half_width), *to_screen(0.0, door_half_width))

        colors = [wx.Colour(220, 70, 70), wx.Colour(70, 220, 140)]
        for i, (sound_pos, color) in enumerate(zip(self.sound_positions, colors)):
            x, y = to_screen(sound_pos[0], sound_pos[1])
            dc.SetBrush(wx.Brush(color))
            dc.SetPen(wx.Pen(color, 2))
            dc.DrawCircle(x, y, 8)
            dc.SetTextForeground(color)
            dc.DrawText(f"声源{i + 1} 遮挡={self.occlusion[i]:.2f}", x + 10, y - 10)

        lx, ly = to_screen(self.listener_pos[0], self.listener_pos[1])
        dc.SetBrush(wx.Brush(wx.Colour(80, 130, 255)))
        dc.SetPen(wx.Pen(wx.Colour(80, 130, 255), 2))
        dc.DrawCircle(lx, ly, 8)
        ahead_end = to_screen(
            self.listener_pos[0] + self.listener_ahead.x * 1.5,
            self.listener_pos[1] + self.listener_ahead.z * 1.5,
        )
        dc.DrawLine(lx, ly, ahead_end[0], ahead_end[1])

        dc.SetTextForeground(wx.Colour(220, 220, 220))
        dc.DrawText("方向键：移动听者", 10, 10)
        dc.DrawText("空格：开关混响  F3：混响预设", 10, 30)
        dc.DrawText("F4：几何设置  F5：几何开关  F6：反射开关", 10, 50)
        dc.DrawText(
            f"反射：{'开' if self.settings.reflections_enabled else '关'}  隔墙材质：{self.settings.divider_material_key}",
            10,
            70,
        )

    def update_state(self, listener_pos, sound_positions, occlusion, settings: GeometrySettings):
        self.listener_pos = listener_pos
        self.sound_positions = sound_positions
        self.occlusion = occlusion
        self.settings = settings
        self.Refresh()


class MainFrame(wx.Frame):
    """主演示窗口。"""

    def __init__(self):
        super().__init__(None, title="Steam Audio 几何场景演示", size=(560, 680))

        pygame.mixer.init()
        self.footstep_sound = None

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Steam Audio 几何场景 / 材质演示")
        font = title.GetFont()
        font.PointSize = 14
        font.Weight = wx.FONTWEIGHT_BOLD
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)

        self.scene_panel = ScenePanel(panel)
        sizer.Add(self.scene_panel, 1, wx.ALL | wx.CENTER, 10)

        self.info = wx.StaticText(
            panel,
            label=(
                "听者初始位于房间左侧。\n"
                "声源 2 默认在隔墙正后方，初始状态下会被明显遮挡。\n"
                "F3 可以切换混响预设，空格可以实时开关混响。\n"
                "F4 可以实时调整门洞宽度、材质、遮挡、透射和反射参数。\n"
                "F5 可以开关几何，F6 可以单独开关场景反射。"
            ),
        )
        sizer.Add(self.info, 0, wx.ALL | wx.EXPAND, 10)

        panel.SetSizer(sizer)
        self.CreateStatusBar()
        self.SetStatusText("正在加载演示...")

        self.stop_event = threading.Event()
        self.listener_queue = queue.Queue(maxsize=1)
        self.audio_thread = None
        self.listener_pos = [-12.0, 0.0]
        self.listener_ahead = steamaudio.Vector3(1.0, 0.0, 0.0)
        self.geometry_settings = GeometrySettings()

        self._load_audio()

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetFocus()

    def _load_audio(self):
        demo_dir = Path(__file__).parent
        audio_paths = [demo_dir / "1.ogg", demo_dir / "3.ogg"]
        footstep_path = demo_dir / "2.ogg"

        try:
            audio_data_list = []
            sample_rate = 44100
            for path in audio_paths:
                data, sample_rate = sf.read(str(path), dtype="float32")
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                audio_data_list.append(data.astype(np.float32))

            if footstep_path.exists():
                self.footstep_sound = pygame.mixer.Sound(str(footstep_path))

            self.audio_thread = AudioThread(
                audio_data_list,
                sample_rate,
                self.listener_queue,
                self.stop_event,
                self.on_audio_status_update,
            )
            self.audio_thread.update_geometry_settings(self.geometry_settings)
            self.audio_thread.start()
            self._push_listener_state()
            self.SetStatusText("几何场景演示运行中")
        except Exception as exc:
            wx.MessageBox(f"加载演示音频失败：\n{exc}", "错误", wx.OK | wx.ICON_ERROR)
            self.SetStatusText("音频加载失败")

    def _push_listener_state(self):
        state = {"position": self.listener_pos.copy(), "ahead": self.listener_ahead}
        try:
            self.listener_queue.put_nowait(state)
        except queue.Full:
            try:
                self.listener_queue.get_nowait()
            except queue.Empty:
                pass
            self.listener_queue.put_nowait(state)

    def on_audio_status_update(self, listener_pos, sound_positions, occlusion, settings):
        wx.CallAfter(self.scene_panel.update_state, listener_pos, sound_positions, occlusion, settings)
        wx.CallAfter(
            self.SetStatusText,
            f"听者=({listener_pos[0]:.1f}, {listener_pos[1]:.1f}) | "
            f"几何={'开' if settings.geometry_enabled else '关'} | "
            f"反射={'开' if settings.reflections_enabled else '关'} | "
            f"遮挡 声源1={occlusion[0]:.2f} 声源2={occlusion[1]:.2f}",
        )

    def show_geometry_settings_dialog(self):
        dlg = GeometrySettingsDialog(self, self.geometry_settings)
        if dlg.ShowModal() == wx.ID_OK:
            self.geometry_settings = dlg.get_settings()
            if self.audio_thread:
                self.audio_thread.update_geometry_settings(self.geometry_settings)
            self.scene_panel.settings = self.geometry_settings
            self.scene_panel.Refresh()
            self.SetStatusText("几何设置已更新")
        dlg.Destroy()

    def show_reverb_preset_dialog(self):
        labels = [name for name, _ in REVERB_PRESETS]
        dlg = wx.SingleChoiceDialog(self, "选择混响预设：", "混响预设", labels)
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetSelection()
            preset_name, preset_value = REVERB_PRESETS[selection]
            if self.audio_thread:
                self.audio_thread.set_reverb_preset(preset_value)
            self.SetStatusText(f"混响预设已切换为：{preset_name}")
        dlg.Destroy()

    def on_key(self, event):
        if event.AltDown():
            event.Skip()
            return

        key = event.GetKeyCode()
        moved = False
        step = 1.5

        if key == wx.WXK_LEFT:
            self.listener_pos[0] -= step
            self.listener_ahead = steamaudio.Vector3(-1.0, 0.0, 0.0)
            moved = True
        elif key == wx.WXK_RIGHT:
            self.listener_pos[0] += step
            self.listener_ahead = steamaudio.Vector3(1.0, 0.0, 0.0)
            moved = True
        elif key == wx.WXK_UP:
            self.listener_pos[1] -= step
            self.listener_ahead = steamaudio.Vector3(0.0, 0.0, -1.0)
            moved = True
        elif key == wx.WXK_DOWN:
            self.listener_pos[1] += step
            self.listener_ahead = steamaudio.Vector3(0.0, 0.0, 1.0)
            moved = True
        elif key == wx.WXK_SPACE and self.audio_thread:
            self.audio_thread.reverb_enabled = not self.audio_thread.reverb_enabled
            self.SetStatusText(f"混响已{'开启' if self.audio_thread.reverb_enabled else '关闭'}")
            return
        elif key == wx.WXK_F3:
            self.show_reverb_preset_dialog()
            return
        elif key == wx.WXK_F4:
            self.show_geometry_settings_dialog()
            return
        elif key == wx.WXK_F5 and self.audio_thread:
            enabled = self.audio_thread.toggle_geometry()
            self.geometry_settings.geometry_enabled = enabled
            self.scene_panel.settings = self.geometry_settings
            self.scene_panel.Refresh()
            self.SetStatusText(f"几何应用已{'开启' if enabled else '关闭'}")
            return
        elif key == wx.WXK_F6 and self.audio_thread:
            enabled = self.audio_thread.toggle_reflections()
            self.geometry_settings.reflections_enabled = enabled
            self.scene_panel.settings = self.geometry_settings
            self.scene_panel.Refresh()
            self.SetStatusText(f"场景反射已{'开启' if enabled else '关闭'}")
            return
        else:
            event.Skip()
            return

        if moved:
            self._push_listener_state()
            if self.footstep_sound:
                self.footstep_sound.play()

    def on_close(self, _):
        self.stop_event.set()
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        pygame.mixer.quit()
        self.Destroy()


class App(wx.App):
    def OnInit(self):
        frame = MainFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = App()
    app.MainLoop()
