#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game7.py - 打地鼠遊戲實現

import random
import pygame
import time
from pygame.locals import *

class WhacAMoleGame:
    """打地鼠遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.BROWN = (165, 42, 42)
        self.LIGHT_BROWN = (222, 184, 135)
        
        # 遊戲參數
        self.grid_size = 3       # 3x3 網格
        self.hole_radius = 50    # 洞的半徑
        self.mole_radius = 40    # 地鼠的半徑
        self.hammer_size = 70    # 錘子的大小
        
        # 計算網格位置
        self.calculate_grid()
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 初始化遊戲狀態
        self.reset_game()
        
        # 載入資源
        self.load_resources()
    
    def load_resources(self):
        """載入遊戲資源，如圖片、聲音等"""
        # 這裡可以載入地鼠、錘子等圖片
        # 但在此版本中，我們使用簡單的幾何圖形繪製
        pass
    
    def calculate_grid(self):
        """計算網格位置"""
        self.grid_positions = []
        
        # 計算間距
        margin_x = self.width // 6
        margin_y = self.height // 6
        
        # 計算間隔
        spacing_x = (self.width - 2 * margin_x) // (self.grid_size - 1)
        spacing_y = (self.height - 2 * margin_y) // (self.grid_size - 1)
        
        # 生成網格座標
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                pos_x = margin_x + x * spacing_x
                pos_y = margin_y + y * spacing_y
                self.grid_positions.append((pos_x, pos_y))
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.score = 0
        self.misses = 0
        self.time_left = 60  # 60 秒遊戲時間
        self.start_time = time.time()
        
        # 地鼠狀態
        self.moles = [False] * (self.grid_size * self.grid_size)  # 是否出現地鼠
        self.mole_timers = [0] * (self.grid_size * self.grid_size)  # 地鼠顯示時間
        
        # 錘子位置 (初始在中央)
        self.hammer_pos = (self.width // 2, self.height // 2)
        self.hammer_idx = (self.grid_size * self.grid_size) // 2  # 中央位置索引
        self.hammer_active = False  # 錘子是否正在敲打
        self.hammer_angle = 0  # 錘子旋轉角度
        
        # 難度參數
        self.mole_show_time_min = 1.0  # 最短顯示時間
        self.mole_show_time_max = 2.5  # 最長顯示時間
        self.mole_spawn_interval = 1.0  # 生成間隔
        self.last_spawn_time = time.time()
        
        # 用於控制輸入頻率
        self.last_input_time = time.time()
        self.input_delay = 0.2  # 秒
        
        # 連擊系統
        self.combo = 0
        self.last_hit_time = 0
        self.hits = 0
    
    def spawn_mole(self):
        """隨機生成一個地鼠"""
        # 尋找所有沒有地鼠的洞
        empty_holes = [i for i, mole in enumerate(self.moles) if not mole]
        
        if empty_holes:
            # 隨機選擇一個洞
            hole_idx = random.choice(empty_holes)
            
            # 出現地鼠
            self.moles[hole_idx] = True
            
            # 設置顯示時間
            show_time = random.uniform(self.mole_show_time_min, self.mole_show_time_max)
            self.mole_timers[hole_idx] = show_time
    
    def update_moles(self, delta_time):
        """更新地鼠狀態"""
        for i in range(len(self.moles)):
            if self.moles[i]:
                # 減少顯示時間
                self.mole_timers[i] -= delta_time
                
                # 如果時間到，地鼠消失
                if self.mole_timers[i] <= 0:
                    self.moles[i] = False
                    self.misses += 1  # 未打中算一次失誤
                    
                    # 增強音效回饋
                    if self.buzzer:
                        # 地鼠逃跑音效
                        self.buzzer.play_tone(frequency=200, duration=0.3)
    
    def hit_mole(self, position_idx):
        """擊中地鼠，增強反饋效果"""
        if 0 <= position_idx < len(self.moles) and self.moles[position_idx]:
            self.moles[position_idx] = False
            self.score += 10
            self.hits += 1
            
            # 連擊系統
            current_time = time.time()
            if current_time - self.last_hit_time < 1.0:  # 1秒內連擊
                self.combo += 1
                combo_bonus = self.combo * 5
                self.score += combo_bonus
            else:
                self.combo = 1
            
            self.last_hit_time = current_time
            
            # 增強音效反饋
            if self.buzzer:
                if self.combo > 5:
                    # 高連擊音效
                    self.buzzer.play_tone(frequency=1200, duration=0.2)
                elif self.combo > 3:
                    # 中連擊音效
                    self.buzzer.play_tone(frequency=1000, duration=0.2)
                else:
                    # 普通擊中音效
                    base_freq = 800 + (self.combo * 50)
                    self.buzzer.play_tone(frequency=base_freq, duration=0.15)
            
            return True
        return False
    
    def update(self, controller_input=None):
        """
        更新遊戲狀態
        
        參數:
            controller_input: 來自控制器的輸入字典
        
        返回:
            包含遊戲狀態的字典
        """
        if self.game_over or self.paused:
            # 處理遊戲結束或暫停狀態下的輸入
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 更新遊戲時間
        current_time = time.time()
        delta_time = current_time - self.start_time
        self.time_left = max(0, 60 - int(delta_time))
        
        # 時間到，遊戲結束
        if self.time_left <= 0:
            self.game_over = True
            
            # 播放遊戲結束音效
            if self.buzzer:
                self.buzzer.play_game_over_melody()
            
            return {"game_over": True, "score": self.score}
        
        # 生成新地鼠
        if current_time - self.last_spawn_time >= self.mole_spawn_interval:
            self.spawn_mole()
            self.last_spawn_time = current_time
        
        # 更新地鼠狀態
        self.update_moles(current_time - self.last_input_time)
        self.last_input_time = current_time
        
        # 處理錘子動畫
        if self.hammer_active:
            self.hammer_angle += 15
            if self.hammer_angle >= 60:
                self.hammer_active = False
                self.hammer_angle = 0
        
        # 處理玩家輸入
        if controller_input:
            input_detected = False
            
            # 移動錘子
            if controller_input.get("up_pressed"):
                self.hammer_idx = max(0, self.hammer_idx - self.grid_size)
                input_detected = True
            elif controller_input.get("down_pressed"):
                self.hammer_idx = min(len(self.grid_positions) - 1, self.hammer_idx + self.grid_size)
                input_detected = True
            
            if controller_input.get("left_pressed"):
                if self.hammer_idx % self.grid_size > 0:
                    self.hammer_idx -= 1
                input_detected = True
            elif controller_input.get("right_pressed"):
                if self.hammer_idx % self.grid_size < self.grid_size - 1:
                    self.hammer_idx += 1
                input_detected = True
            
            # 更新錘子位置
            if 0 <= self.hammer_idx < len(self.grid_positions):
                self.hammer_pos = self.grid_positions[self.hammer_idx]
            
            # 敲打控制
            if controller_input.get("a_pressed") and not self.hammer_active:
                self.hammer_active = True
                self.hammer_angle = 0
                self.hit_mole(self.hammer_idx)
                input_detected = True
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                input_detected = True
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
            
            # 如果檢測到輸入，播放音效
            if input_detected and self.buzzer and not controller_input.get("a_pressed"):
                self.buzzer.play_tone("navigate")
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製背景 (草地)
        pygame.draw.rect(screen, (34, 139, 34), (0, 0, self.width, self.height))
        
        # 繪製洞和地鼠
        for i, (x, y) in enumerate(self.grid_positions):
            # 繪製洞
            pygame.draw.circle(screen, self.BROWN, (x, y), self.hole_radius)
            pygame.draw.circle(screen, self.BLACK, (x, y), self.hole_radius - 5)
            
            # 如果有地鼠，繪製地鼠
            if self.moles[i]:
                pygame.draw.circle(screen, self.LIGHT_BROWN, (x, y - 15), self.mole_radius)
                
                # 繪製地鼠眼睛
                pygame.draw.circle(screen, self.BLACK, (x - 15, y - 25), 5)
                pygame.draw.circle(screen, self.BLACK, (x + 15, y - 25), 5)
                
                # 繪製地鼠鼻子和嘴巴
                pygame.draw.circle(screen, self.BLACK, (x, y - 15), 5)
                pygame.draw.arc(screen, self.BLACK, (x - 20, y - 15, 40, 20), 0, 3.14, 2)
        
        # 繪製錘子
        hammer_center = self.hammer_pos
        # 繪製錘子頭
        hammer_head_points = [
            (hammer_center[0] - 20, hammer_center[1] - 60 + self.hammer_angle),
            (hammer_center[0] + 20, hammer_center[1] - 60 + self.hammer_angle),
            (hammer_center[0] + 20, hammer_center[1] - 30 + self.hammer_angle),
            (hammer_center[0] - 20, hammer_center[1] - 30 + self.hammer_angle)
        ]
        pygame.draw.polygon(screen, (150, 75, 0), hammer_head_points)
        # 繪製錘子柄
        pygame.draw.line(screen, (101, 67, 33), 
                         (hammer_center[0], hammer_center[1] - 30 + self.hammer_angle),
                         (hammer_center[0], hammer_center[1] + 30),
                         5)
        
        # 繪製遊戲資訊
        font = pygame.font.Font(None, 36)
        
        # 分數
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        
        # 失誤次數
        misses_text = font.render(f"失誤: {self.misses}", True, self.WHITE)
        screen.blit(misses_text, (10, 50))
        
        # 剩餘時間
        time_text = font.render(f"時間: {self.time_left}", True, self.WHITE)
        screen.blit(time_text, (self.width - 150, 10))
        
        # 遊戲結束畫面
        if self.game_over:
            self.draw_game_over(screen)
        
        # 暫停畫面
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """繪製遊戲結束畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("遊戲結束", True, self.RED)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"最終分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 2 + 10))
        
        miss_text = font.render(f"總失誤: {self.misses}", True, self.WHITE)
        screen.blit(miss_text, (self.width // 2 - miss_text.get_width() // 2, self.height // 2 + 50))
        
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 90))
    
    def draw_pause(self, screen):
        """繪製暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("暫停", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        continue_text = font.render("按 Start 繼續", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 10))
    
    def cleanup(self):
        """清理遊戲資源"""
        # 目前無需特殊清理，但保留此方法以便未來擴充
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
        pygame.display.set_caption("打地鼠遊戲測試")
        
        # 建立遊戲實例
        game = WhacAMoleGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # 遊戲主迴圈
        running = True
        last_time = time.time()
        
        while running:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            # 處理事件
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # 獲取當前按下的按鍵狀態
            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True
            
            # 更新遊戲
            game.update(controller_input)
            
            # 渲染
            game.render(screen)
            pygame.display.flip()
            
            # 控制幀率
            pygame.time.Clock().tick(60)
        
        # 退出 pygame
        pygame.quit()
    
    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        pygame.quit()
