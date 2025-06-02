#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game9.py - 增強版反應力測試遊戲實現

import random
import pygame
import time
import math
from pygame.locals import *

class ReactionTestGame:
    """增強版反應力測試遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (255, 0, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.DARK_GREEN = (0, 128, 0)
        self.GRAY = (128, 128, 128)
        
        # 遊戲參數
        self.trials = 10           # 測試次數
        self.min_wait_time = 1.0   # 最短等待時間
        self.max_wait_time = 5.0   # 最長等待時間
        self.signal_duration = 2.0 # 信號顯示時間
        
        # 測試模式
        self.test_modes = [
            {
                'name': '視覺反應',
                'description': '看到綠色信號時按A',
                'type': 'visual',
                'signal_color': self.GREEN,
                'background_color': self.BLACK
            },
            {
                'name': '顏色識別',
                'description': '只對綠色信號反應',
                'type': 'color_recognition',
                'signal_color': self.GREEN,
                'distractor_colors': [self.RED, self.BLUE, self.YELLOW],
                'background_color': self.BLACK
            },
            {
                'name': '位置反應',
                'description': '信號出現在不同位置',
                'type': 'position',
                'signal_color': self.GREEN,
                'background_color': self.BLACK
            },
            {
                'name': '音視反應',
                'description': '同時有聲音和視覺信號',
                'type': 'audio_visual',
                'signal_color': self.CYAN,
                'background_color': self.BLACK
            },
            {
                'name': '連續反應',
                'description': '快速連續信號測試',
                'type': 'continuous',
                'signal_color': self.YELLOW,
                'background_color': self.BLACK
            }
        ]
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.current_mode_index = 0
        self.current_trial = 0
        
        # 測試數據
        self.reaction_times = []
        self.false_starts = 0     # 過早反應次數
        self.missed_signals = 0   # 錯過信號次數
        self.correct_responses = 0 # 正確反應次數
        
        # 狀態控制
        self.state = 'menu'  # menu, instructions, waiting, signal, result, game_over
        self.signal_start_time = 0
        self.wait_start_time = 0
        self.signal_position = (self.width // 2, self.height // 2)
        self.current_signal_color = self.GREEN
        self.is_distractor = False
        
        # 連續模式特殊變數
        self.continuous_signals = []
        self.continuous_responses = []
        
        # 動畫效果
        self.signal_pulse = 0
        self.background_flash = 0
        self.particles = []
        
        # 統計分析
        self.session_start_time = time.time()
    
    def get_current_mode(self):
        """獲取當前測試模式"""
        return self.test_modes[self.current_mode_index]
    
    def start_test(self):
        """開始測試"""
        self.state = 'instructions'
        if self.buzzer:
            self.buzzer.play_tone(frequency=800, duration=0.3)
    
    def next_trial(self):
        """進入下一個試驗"""
        if self.current_trial >= self.trials:
            self.finish_mode()
            return
        
        self.state = 'waiting'
        self.wait_start_time = time.time()
        
        # 根據模式設置等待時間
        mode = self.get_current_mode()
        if mode['type'] == 'continuous':
            self.wait_time = random.uniform(0.5, 1.5)
        else:
            self.wait_time = random.uniform(self.min_wait_time, self.max_wait_time)
        
        # 設置信號位置（位置反應模式）
        if mode['type'] == 'position':
            margin = 100
            self.signal_position = (
                random.randint(margin, self.width - margin),
                random.randint(margin, self.height - margin)
            )
        else:
            self.signal_position = (self.width // 2, self.height // 2)
        
        # 設置信號顏色（顏色識別模式）
        if mode['type'] == 'color_recognition':
            if random.random() < 0.7:  # 70% 機率是正確顏色
                self.current_signal_color = mode['signal_color']
                self.is_distractor = False
            else:
                self.current_signal_color = random.choice(mode['distractor_colors'])
                self.is_distractor = True
        else:
            self.current_signal_color = mode['signal_color']
            self.is_distractor = False
    
    def show_signal(self):
        """顯示信號"""
        self.state = 'signal'
        self.signal_start_time = time.time()
        self.signal_pulse = 0
        
        # 播放音效（音視反應模式）
        mode = self.get_current_mode()
        if mode['type'] == 'audio_visual' and self.buzzer:
            self.buzzer.play_tone(frequency=800, duration=0.2)
        
        # 創建視覺效果
        self.create_signal_particles()
    
    def create_signal_particles(self):
        """創建信號粒子效果"""
        for _ in range(8):
            particle = {
                'x': self.signal_position[0],
                'y': self.signal_position[1],
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-100, 100),
                'life': 1.0,
                'color': self.current_signal_color,
                'size': random.uniform(3, 8)
            }
            self.particles.append(particle)
    
    def handle_response(self):
        """處理玩家反應"""
        current_time = time.time()
        
        if self.state == 'waiting':
            # 過早反應
            self.false_starts += 1
            self.background_flash = 10
            if self.buzzer:
                self.buzzer.play_tone(frequency=300, duration=0.5)
            self.next_trial()
            
        elif self.state == 'signal':
            # 正確時機的反應
            mode = self.get_current_mode()
            
            if mode['type'] == 'color_recognition' and self.is_distractor:
                # 對干擾信號的錯誤反應
                self.false_starts += 1
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
            else:
                # 正確反應
                reaction_time = (current_time - self.signal_start_time) * 1000  # 轉換為毫秒
                self.reaction_times.append(reaction_time)
                self.correct_responses += 1
                
                # 視覺回饋
                self.create_success_particles()
                
                # 音效回饋
                if self.buzzer:
                    # 根據反應時間播放不同音調
                    if reaction_time < 200:
                        self.buzzer.play_tone(frequency=1000, duration=0.2)  # 優秀
                    elif reaction_time < 350:
                        self.buzzer.play_tone(frequency=800, duration=0.2)   # 良好
                    else:
                        self.buzzer.play_tone(frequency=600, duration=0.2)   # 一般
            
            self.current_trial += 1
            self.next_trial()
    
    def create_success_particles(self):
        """創建成功反應的粒子效果"""
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            particle = {
                'x': self.signal_position[0],
                'y': self.signal_position[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.5,
                'color': self.YELLOW,
                'size': random.uniform(2, 6)
            }
            self.particles.append(particle)
    
    def finish_mode(self):
        """完成當前模式"""
        self.state = 'result'
        if self.buzzer:
            self.buzzer.play_tone(frequency=1200, duration=0.5)
    
    def next_mode(self):
        """進入下一個模式"""
        self.current_mode_index += 1
        if self.current_mode_index >= len(self.test_modes):
            self.game_over = True
            self.state = 'game_over'
        else:
            self.current_trial = 0
            self.state = 'menu'
    
    def calculate_statistics(self):
        """計算統計數據"""
        if not self.reaction_times:
            return {}
        
        times = self.reaction_times
        return {
            'count': len(times),
            'average': sum(times) / len(times),
            'fastest': min(times),
            'slowest': max(times),
            'median': sorted(times)[len(times) // 2],
            'consistency': max(times) - min(times) if len(times) > 1 else 0
        }
    
    def get_performance_rating(self, avg_time):
        """根據平均反應時間評定表現"""
        if avg_time < 200:
            return "驚人", self.GREEN
        elif avg_time < 250:
            return "優秀", self.CYAN
        elif avg_time < 300:
            return "良好", self.YELLOW
        elif avg_time < 400:
            return "普通", self.ORANGE
        else:
            return "需要改進", self.RED
    
    def update_particles(self, delta_time):
        """更新粒子效果"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time
            particle['vy'] += 200 * delta_time  # 重力效果
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update(self, controller_input=None):
        """更新遊戲狀態"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "paused": self.paused}
        
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # 更新動畫效果
        self.signal_pulse += delta_time * 8
        if self.background_flash > 0:
            self.background_flash -= delta_time * 30
        
        # 更新粒子
        self.update_particles(delta_time)
        
        # 處理輸入
        if controller_input:
            # A按鈕 - 反應按鈕
            if controller_input.get("a_pressed"):
                if self.state in ['waiting', 'signal']:
                    self.handle_response()
                elif self.state == 'menu':
                    self.start_test()
                elif self.state == 'instructions':
                    self.next_trial()
                elif self.state == 'result':
                    self.next_mode()
            
            # B按鈕 - 返回或跳過
            if controller_input.get("b_pressed"):
                if self.state == 'menu':
                    self.game_over = True
                elif self.state in ['instructions', 'result']:
                    self.state = 'menu'
            
            # 方向鍵 - 選擇模式
            if self.state == 'menu':
                if controller_input.get("up_pressed"):
                    self.current_mode_index = (self.current_mode_index - 1) % len(self.test_modes)
                elif controller_input.get("down_pressed"):
                    self.current_mode_index = (self.current_mode_index + 1) % len(self.test_modes)
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "paused": self.paused}
        
        # 狀態機邏輯
        if self.state == 'waiting':
            if current_time - self.wait_start_time >= self.wait_time:
                self.show_signal()
        
        elif self.state == 'signal':
            if current_time - self.signal_start_time >= self.signal_duration:
                # 超時，算作錯過
                self.missed_signals += 1
                self.current_trial += 1
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
                self.next_trial()
        
        return {"game_over": self.game_over}
    
    def render(self, screen):
        """渲染遊戲畫面"""
        # 背景
        mode = self.get_current_mode()
        bg_color = mode.get('background_color', self.BLACK)
        
        # 閃爍效果
        if self.background_flash > 0:
            flash_intensity = min(self.background_flash / 10, 1.0)
            bg_color = tuple(min(255, int(c + (255 - c) * flash_intensity)) for c in bg_color)
        
        screen.fill(bg_color)
        
        # 根據狀態渲染不同內容
        if self.state == 'menu':
            self.render_menu(screen)
        elif self.state == 'instructions':
            self.render_instructions(screen)
        elif self.state == 'waiting':
            self.render_waiting(screen)
        elif self.state == 'signal':
            self.render_signal(screen)
        elif self.state == 'result':
            self.render_result(screen)
        elif self.game_over:
            self.render_game_over(screen)
        
        # 渲染粒子效果
        self.render_particles(screen)
        
        # 暫停畫面
        if self.paused:
            self.render_pause_overlay(screen)
    
    def render_menu(self, screen):
        """渲染選單"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # 標題
        title_text = font_large.render("反應力測試", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))
        
        # 模式選擇
        y_start = 150
        for i, mode in enumerate(self.test_modes):
            color = self.YELLOW if i == self.current_mode_index else self.WHITE
            prefix = "▶ " if i == self.current_mode_index else "  "
            
            mode_text = font_medium.render(f"{prefix}{mode['name']}", True, color)
            screen.blit(mode_text, (100, y_start + i * 60))
            
            # 模式描述
            if i == self.current_mode_index:
                desc_text = font_small.render(mode['description'], True, self.GRAY)
                screen.blit(desc_text, (120, y_start + i * 60 + 35))
        
        # 操作提示
        hint_text = font_small.render("上下鍵選擇模式，A鍵開始，B鍵退出", True, self.WHITE)
        screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 80))
    
    def render_instructions(self, screen):
        """渲染說明"""
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        mode = self.get_current_mode()
        
        # 模式名稱
        title_text = font_large.render(mode['name'], True, self.CYAN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        # 說明
        instructions = [
            mode['description'],
            "",
            "準備好後按 A 鍵開始測試",
            f"將進行 {self.trials} 次測試",
            "",
            "注意：",
            "• 過早反應會被記錄為錯誤",
            "• 超時未反應也會被記錄",
            "• 盡可能快速且準確地反應"
        ]
        
        y_pos = 200
        for instruction in instructions:
            if instruction == "":
                y_pos += 30
                continue
            
            if instruction.startswith("注意："):
                color = self.YELLOW
                font = font_medium
            elif instruction.startswith("•"):
                color = self.WHITE
                font = font_small
            else:
                color = self.WHITE
                font = font_medium
            
            text = font.render(instruction, True, color)
            screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
            y_pos += 40
    
    def render_waiting(self, screen):
        """渲染等待畫面"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # 等待提示
        wait_text = font_large.render("準備...", True, self.WHITE)
        screen.blit(wait_text, (self.width // 2 - wait_text.get_width() // 2, self.height // 2 - 50))
        
        # 進度顯示
        progress_text = font_medium.render(f"測試 {self.current_trial + 1} / {self.trials}", True, self.GRAY)
        screen.blit(progress_text, (self.width // 2 - progress_text.get_width() // 2, self.height // 2 + 50))
        
        # 警告文字（閃爍）
        if int(time.time() * 2) % 2:
            warning_text = font_medium.render("不要提前按鍵！", True, self.RED)
            screen.blit(warning_text, (self.width // 2 - warning_text.get_width() // 2, self.height // 2 + 100))
    
    def render_signal(self, screen):
        """渲染信號"""
        font_large = pygame.font.Font(None, 72)
        
        # 信號圓圈（脈沖效果）
        pulse_size = 80 + math.sin(self.signal_pulse) * 20
        
        pygame.draw.circle(screen, self.current_signal_color, 
                         self.signal_position, int(pulse_size))
        pygame.draw.circle(screen, self.WHITE, 
                         self.signal_position, int(pulse_size), 3)
        
        # 反應提示
        if not self.is_distractor:
            react_text = font_large.render("反應！", True, self.WHITE)
            screen.blit(react_text, (self.width // 2 - react_text.get_width() // 2, 100))
        
        # 進度顯示
        font_medium = pygame.font.Font(None, 48)
        progress_text = font_medium.render(f"測試 {self.current_trial + 1} / {self.trials}", True, self.GRAY)
        screen.blit(progress_text, (self.width // 2 - progress_text.get_width() // 2, self.height - 100))
    
    def render_result(self, screen):
        """渲染結果"""
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        mode = self.get_current_mode()
        stats = self.calculate_statistics()
        
        # 模式名稱
        title_text = font_large.render(f"{mode['name']} - 結果", True, self.CYAN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))
        
        if stats:
            # 主要統計
            avg_time = stats['average']
            rating, rating_color = self.get_performance_rating(avg_time)
            
            y_pos = 150
            results = [
                f"平均反應時間: {avg_time:.1f} ms",
                f"最快反應: {stats['fastest']:.1f} ms",
                f"最慢反應: {stats['slowest']:.1f} ms",
                f"穩定性: {stats['consistency']:.1f} ms",
                "",
                f"表現評定: {rating}"
            ]
            
            for i, result in enumerate(results):
                if result == "":
                    y_pos += 30
                    continue
                
                if result.startswith("表現評定"):
                    color = rating_color
                    font = font_medium
                else:
                    color = self.WHITE
                    font = font_medium
                
                text = font.render(result, True, color)
                screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
                y_pos += 45
            
            # 準確率
            total_attempts = self.correct_responses + self.false_starts + self.missed_signals
            if total_attempts > 0:
                accuracy = (self.correct_responses / total_attempts) * 100
                accuracy_text = font_medium.render(f"準確率: {accuracy:.1f}%", True, 
                                                 self.GREEN if accuracy >= 80 else self.YELLOW if accuracy >= 60 else self.RED)
                screen.blit(accuracy_text, (self.width // 2 - accuracy_text.get_width() // 2, y_pos))
                y_pos += 45
        
        # 操作提示
        hint_text = font_small.render("A鍵繼續下一個模式，B鍵返回選單", True, self.WHITE)
        screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 80))
    
    def render_game_over(self, screen):
        """渲染遊戲結束畫面"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # 標題
        title_text = font_large.render("測試完成！", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        # 總體統計
        if self.reaction_times:
            overall_stats = self.calculate_statistics()
            avg_time = overall_stats['average']
            rating, rating_color = self.get_performance_rating(avg_time)
            
            y_pos = 200
            summary = [
                f"總測試次數: {len(self.reaction_times)}",
                f"總體平均反應時間: {avg_time:.1f} ms",
                f"最佳反應時間: {overall_stats['fastest']:.1f} ms",
                f"總體表現: {rating}",
                "",
                f"正確反應: {self.correct_responses}",
                f"過早反應: {self.false_starts}",
                f"錯過信號: {self.missed_signals}"
            ]
            
            for line in summary:
                if line == "":
                    y_pos += 30
                    continue
                
                if line.startswith("總體表現"):
                    color = rating_color
                elif line.startswith("正確反應"):
                    color = self.GREEN
                elif line.startswith("過早反應") or line.startswith("錯過信號"):
                    color = self.RED
                else:
                    color = self.WHITE
                
                text = font_medium.render(line, True, color)
                screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
                y_pos += 40
        
        # 重新開始提示
        restart_text = font_small.render("按 Start 重新測試", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height - 80))
    
    def render_particles(self, screen):
        """渲染粒子效果"""
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                size = max(1, int(particle['size'] * particle['life']))
                
                # 創建半透明表面
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], alpha)
                pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))
    
    def render_pause_overlay(self, screen):
        """渲染暫停覆蓋層"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        pause_text = font_large.render("暫停", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))
        
        continue_text = font_medium.render("按 Start 繼續", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 50))
    
    def cleanup(self):
        """清理遊戲資源"""
        pass


# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 設置視窗
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("反應力測試遊戲")
        
        # 建立遊戲實例
        game = ReactionTestGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_b: "b_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # 遊戲主迴圈
        running = True
        clock = pygame.time.Clock()
        
        while running:
            # 處理事件
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # 獲取當前按下的按鍵狀態
            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True
            
            # 更新遊戲
            game_status = game.update(controller_input)
            
            # 渲染
            game.render(screen)
            pygame.display.flip()
            
            # 控制幀率
            clock.tick(60)
            
            # 檢查是否結束
            if game_status.get("game_over") and not keys[pygame.K_RETURN]:
                pass
    
    except Exception as e:
        print(f"遊戲執行過程中發生錯誤: {e}")
    finally:
        pygame.quit()
        print("反應力測試遊戲結束")
