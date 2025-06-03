#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filepath: d:\User\Desktop\SensorGAME\gamebox\games\game2.py # Original path comment
# game2.py - Brick Breaker Game Implementation (Enhanced)

import random
import pygame
import time
import math
from pygame.locals import *

class PowerUp:
    """道具類別"""
    def __init__(self, x, y, type_info, power_type_name, speed=2.5):
        self.x = x
        self.y = y
        self.type_info = type_info # 包含顏色、持續時間、音效頻率等
        self.type_name = power_type_name
        self.color = type_info["color"]
        self.speed = speed
        self.width = 30
        self.height = 15
        # 讓道具從磚塊中心掉落
        self.rect = pygame.Rect(x - self.width // 2, y - self.height // 2, self.width, self.height)
        self.active = True
        self.creation_time = time.time() # 用於某些不需要持續時間的道具效果觸發

    def move(self):
        self.y += self.speed
        self.rect.y = self.y

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=3)
        # 簡單用文字標示道具類型 (可選)
        # text_surf = font.render(self.type_name[0:2], True, (0,0,0)) # 例如顯示前兩個字母
        # screen.blit(text_surf, (self.rect.centerx - text_surf.get_width() // 2, self.rect.centery - text_surf.get_height() // 2))


class BrickBreakerGame:
    """打磚塊遊戲類別 (增強版)"""

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於聲音反饋

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
        self.GRAY = (100, 100, 100) # 用於多重打擊磚塊
        self.LIGHT_BLUE = (173, 216, 230)
        self.PINK = (255, 192, 203)
        self.LIGHT_GREEN = (144, 238, 144)
        self.DARK_RED = (139, 0, 0)
        self.DARK_GRAY = (70, 70, 70)      # 用於爆炸磚塊
        self.GOLD = (255,215,0)            # 用於標記爆炸磚塊

        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60        # 球和板的初始參數
        self.initial_paddle_width = 100
        self.paddle_width = self.initial_paddle_width # 可變的板寬度
        self.paddle_height = 15
        self.paddle_speed = 8  # 板的移動速度
        self.ball_radius = 8
        self.initial_ball_speed = 4.5 # 稍微降低初始速度
        self.ball_speed = self.initial_ball_speed # 可變的球速
        self.max_ball_speed = 12 # 球的最大速度

        # 磚塊參數
        self.brick_width = (self.width - 100 - (9*2)) // 10
        self.brick_height = 20
        self.brick_rows = 5
        self.brick_cols = 10
        self.brick_gap = 2
        self.explosion_radius = self.brick_width * 1.6 # 爆炸磚塊的影響半徑

        # 聲音計時
        self.last_paddle_hit_time = 0
        self.last_brick_hit_time = 0
        self.last_wall_hit_time = 0
        self.last_power_up_sound_time = 0


        # 道具系統
        self.power_ups = []
        self.power_up_drop_chance = 0.20 # 20% 的機率掉落道具
        self.power_up_definitions = {
            # 類型: {顏色, 持續時間(幀), 音效頻率, (可選)效果值}
            "PADDLE_GROW": {"color": self.LIGHT_BLUE, "duration": 10 * self.fps, "sound_freq": 700, "value": 1.5},
            "PADDLE_SHRINK": {"color": self.DARK_RED, "duration": 8 * self.fps, "sound_freq": 300, "value": 0.66},
            "BALL_SPEED_UP": {"color": self.PINK, "duration": 10 * self.fps, "sound_freq": 800, "value": 1.3},
            "BALL_SPEED_DOWN": {"color": self.BLUE, "duration": 8 * self.fps, "sound_freq": 250, "value": 0.7},
            "EXTRA_LIFE": {"color": self.LIGHT_GREEN, "duration": 0, "sound_freq": 900},
            # "MULTI_BALL": {"color": self.GOLD, "duration": 0, "sound_freq": 1000}, # 未來可擴展
        }
        self.active_power_up_effects = {} # 儲存活動中的有時限道具及其剩餘時間

        # 初始化字型
        self.init_font()

        # 初始化遊戲狀態
        self.current_level = 0 # 從0開始，第一次create_bricks會變1
        self.reset_game()

    def init_font(self):
        """初始化字型（簡化為英文版）。"""
        try:
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24) # 用於道具等較小文字
            print("成功載入預設字型。")
        except Exception as e:
            print(f"無法載入預設字型，錯誤: {e}")
            try:
                self.font = pygame.font.SysFont("arial", 30)
                self.small_font = pygame.font.SysFont("arial", 20)
                print("使用系統 Arial 字型作為備用。")
            except Exception as e_sys:
                print(f"無法載入系統 Arial 字型: {e_sys}。文字可能無法渲染。")
                self.font = None
                self.small_font = None

    def reset_game(self, new_level=True):
        """重置遊戲狀態"""
        if new_level:
            self.current_level += 1

        # 板的初始位置
        self.paddle_x = (self.width - self.paddle_width) // 2
        self.paddle_y = self.height - 40

        # 重置板和球的屬性到初始值
        self.paddle_width = self.initial_paddle_width
        # 根據關卡稍微增加基礎球速，但受最大速度限制
        self.ball_speed = min(self.initial_ball_speed + (self.current_level -1) * 0.25, self.max_ball_speed)


        # 球的初始位置和速度
        self.ball_x = self.width // 2
        self.ball_y = self.paddle_y - self.ball_radius -1

        angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
        self.ball_dx = self.ball_speed * math.cos(angle)
        self.ball_dy = self.ball_speed * math.sin(angle)

        # 遊戲狀態
        if new_level and self.current_level == 1 : # 只有在全新遊戲開始時才重置分數和生命
             self.score = 0
             self.lives = 3
        elif not new_level: # 例如失去生命後的重置
            pass


        self.game_over = False
        self.paused = False
        self.ball_launched = False

        self.power_ups.clear()
        self.active_power_up_effects.clear()


        # 建立磚塊
        self.create_bricks()

    def handle_ball_paddle_collision(self):
        """處理球與板的碰撞，包含改進的反彈角度和聲音。"""
        current_time = time.time()
        offset = (self.ball_x - (self.paddle_x + self.paddle_width / 2)) / (self.paddle_width / 2)
        offset = max(-1.0, min(1.0, offset))
        max_bounce_angle_rad = math.pi * (5/12)
        bounce_angle_rad = offset * max_bounce_angle_rad

        current_abs_speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
        if current_abs_speed == 0: # 避免除以零，如果速度為零則使用預設速度
            current_abs_speed = self.ball_speed

        self.ball_dx = current_abs_speed * math.sin(bounce_angle_rad)
        self.ball_dy = -current_abs_speed * math.cos(bounce_angle_rad) # 負值表示向上移動

        if self.buzzer and current_time - self.last_paddle_hit_time > 0.05:
            base_freq = 400
            freq_variation = int(offset * 100)
            self.buzzer.play_tone(frequency=base_freq + freq_variation, duration=0.08)
            self.last_paddle_hit_time = current_time

        self.ball_y = self.paddle_y - self.ball_radius - 0.1

    def move_paddle(self, direction):
        """移動板子"""
        if direction == "left":
            self.paddle_x = max(0, self.paddle_x - self.paddle_speed)
        elif direction == "right":
            # 檢查是否有寬板道具效果
            current_width = self.paddle_width
            if hasattr(self, 'active_power_up_effects') and 'PADDLE_GROW' in self.active_power_up_effects:
                current_width = self.paddle_width * self.power_up_definitions['PADDLE_GROW']['value']
            self.paddle_x = min(self.width - current_width, self.paddle_x + self.paddle_speed)

    def handle_ball_brick_collision(self, brick_idx):
        """處理球與磚塊的碰撞，計算分數和聲音。"""
        brick = self.bricks[brick_idx]
        current_time = time.time()

        score_values = {'red': 50, 'orange': 40, 'yellow': 30, 'green': 20, 'blue': 10, 'gray': 15, 'exploding': 25}
        self.score += score_values.get(brick['type'], 10)

        if self.buzzer and current_time - self.last_brick_hit_time > 0.05:
            freq_map = {'red': 1000, 'orange': 900, 'yellow': 800, 'green': 700, 'blue': 600, 'gray': 750, 'exploding': 850}
            frequency = freq_map.get(brick['type'], 500)
            self.buzzer.play_tone(frequency=frequency, duration=0.08)
            self.last_brick_hit_time = current_time

        brick['remaining_hits'] -= 1
        if brick['remaining_hits'] <= 0:
            brick['active'] = False

            # 處理爆炸磚塊
            if brick['type'] == 'exploding':
                self.trigger_explosion(brick['rect'].centerx, brick['rect'].centery)
                if self.buzzer: self.buzzer.play_tone(1500, 0.2) # 爆炸聲

            # 機率掉落道具 (非爆炸磚塊本身，避免連鎖)
            elif random.random() < self.power_up_drop_chance:
                self.spawn_power_up(brick['rect'].centerx, brick['rect'].centery)

            # 更新磚塊顏色或移除
            if brick['type'] != 'exploding': # 爆炸磚塊立即移除
                 # self.bricks.pop(brick_idx) # 在主循環中移除，避免迭代問題
                 pass # 標記為 inactive，在 update 主循環中統一移除
        else:
            # 多重打擊磚塊變色
            hit_ratio = brick['remaining_hits'] / brick['total_hits']
            r = int(brick['original_color_tuple'][0] * hit_ratio + self.GRAY[0] * (1 - hit_ratio))
            g = int(brick['original_color_tuple'][1] * hit_ratio + self.GRAY[1] * (1 - hit_ratio))
            b = int(brick['original_color_tuple'][2] * hit_ratio + self.GRAY[2] * (1 - hit_ratio))
            brick['current_color_tuple'] = (max(0,min(r,255)), max(0,min(g,255)), max(0,min(b,255)))

    def trigger_explosion(self, center_x, center_y):
        """觸發爆炸效果，摧毀範圍內的磚塊"""
        for i in range(len(self.bricks) -1, -1, -1): # 反向迭代以安全移除
            brick = self.bricks[i]
            if not brick['active']:
                continue

            dist_sq = (brick['rect'].centerx - center_x)**2 + (brick['rect'].centery - center_y)**2
            if dist_sq <= self.explosion_radius**2:
                if brick['type'] != 'exploding': # 避免連鎖爆炸視覺/音效過多
                    self.score += 10 # 爆炸摧毀的磚塊給少量分數
                brick['active'] = False # 標記為非活動，稍後移除

    def spawn_power_up(self, x, y):
        """在指定位置生成一個隨機道具"""
        chosen_type_name = random.choice(list(self.power_up_definitions.keys()))
        type_info = self.power_up_definitions[chosen_type_name]
        new_power_up = PowerUp(x, y, type_info, chosen_type_name)
        self.power_ups.append(new_power_up)

    def apply_power_up_effect(self, power_up):
        """應用道具效果"""
        effect_type = power_up.type_name
        details = power_up.type_info

        current_time = time.time()
        if self.buzzer and current_time - self.last_power_up_sound_time > 0.1:
             self.buzzer.play_tone(details["sound_freq"], 0.15)
             self.last_power_up_sound_time = current_time

        if effect_type == "PADDLE_GROW" or effect_type == "PADDLE_SHRINK":
            self.paddle_width = max(self.initial_paddle_width * 0.5, min(self.initial_paddle_width * 2, self.initial_paddle_width * details["value"]))
            self.active_power_up_effects[effect_type] = {"timer": details["duration"], "original_value": self.initial_paddle_width, "target_attr": "paddle_width"}
        elif effect_type == "BALL_SPEED_UP" or effect_type == "BALL_SPEED_DOWN":
            new_speed_multiplier = details["value"]
            # 直接調整球的當前速度向量，保持方向
            current_abs_speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
            if current_abs_speed == 0: current_abs_speed = self.ball_speed # 避免乘以0

            effective_new_speed = min(self.max_ball_speed, max(self.initial_ball_speed * 0.5, current_abs_speed * new_speed_multiplier))

            speed_ratio = effective_new_speed / current_abs_speed if current_abs_speed != 0 else 1.0

            self.ball_dx *= speed_ratio
            self.ball_dy *= speed_ratio

            # 儲存基礎速度以供恢復，而不是當前速度
            self.active_power_up_effects[effect_type] = {"timer": details["duration"], "original_value": self.ball_speed, "target_attr": "ball_speed_vector"}
        elif effect_type == "EXTRA_LIFE":
            self.lives += 1

        # 清理掉可能衝突的舊效果 (例如， paddle grow 和 paddle shrink 不能同時作用)
        if "PADDLE" in effect_type:
            for key in list(self.active_power_up_effects.keys()):
                if "PADDLE" in key and key != effect_type:
                    del self.active_power_up_effects[key]
        if "BALL_SPEED" in effect_type:
             for key in list(self.active_power_up_effects.keys()):
                if "BALL_SPEED" in key and key != effect_type:
                    # 恢復舊的速度效果的原始速度
                    old_effect = self.active_power_up_effects.pop(key)
                    # 這部分恢復邏輯需要更仔細，目前簡化為只允許一個速度效果
                    # 理想情況是基於一個 'base_ball_speed' 調整
                    pass # 新的速度效果會覆蓋舊的

    def update_active_power_ups(self):
        """更新活動中道具效果的計時器，並在到期時恢復屬性"""
        keys_to_remove = []
        for effect_type, data in self.active_power_up_effects.items():
            data["timer"] -= 1
            if data["timer"] <= 0:
                keys_to_remove.append(effect_type)
                # 恢復屬性
                if data["target_attr"] == "paddle_width":
                    self.paddle_width = self.initial_paddle_width # 直接恢復到初始寬度
                elif data["target_attr"] == "ball_speed_vector":
                    # 恢復到基礎速度，方向不變
                    current_direction_dx = self.ball_dx
                    current_direction_dy = self.ball_dy
                    magnitude = math.sqrt(current_direction_dx**2 + current_direction_dy**2)
                    if magnitude > 0:
                        # self.ball_speed 是關卡基礎速度
                        normalized_dx = current_direction_dx / magnitude
                        normalized_dy = current_direction_dy / magnitude
                        self.ball_dx = normalized_dx * self.ball_speed
                        self.ball_dy = normalized_dy * self.ball_speed

        for key in keys_to_remove:
            del self.active_power_up_effects[key]


    def create_bricks(self):
        """建立磚塊，包含顏色層次、不同耐久度和特殊磚塊。"""
        self.bricks = []
        # (Pygame 顏色, 字串類型, 耐久度, 是否為特殊磚塊)
        # 調整定義，加入爆炸磚塊
        base_brick_definitions = [
            (self.RED, 'red', 3),
            (self.ORANGE, 'orange', 2),
            (self.YELLOW, 'yellow', 1),
            (self.GREEN, 'green', 1),
            (self.BLUE, 'blue', 1)
        ]

        # 根據關卡增加爆炸磚塊數量
        num_exploding_bricks = min(self.brick_cols // 2, 1 + self.current_level // 2)
        exploding_brick_def = (self.DARK_GRAY, 'exploding', 1)

        total_gap_width = (self.brick_cols - 1) * self.brick_gap
        available_width_for_bricks = self.width - 100
        self.brick_width = (available_width_for_bricks - total_gap_width) / self.brick_cols

        brick_positions = []
        for row in range(self.brick_rows):
            for col in range(self.brick_cols):
                brick_positions.append((row, col))

        random.shuffle(brick_positions) # 打亂位置以便隨機分配爆炸磚塊

        exploding_assigned_count = 0
        for i, (row, col) in enumerate(brick_positions):
            is_exploding = False
            if exploding_assigned_count < num_exploding_bricks and i < len(brick_positions) * 0.5: # 嘗試在前50%的位置分配
                # 簡單的隨機分配策略
                if random.random() < (num_exploding_bricks / (len(brick_positions) * 0.5)):
                    brick_color, brick_type, brick_hits = exploding_brick_def
                    is_exploding = True
                    exploding_assigned_count += 1
                else: # 隨機選擇一個普通磚塊定義
                    def_idx = row % len(base_brick_definitions) # 按行分配基礎類型
                    brick_color, brick_type, brick_hits = base_brick_definitions[def_idx]
            else: # 分配普通磚塊
                def_idx = row % len(base_brick_definitions)
                brick_color, brick_type, brick_hits = base_brick_definitions[def_idx]


            brick_x = 50 + col * (self.brick_width + self.brick_gap)
            brick_y = 50 + row * (self.brick_height + self.brick_gap)

            brick = {
                'x': brick_x, 'y': brick_y,
                'width': self.brick_width, 'height': self.brick_height,
                'rect': pygame.Rect(brick_x, brick_y, self.brick_width, self.brick_height),
                'original_color_tuple': brick_color,
                'current_color_tuple': brick_color,
                'type': brick_type,
                'active': True,
                'total_hits': brick_hits,
                'remaining_hits': brick_hits,
                'is_exploding_visual': is_exploding # 用於渲染時的特殊標記
            }
            self.bricks.append(brick)

        # 確保至少有一個磚塊（如果上面邏輯有誤）
        if not self.bricks and self.brick_rows > 0 and self.brick_cols > 0:
             print("Warning: No bricks created, forcing one default brick.") # 開發時的警告
             brick_color, brick_type, brick_hits = base_brick_definitions[0]
             brick_x = 50 + 0 * (self.brick_width + self.brick_gap)
             brick_y = 50 + 0 * (self.brick_height + self.brick_gap)
             self.bricks.append({
                'x': brick_x, 'y': brick_y,
                'width': self.brick_width, 'height': self.brick_height,
                'rect': pygame.Rect(brick_x, brick_y, self.brick_width, self.brick_height),
                'original_color_tuple': brick_color, 'current_color_tuple': brick_color,
                'type': brick_type, 'active': True, 'total_hits': brick_hits, 'remaining_hits': brick_hits,
                'is_exploding_visual': False
            })


    def update(self, controller_input=None):
        """更新遊戲狀態。"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.paused = False
                    self.last_start_press_time = time.time()
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "level": self.current_level}

        # 更新活動中的道具效果
        self.update_active_power_ups()

        # 處理輸入
        if controller_input:
            # 初始化搖桿參數
            if not hasattr(self, 'stick_threshold'):
                self.stick_threshold = 0.3  # 連續移動的閾值
                self.stick_speed_multiplier = 1.0  # 調整搖桿靈敏度

            # 左搖桿輸入處理（連續移動）
            stick_x = controller_input.get("left_stick_x", 0.0)
              # 應用搖桿移動（帶縮放）
            if abs(stick_x) > self.stick_threshold:
                # 根據搖桿偏移縮放移動量
                movement_amount = self.paddle_speed * (abs(stick_x) * self.stick_speed_multiplier)
                if stick_x < -self.stick_threshold:  # 向左
                    self.paddle_x = max(0, self.paddle_x - movement_amount)
                elif stick_x > self.stick_threshold:  # 向右
                    # 檢查是否有板子變大的道具效果
                    current_width = self.paddle_width
                    if 'PADDLE_GROW' in self.active_power_up_effects:
                        current_width = self.paddle_width * self.power_up_definitions['PADDLE_GROW']['value']
                    self.paddle_x = min(self.width - current_width, self.paddle_x + movement_amount)

            # D-pad 輸入（保留原有邏輯，優先級較高）
            if controller_input.get("left_pressed"):
                self.move_paddle("left")
            if controller_input.get("right_pressed"):
                self.move_paddle("right")

            # 發射球
            if controller_input.get("a_pressed"):
                self.ball_launched = True
                if self.buzzer: self.buzzer.play_tone(frequency=600, duration=0.1)

            # 暫停控制
            if controller_input.get("start_pressed"):
                if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    self.paused = not self.paused
                    self.last_start_press_time = time.time()
                    if self.buzzer: self.buzzer.play_tone(frequency=500, duration=0.1)
                    return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "level": self.current_level}

        if not self.ball_launched:
            self.ball_x = self.paddle_x + self.paddle_width // 2
            self.ball_y = self.paddle_y - self.ball_radius - 1
            # 更新道具位置
            for power_up in self.power_ups: power_up.move()
            self.power_ups = [p for p in self.power_ups if p.active and p.rect.top < self.height]

            return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "level": self.current_level}

        ball_prev_x = self.ball_x
        ball_prev_y = self.ball_y

        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # 牆壁碰撞
        current_time = time.time()
        wall_hit_sound_delay = 0.1
        if self.ball_x <= self.ball_radius:
            self.ball_x = self.ball_radius
            self.ball_dx = -self.ball_dx
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05)
                self.last_wall_hit_time = current_time
        elif self.ball_x >= self.width - self.ball_radius:
            self.ball_x = self.width - self.ball_radius
            self.ball_dx = -self.ball_dx
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05)
                self.last_wall_hit_time = current_time

        if self.ball_y <= self.ball_radius:
            self.ball_y = self.ball_radius
            self.ball_dy = -self.ball_dy
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05)
                self.last_wall_hit_time = current_time

        # 球未接住
        if self.ball_y >= self.height - self.ball_radius:
            self.lives -= 1
            if self.buzzer: self.buzzer.play_tone(frequency=150, duration=0.5)

            if self.lives <= 0:
                self.game_over = True
                if self.buzzer: self.buzzer.play_tone(frequency=100, duration=1.0)
            else:
                self.reset_game(new_level=False) # 重置球和板，但不重置關卡和分數
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "level": self.current_level}

        # 球與板碰撞
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        ball_rect = pygame.Rect(self.ball_x - self.ball_radius, self.ball_y - self.ball_radius,
                                self.ball_radius * 2, self.ball_radius * 2)

        if ball_rect.colliderect(paddle_rect) and self.ball_dy > 0:
            self.handle_ball_paddle_collision()

        # 球與磚塊碰撞
        collided_brick_this_frame = False
        for i in range(len(self.bricks) -1, -1, -1): # 反向迭代以便安全操作（儘管移除在後面）
            brick = self.bricks[i]
            if not brick['active'] or collided_brick_this_frame:
                continue

            if ball_rect.colliderect(brick['rect']):
                self.handle_ball_brick_collision(i) # 傳遞索引
                collided_brick_this_frame = True # 每幀只處理一次磚塊碰撞，避免多次反彈

                # --- 改進的磚塊反彈邏輯 ---
                time_to_coll_x = float('inf')
                if self.ball_dx > 0:
                    if ball_prev_x + self.ball_radius <= brick['rect'].left : # 確保是從外部碰撞
                       time_to_coll_x = (brick['rect'].left - (ball_prev_x + self.ball_radius)) / self.ball_dx if self.ball_dx != 0 else float('inf')
                elif self.ball_dx < 0:
                    if ball_prev_x - self.ball_radius >= brick['rect'].right:
                       time_to_coll_x = (brick['rect'].right - (ball_prev_x - self.ball_radius)) / self.ball_dx if self.ball_dx != 0 else float('inf')

                time_to_coll_y = float('inf')
                if self.ball_dy > 0:
                    if ball_prev_y + self.ball_radius <= brick['rect'].top:
                       time_to_coll_y = (brick['rect'].top - (ball_prev_y + self.ball_radius)) / self.ball_dy if self.ball_dy != 0 else float('inf')
                elif self.ball_dy < 0:
                    if ball_prev_y - self.ball_radius >= brick['rect'].bottom:
                       time_to_coll_y = (brick['rect'].bottom - (ball_prev_y - self.ball_radius)) / self.ball_dy if self.ball_dy != 0 else float('inf')

                time_to_coll_x = max(0, time_to_coll_x if time_to_coll_x is not None else float('inf'))
                time_to_coll_y = max(0, time_to_coll_y if time_to_coll_y is not None else float('inf'))

                # 檢查碰撞是否發生在當前影格內 (時間 < 1.0)
                # 且球是朝向磚塊移動的
                if time_to_coll_x < time_to_coll_y and time_to_coll_x < 1.0 :
                    original_dx = self.ball_dx
                    self.ball_dx = -self.ball_dx
                    if original_dx > 0: # 向右移動，撞到左邊
                         self.ball_x = brick['rect'].left - self.ball_radius - 0.1
                    else: # 向左移動，撞到右邊
                         self.ball_x = brick['rect'].right + self.ball_radius + 0.1
                elif time_to_coll_y < time_to_coll_x and time_to_coll_y < 1.0:
                    original_dy = self.ball_dy
                    self.ball_dy = -self.ball_dy
                    if original_dy > 0: # 向下移動，撞到頂部
                        self.ball_y = brick['rect'].top - self.ball_radius - 0.1
                    else: # 向上移動，撞到底部
                        self.ball_y = brick['rect'].bottom + self.ball_radius + 0.1
                else: # 角落碰撞或同時碰撞 - 簡單回退
                    # 如果球卡住了，這個回退可能不夠完美
                    overlap_x = (self.ball_radius + brick['rect'].width / 2) - abs(self.ball_x - brick['rect'].centerx)
                    overlap_y = (self.ball_radius + brick['rect'].height / 2) - abs(self.ball_y - brick['rect'].centery)

                    # 檢查球的先前位置是否已經在磚塊內，避免錯誤反彈
                    was_inside_x = ball_prev_x > brick['rect'].left and ball_prev_x < brick['rect'].right
                    was_inside_y = ball_prev_y > brick['rect'].top and ball_prev_y < brick['rect'].bottom

                    if not (was_inside_x and was_inside_y): # 只有當球不是從內部開始時才進行簡單反彈
                        if overlap_x < overlap_y :
                            if (self.ball_y < brick['rect'].centery and self.ball_dy > 0) or \
                               (self.ball_y > brick['rect'].centery and self.ball_dy < 0):
                                self.ball_dy = -self.ball_dy
                        else:
                            if (self.ball_x < brick['rect'].centerx and self.ball_dx > 0) or \
                               (self.ball_x > brick['rect'].centerx and self.ball_dx < 0):
                                self.ball_dx = -self.ball_dx
                break

        # 移除非活動的磚塊
        self.bricks = [b for b in self.bricks if b['active']]

        # 更新和處理道具
        for p_idx in range(len(self.power_ups) -1, -1, -1):
            power_up = self.power_ups[p_idx]
            power_up.move()
            if power_up.rect.colliderect(paddle_rect):
                self.apply_power_up_effect(power_up)
                power_up.active = False # 標記為非活動

            if not power_up.active or power_up.rect.top > self.height:
                self.power_ups.pop(p_idx)


        # 檢查是否清空關卡
        if not self.bricks:
            self.score += 100 * self.current_level # 過關獎勵隨關卡增加
            self.reset_game(new_level=True) # 進入下一關
            if self.buzzer:
                for freq in [600, 750, 900, 1050]:
                    self.buzzer.play_tone(frequency=freq, duration=0.06)
                    time.sleep(0.04)

        return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "level": self.current_level}

    def render(self, screen):
        """渲染遊戲畫面。"""
        screen.fill(self.BLACK)

        paddle_rect_obj = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        pygame.draw.rect(screen, self.GREEN, paddle_rect_obj, border_radius=3) # 板子改為綠色

        pygame.draw.circle(screen, self.WHITE, (int(self.ball_x), int(self.ball_y)), self.ball_radius)

        for brick in self.bricks:
            if brick['active']:
                pygame.draw.rect(screen, brick['current_color_tuple'], brick['rect'])
                pygame.draw.rect(screen, self.BLACK, brick['rect'], 1)
                if brick.get('is_exploding_visual', False) and self.small_font: # 標記爆炸磚塊
                    pygame.draw.circle(screen, self.GOLD, brick['rect'].center, 4)


        for power_up in self.power_ups:
            if power_up.active:
                power_up.draw(screen, self.small_font) # 傳入字型供道具繪製文字 (可選)

        if self.font:
            score_surf = self.font.render(f"Score: {self.score}", True, self.WHITE)
            lives_surf = self.font.render(f"Lives: {self.lives}", True, self.WHITE)
            level_surf = self.font.render(f"Level: {self.current_level}", True, self.WHITE)
            screen.blit(score_surf, (10, 10))
            screen.blit(lives_surf, (self.width - lives_surf.get_width() - 10, 10))
            screen.blit(level_surf, (self.width // 2 - level_surf.get_width() // 2, 10))


            if not self.ball_launched and not self.game_over:
                hint_surf = self.font.render("Press A to Launch Ball", True, self.YELLOW)
                screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, self.height - 70))

            # 顯示活動中的道具效果 (可選)
            y_offset = 40
            for effect_type_full, data in self.active_power_up_effects.items():
                if data['timer'] > 0: #  and data.get('duration',0) > 0 : # 只顯示有時限的
                    # 從 effect_type_full (e.g., PADDLE_GROW_1622...) 提取基礎類型 PADDLE_GROW
                    base_effect_type = "_".join(effect_type_full.split('_')[:2]) if len(effect_type_full.split('_')) > 1 else effect_type_full

                    effect_text = f"{base_effect_type}: {data['timer'] // self.fps + 1}s"
                    color_to_use = self.WHITE # 預設顏色
                    if base_effect_type in self.power_up_definitions:
                        color_to_use = self.power_up_definitions[base_effect_type]["color"]

                    text_surf = self.small_font.render(effect_text, True, color_to_use)
                    screen.blit(text_surf, (10, y_offset))
                    y_offset += 20


        else:
            pygame.draw.rect(screen, self.RED, (10,10,100,20))
            pygame.draw.rect(screen, self.RED, (self.width-110,10,100,20))

        if self.game_over:
            self.draw_game_over_screen(screen)
        elif self.paused:
            self.draw_pause_screen(screen)

    def draw_game_over_screen(self, screen):
        """繪製遊戲結束畫面。"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        if self.font:
            game_over_surf = self.font.render("Game Over!", True, self.RED)
            final_score_surf = self.font.render(f"Final Score: {self.score} (Level {self.current_level})", True, self.WHITE)
            restart_surf = self.font.render("Press Start to Restart", True, self.WHITE)

            screen.blit(game_over_surf, (self.width // 2 - game_over_surf.get_width() // 2, self.height // 2 - 60))
            screen.blit(final_score_surf, (self.width // 2 - final_score_surf.get_width() // 2, self.height // 2 - 10))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 40))

    def draw_pause_screen(self, screen):
        """繪製暫停畫面。"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        if self.font:
            pause_surf = self.font.render("Paused", True, self.YELLOW)
            continue_surf = self.font.render("Press Start to Continue", True, self.WHITE)
            screen.blit(pause_surf, (self.width // 2 - pause_surf.get_width() // 2, self.height // 2 - 40))
            screen.blit(continue_surf, (self.width // 2 - continue_surf.get_width() // 2, self.height // 2 + 10))

    def cleanup(self):
        """清理遊戲資源（若有）。"""
        pass


# 測試函數 - 當腳本直接執行時運行
if __name__ == "__main__":
    try:
        pygame.init()
        screen_width_main = 800
        screen_height_main = 600
        main_screen = pygame.display.set_mode((screen_width_main, screen_height_main))
        pygame.display.set_caption("Brick Breaker Game Test (Enhanced)")

        game_instance = BrickBreakerGame(screen_width_main, screen_height_main) # buzzer=None for test

        key_mapping = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_SPACE: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }

        game_running = True
        game_clock = pygame.time.Clock()

        while game_running:
            controller_input = {action: False for action in key_mapping.values()}
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False

            pressed_keys = pygame.key.get_pressed()
            for key_code, action_name in key_mapping.items():
                if pressed_keys[key_code]:
                    controller_input[action_name] = True

            game_state = game_instance.update(controller_input)
            game_instance.render(main_screen)
            pygame.display.flip()
            game_clock.tick(game_instance.fps)

        game_instance.cleanup()
        pygame.quit()

    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()