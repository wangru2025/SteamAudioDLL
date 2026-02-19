#!/usr/bin/env python3
"""
交互式3D空间音频环境 - 使用steamaudio库版本
支持方向键移动听者，实时处理空间音频，用pygame播放脚步声
"""

import sys
from pathlib import Path
import numpy as np
import math
import threading
import queue
import wx
import soundfile as sf
import pyaudio
import time
import pygame
import keyboard

# 添加python-steamaudio到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "python-steamaudio"))

try:
    import steamaudio
except ImportError as e:
    print(f"错误: 无法导入steamaudio库: {e}")
    print("请确保python-steamaudio包已安装或在正确的路径")
    sys.exit(1)


class AudioThread(threading.Thread):
    """后台音频处理和播放线程"""
    
    def __init__(self, audio_data_list, sample_rate, listener_queue, stop_event, status_callback):
        super().__init__(daemon=True)
        self.audio_data_list = audio_data_list  # 多个音频源
        self.sample_rate = sample_rate
        self.listener_queue = listener_queue
        self.stop_event = stop_event
        self.status_callback = status_callback
        self.chunk_size = 256
        self.mixer = None
        self.reverb = None
        self.current_positions = [0, 0]  # 每个源的当前位置
        self.listener_pos = [0.0, 0.0]
        self.sound_positions = [[0.0, 0.0], [30.0, 0.0]]  # 两个声源位置
        self.reverb_enabled = False
        self.current_preset = steamaudio.RoomReverb.PRESET_MEDIUM_ROOM
        
    def run(self):
        try:
            # 初始化Steam Audio上下文
            with steamaudio.Context(sample_rate=self.sample_rate, frame_size=self.chunk_size):
                print("✓ Steam Audio上下文已初始化")
                
                # 创建多声源混音器
                self.mixer = steamaudio.AudioMixer(max_sources=8)
                
                # 添加两个声源
                self.mixer.add_source(0, input_channels=1)  # 源0：单声道
                self.mixer.add_source(1, input_channels=1)  # 源1：单声道
                
                print("✓ 混音器已创建，添加了2个声源")
                
                # 创建房间混响
                self.reverb = steamaudio.RoomReverb()
                self.reverb.set_preset(self.current_preset)
                
                print("✓ 房间混响已创建")
                
                # 初始化PyAudio
                p = pyaudio.PyAudio()
                stream = p.open(
                    format=pyaudio.paFloat32,
                    channels=2,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=self.chunk_size
                )
                
                print("✓ 音频流已打开")
                
                # 处理音频循环
                while not self.stop_event.is_set():
                    # 获取最新的听者位置
                    try:
                        self.listener_pos = self.listener_queue.get_nowait()
                    except queue.Empty:
                        pass
                    
                    # 为每个源读取音频块
                    sources_data = {}
                    params_dict = {}
                    
                    for i in range(2):
                        start = self.current_positions[i]
                        end = min(start + self.chunk_size, len(self.audio_data_list[i]))
                        chunk = self.audio_data_list[i][start:end]
                        
                        if end >= len(self.audio_data_list[i]):
                            self.current_positions[i] = 0
                        else:
                            self.current_positions[i] = end
                        
                        # 填充不足的样本
                        if len(chunk) < self.chunk_size:
                            chunk = np.pad(chunk, (0, self.chunk_size - len(chunk)), mode='constant')
                        
                        sources_data[i] = chunk.astype(np.float32)
                        
                        # 设置空间化参数
                        params = steamaudio.SpatializationParams()
                        params.listener_pos = steamaudio.Vector3(
                            self.listener_pos[0], 0, self.listener_pos[1]
                        )
                        params.listener_forward = steamaudio.Vector3(0, 0, 1)
                        params.listener_up = steamaudio.Vector3(0, 1, 0)
                        params.sound_pos = steamaudio.Vector3(
                            self.sound_positions[i][0], 0, self.sound_positions[i][1]
                        )
                        params.min_distance = 0.1
                        params.max_distance = 1000.0
                        params.rolloff = 1.0
                        params.directional_attenuation = 1.0
                        
                        params_dict[i] = params
                    
                    # 处理音频（混合多个声源）
                    output_chunk = self.mixer.process(sources_data, params_dict)
                    
                    # 应用混响（如果启用）
                    if self.reverb_enabled and self.reverb:
                        # 将立体声转换为交错格式（与原版本一致）
                        # output_chunk shape: (frames, 2) -> interleaved: (frames*2,)
                        interleaved = output_chunk.flatten('C')  # C order: row-major
                        
                        # 处理交错的立体声数据
                        reverb_output = self.reverb.process(interleaved)
                        
                        # 混合原始输出和混响输出（50% 原始 + 50% 混响）
                        mixed = interleaved * 0.5 + reverb_output * 0.5
                        
                        # 转换回立体声格式
                        output_chunk = mixed.reshape(-1, 2)
                    
                    # 播放处理后的音频
                    try:
                        stream.write(output_chunk.astype(np.float32).tobytes())
                    except Exception as e:
                        print(f"播放错误: {e}")
                        break
                    
                    # 更新状态显示
                    if self.status_callback:
                        self.status_callback(self.listener_pos, self.sound_positions)
                
                # 清理
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                print("✓ 音频线程停止")
            
        except Exception as e:
            print(f"音频线程错误: {e}")
            import traceback
            traceback.print_exc()


class ScenePanel(wx.Panel):
    """3D场景显示面板 - 无限大地图，跟随听者"""
    
    PANEL_SIZE = 400
    GRID_SIZE = 10
    
    def __init__(self, parent, listener_queue):
        super().__init__(parent)
        self.listener_queue = listener_queue
        self.listener_pos = [0.0, 0.0]
        self.sound_positions = [[0.0, 0.0], [30.0, 0.0]]  # 两个声源
        self.distances = [0.0, 0.0]
        self.zoom = 1.0
        
        self.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBackground(wx.Brush(wx.Colour(30, 30, 30)))
        dc.Clear()
        
        # 计算缩放因子 - 根据最近的声源距离自动调整视野
        min_distance = min(self.distances) if self.distances else 10
        if min_distance < 5:
            self.zoom = 20
        elif min_distance < 20:
            self.zoom = 10
        elif min_distance < 50:
            self.zoom = 5
        else:
            self.zoom = 2
        
        # 听者始终在屏幕中心
        center_x = self.PANEL_SIZE // 2
        center_y = self.PANEL_SIZE // 2
        
        # 绘制网格（以听者为中心）
        dc.SetPen(wx.Pen(wx.Colour(60, 60, 60), 1))
        grid_step = self.GRID_SIZE * self.zoom
        
        # 计算网格偏移
        offset_x = (self.listener_pos[0] * self.zoom) % grid_step
        offset_y = (self.listener_pos[1] * self.zoom) % grid_step
        
        # 绘制竖线
        x = center_x - offset_x
        while x < self.PANEL_SIZE:
            dc.DrawLine(int(x), 0, int(x), self.PANEL_SIZE)
            x += grid_step
        
        x = center_x - offset_x - grid_step
        while x >= 0:
            dc.DrawLine(int(x), 0, int(x), self.PANEL_SIZE)
            x -= grid_step
        
        # 绘制横线
        y = center_y - offset_y
        while y < self.PANEL_SIZE:
            dc.DrawLine(0, int(y), self.PANEL_SIZE, int(y))
            y += grid_step
        
        y = center_y - offset_y - grid_step
        while y >= 0:
            dc.DrawLine(0, int(y), self.PANEL_SIZE, int(y))
            y -= grid_step
        
        # 绘制中心十字（听者位置）
        dc.SetPen(wx.Pen(wx.Colour(100, 100, 100), 1))
        dc.DrawLine(center_x - 5, center_y, center_x + 5, center_y)
        dc.DrawLine(center_x, center_y - 5, center_x, center_y + 5)
        
        # 绘制两个声源（不同颜色）
        colors = [(255, 0, 0), (0, 255, 0)]  # 红色和绿色
        labels = ["声源1", "声源2"]
        
        for i, (sound_pos, color, label) in enumerate(zip(self.sound_positions, colors, labels)):
            sound_screen_x = center_x + (sound_pos[0] - self.listener_pos[0]) * self.zoom
            sound_screen_y = center_y + (sound_pos[1] - self.listener_pos[1]) * self.zoom
            
            # 只在屏幕范围内绘制声源
            if -50 < sound_screen_x < self.PANEL_SIZE + 50 and -50 < sound_screen_y < self.PANEL_SIZE + 50:
                dc.SetBrush(wx.Brush(wx.Colour(*color)))
                dc.SetPen(wx.Pen(wx.Colour(*color), 2))
                dc.DrawCircle(int(sound_screen_x), int(sound_screen_y), 8)
                dc.SetTextForeground(wx.Colour(*color))
                dc.DrawText(label, int(sound_screen_x) + 12, int(sound_screen_y) - 8)
        
        # 绘制听者（蓝色圆形，始终在中心）
        dc.SetBrush(wx.Brush(wx.Colour(0, 100, 255)))
        dc.SetPen(wx.Pen(wx.Colour(0, 100, 255), 2))
        dc.DrawCircle(center_x, center_y, 8)
        dc.SetTextForeground(wx.Colour(100, 150, 255))
        dc.DrawText("听者", center_x + 12, center_y - 8)
        
        # 绘制听者方向（蓝色箭头）
        arrow_length = 20
        arrow_x = center_x + arrow_length
        arrow_y = center_y
        dc.SetPen(wx.Pen(wx.Colour(0, 150, 255), 2))
        dc.DrawLine(center_x, center_y, arrow_x, arrow_y)
        
        # 绘制连接线
        dc.SetPen(wx.Pen(wx.Colour(150, 150, 150), 1))
        for sound_pos in self.sound_positions:
            sound_screen_x = center_x + (sound_pos[0] - self.listener_pos[0]) * self.zoom
            sound_screen_y = center_y + (sound_pos[1] - self.listener_pos[1]) * self.zoom
            dc.DrawLine(center_x, center_y, int(sound_screen_x), int(sound_screen_y))
        
        # 绘制坐标信息
        dc.SetTextForeground(wx.Colour(200, 200, 200))
        dc.DrawText(f"声源1坐标: ({self.sound_positions[0][0]:.1f}, {self.sound_positions[0][1]:.1f})", 10, 10)
        dc.DrawText(f"声源1距离: {self.distances[0]:.1f}m", 10, 30)
        dc.DrawText(f"声源2坐标: ({self.sound_positions[1][0]:.1f}, {self.sound_positions[1][1]:.1f})", 10, 50)
        dc.DrawText(f"声源2距离: {self.distances[1]:.1f}m", 10, 70)
        dc.DrawText(f"听者坐标: ({self.listener_pos[0]:.1f}, {self.listener_pos[1]:.1f})", 10, 90)
        dc.DrawText(f"缩放: {self.zoom:.1f}x", 10, 110)
    
    def update_positions(self, listener_pos, sound_positions):
        """更新位置"""
        self.listener_pos = listener_pos
        self.sound_positions = sound_positions
        self.distances = [
            math.sqrt((sound_positions[i][0] - listener_pos[0])**2 + 
                     (sound_positions[i][1] - listener_pos[1])**2)
            for i in range(2)
        ]
        self.Refresh()
    
    def move_listener(self, dx, dy):
        """移动听者（无限制）"""
        self.listener_pos[0] += dx
        self.listener_pos[1] += dy
        
        # 发送到音频线程
        try:
            self.listener_queue.put_nowait(self.listener_pos.copy())
        except queue.Full:
            pass
        
        self.Refresh()


class MainFrame(wx.Frame):
    """主窗口"""
    
    def __init__(self):
        super().__init__(None, title="交互式3D空间音频环境 (steamaudio库)", size=(500, 750))
        
        # 初始化pygame mixer用于脚步声
        pygame.mixer.init()
        self.footstep_sound = None
        
        # 创建面板
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标题
        title = wx.StaticText(panel, label="交互式3D空间音频环境")
        font = title.GetFont()
        font.PointSize = 14
        font.Weight = wx.FONTWEIGHT_BOLD
        title.SetFont(font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # 场景面板
        self.scene_panel = ScenePanel(panel, queue.Queue(maxsize=1))
        sizer.Add(self.scene_panel, 1, wx.ALL | wx.EXPAND, 10)
        
        # 控制说明
        info_text = wx.StaticText(panel, label=
            "红色圆: 声源1 (固定在原点)\n"
            "绿色圆: 声源2 (固定在距离30处)\n"
            "蓝色圆: 听者 (始终在屏幕中心)\n"
            "\n"
            "控制方式:\n"
            "  ↑ / ↓ / ← / → : 移动听者\n"
            "  Shift + 方向键 : 更快速移动\n"
            "  空格 : 启用/禁用房间混响\n"
            "  F3 : 打开混响预设菜单\n"
            "\n"
            "地图无限大，可无限远离声源\n"
            "每次移动都会播放脚步声\n"
            "距离越远，声音越小\n"
            "\n"
            "使用steamaudio Python库")
        sizer.Add(info_text, 0, wx.ALL | wx.EXPAND, 10)
        
        # 状态栏
        self.CreateStatusBar()
        self.SetStatusText("准备就绪")
        
        panel.SetSizer(sizer)
        
        # 绑定事件
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.scene_panel.SetFocus()
        
        # 房间预设列表
        self.room_presets = [
            "小房间 (2x2x2m)",
            "中等房间 (5x4x3m)",
            "大房间 (10x8x4m)",
            "小厅 (15x10x5m)",
            "大厅 (30x20x10m)",
            "大教堂 (50x40x20m)",
            "室外 (无混响)",
        ]
        
        # 启动音频线程
        self.stop_event = threading.Event()
        self.listener_queue = self.scene_panel.listener_queue
        self.audio_thread = None
        
        # 加载音频
        audio_path = Path(__file__).parent / "1.ogg"
        if not audio_path.exists():
            audio_path = Path(__file__).parent / "1.wav"
        
        footstep_path = Path(__file__).parent / "2.ogg"
        if not footstep_path.exists():
            footstep_path = Path(__file__).parent / "2.wav"
        
        audio_path_2 = Path(__file__).parent / "3.ogg"
        if not audio_path_2.exists():
            audio_path_2 = Path(__file__).parent / "3.wav"
        
        if not audio_path.exists() or not audio_path_2.exists():
            wx.MessageBox("错误: 找不到音频文件 (1.ogg/1.wav 或 3.ogg/3.wav)", "错误", wx.OK | wx.ICON_ERROR)
            self.audio_data_list = None
            self.sample_rate = 44100
        else:
            try:
                # 加载第一个音频
                audio_data_1, sample_rate = sf.read(str(audio_path), dtype='float32')
                if len(audio_data_1.shape) > 1 and audio_data_1.shape[1] > 1:
                    audio_data_1 = np.mean(audio_data_1, axis=1)
                else:
                    audio_data_1 = audio_data_1.flatten()
                
                # 加载第二个音频
                audio_data_2, _ = sf.read(str(audio_path_2), dtype='float32')
                if len(audio_data_2.shape) > 1 and audio_data_2.shape[1] > 1:
                    audio_data_2 = np.mean(audio_data_2, axis=1)
                else:
                    audio_data_2 = audio_data_2.flatten()
                
                self.audio_data_list = [audio_data_1, audio_data_2]
                self.sample_rate = sample_rate
                
                # 加载脚步声用pygame
                if footstep_path.exists():
                    try:
                        self.footstep_sound = pygame.mixer.Sound(str(footstep_path))
                        print(f"✓ 已加载脚步声: {footstep_path.name}")
                    except Exception as e:
                        print(f"警告: 无法加载脚步声: {e}")
                
                self.SetStatusText(f"已加载: {audio_path.name} 和 {audio_path_2.name} ({sample_rate}Hz)")
                
                # 启动音频线程
                self.audio_thread = AudioThread(
                    self.audio_data_list,
                    self.sample_rate,
                    self.listener_queue,
                    self.stop_event,
                    self.on_audio_status_update
                )
                self.audio_thread.start()
                
                # 初始化听者位置为原点
                self.scene_panel.listener_pos = [0.0, 0.0]
                self.scene_panel.sound_positions = [[0.0, 0.0], [30.0, 0.0]]
                
                # 启动按键监听线程
                self.start_keyboard_listener()
                
            except Exception as e:
                wx.MessageBox(f"错误: 无法加载音频文件\n{e}", "错误", wx.OK | wx.ICON_ERROR)
                self.audio_data_list = None
                self.sample_rate = 44100
    
    def on_audio_status_update(self, listener_pos, sound_pos):
        """音频线程更新状态"""
        wx.CallAfter(self.scene_panel.update_positions, listener_pos, sound_pos)
    
    def start_keyboard_listener(self):
        """启动按键监听线程"""
        def listen_keys():
            print("✓ 按键监听已启动")
            try:
                # 注册按键事件
                keyboard.on_press_key('up', lambda e: self.handle_key_press('up'))
                keyboard.on_press_key('down', lambda e: self.handle_key_press('down'))
                keyboard.on_press_key('left', lambda e: self.handle_key_press('left'))
                keyboard.on_press_key('right', lambda e: self.handle_key_press('right'))
                keyboard.on_press_key('space', lambda e: self.handle_key_press('space'))
                keyboard.on_press_key('f3', lambda e: self.handle_key_press('f3'))
                
                # 保持监听
                while not self.stop_event.is_set():
                    time.sleep(0.1)
            except Exception as e:
                print(f"按键监听错误: {e}")
        
        listener_thread = threading.Thread(target=listen_keys, daemon=True)
        listener_thread.start()
    
    def handle_key_press(self, key):
        """处理按键按下事件"""
        if key == 'space':
            if self.audio_thread:
                self.audio_thread.reverb_enabled = not self.audio_thread.reverb_enabled
                status = "启用" if self.audio_thread.reverb_enabled else "禁用"
                wx.CallAfter(self.SetStatusText, f"混响已{status}")
        
        elif key == 'f3':
            wx.CallAfter(self.show_reverb_preset_dialog)
        
        elif key in ['up', 'down', 'left', 'right']:
            step = 5
            if key == 'up':
                self.scene_panel.move_listener(0, -step)
            elif key == 'down':
                self.scene_panel.move_listener(0, step)
            elif key == 'left':
                self.scene_panel.move_listener(-step, 0)
            elif key == 'right':
                self.scene_panel.move_listener(step, 0)
            
            if self.footstep_sound:
                self.play_footstep()
    
    def on_key_down(self, event):
        """处理按键事件"""
        key_code = event.GetKeyCode()
        
        # 空格：切换混响
        if key_code == wx.WXK_SPACE:
            if self.audio_thread:
                self.audio_thread.reverb_enabled = not self.audio_thread.reverb_enabled
                status = "启用" if self.audio_thread.reverb_enabled else "禁用"
                self.SetStatusText(f"混响已{status}")
            return
        
        # F3：打开混响预设菜单
        if key_code == wx.WXK_F3:
            self.show_reverb_preset_dialog()
            return
        
        event.Skip()
    
    def play_footstep(self):
        """播放脚步声"""
        if self.footstep_sound:
            self.footstep_sound.play()
    
    def show_reverb_preset_dialog(self):
        """显示混响预设选择对话框"""
        dlg = wx.SingleChoiceDialog(
            self,
            "选择房间混响预设:",
            "房间混响",
            self.room_presets
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            selection = dlg.GetSelection()
            if self.audio_thread and self.audio_thread.reverb:
                # 应用预设
                try:
                    self.audio_thread.reverb.set_preset(selection)
                    self.audio_thread.current_preset = selection
                    self.SetStatusText(f"混响预设已更改: {self.room_presets[selection]}")
                except Exception as e:
                    self.SetStatusText(f"混响预设设置失败: {e}")
        
        dlg.Destroy()
    
    def on_close(self, event):
        """关闭窗口"""
        self.stop_event.set()
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        pygame.mixer.quit()
        self.Destroy()


class App(wx.App):
    """应用程序"""
    
    def OnInit(self):
        self.frame = MainFrame()
        self.frame.Show()
        return True


if __name__ == "__main__":
    app = App()
    app.MainLoop()
