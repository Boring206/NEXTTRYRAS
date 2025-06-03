#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game3.py - Space Invaders Game Implementation (Enhanced)
# game3.py - 太空侵略者遊戲實作（增強版）

import random
import pygame
import time
from pygame.locals import *

class SpaceInvadersGame:
    """Space Invaders Game Class (Enhanced)"""
    # 太空侵略者遊戲類別（增強版）

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width      # 遊戲區域寬度
        self.height = height    # 遊戲區域高度
        self.buzzer = buzzer    # 蜂鳴器實例，用於聲音反饋

        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (128, 0, 128) # 用於UFO
        self.CYAN = (0, 255, 255)   # 用於道具

        # 遊戲元素尺寸
        self.player_width = 50
        self.player_height = 30
        self.enemy_width = 40
        self.enemy_height = 30
        self.bullet_width = 5
        self.bullet_height = 15
        self.enemy_bullet_width = 4 # 稍微加粗一點
        self.enemy_bullet_height = 12

        # UFO 尺寸
        self.ufo_width = 55
        self.ufo_height = 25

        # 掩體方塊尺寸
        self.barrier_block_size = 8
        self.initial_barrier_block_health = 5 # 掩體方塊初始生命值

        # 道具尺寸
        self.power_up_width = 25
        self.power_up_height = 25

        # 遊戲速度設定
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player_speed = 5
        self.bullet_speed = 8 # 稍微加快玩家子彈
        self.enemy_speed_x_initial = 1.5 # 初始敵人X軸速度
        self.enemy_speed_x = self.enemy_speed_x_initial
        self.enemy_speed_y = 15 # 敵人向下移動的距離
        self.enemy_bullet_speed = 5 # 稍微加快敵人子彈
        self.ufo_speed = 2.5

        # 字型初始化
        try:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
            print("字型載入成功。")
        except Exception as e:
            print(f"字型載入失敗: {e}")
            # 如果預設字型載入失敗，嘗試使用系統字型
            self.font_large = pygame.font.SysFont("arial", 68) # 使用常見的系統字型 Arial
            self.font_medium = pygame.font.SysFont("arial", 32)
            self.font_small = pygame.font.SysFont("arial", 20)

        # 初始化遊戲狀態
        self.shot_delay_normal = 0.5  # 正常射擊間隔 (秒)
        self.shot_delay_rapid_fire = 0.15 # 快速射擊間隔
        self.reset_game()

    def reset_game(self):
        """重置遊戲狀態"""
        self.player_x = (self.width - self.player_width) // 2
        self.player_y = self.height - 60 # 調整玩家Y軸起始位置

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.enemy_direction = 1 # 敵人移動方向，1為右，-1為左
        self.enemy_speed_x = self.enemy_speed_x_initial

        self.last_shot_time = 0 # 上次射擊時間
        self.shot_delay = self.shot_delay_normal # 當前射擊間隔

        self.enemy_shot_timer = 0 # 敵人射擊計時器
        self.enemy_shot_interval_initial = 70 # 初始敵人射擊間隔 (幀)
        self.enemy_shot_interval = self.enemy_shot_interval_initial

        self.wave = 1 # 目前波數
        self.score = 0 # 分數
        self.lives = 3 # 生命值

        self.game_over = False # 遊戲是否結束
        self.paused = False    # 遊戲是否暫停

        self.create_enemies()  # 建立敵人
        self.create_barriers() # 建立掩體

        # UFO 重置
        self.ufo = None        # 目前的UFO物件
        self.ufo_active = False # UFO是否在畫面上活動
        self.ufo_spawn_timer = 0 # UFO出現計時器
        # 稍微提早UFO出現時間
        self.ufo_spawn_interval = random.randint(int(8 * self.fps), int(15 * self.fps)) # UFO出現間隔
        self.ufo_y_pos = 50 # UFO出現的Y軸位置

        # 道具重置
        self.power_ups = [] # 畫面上活動的道具列表
        self.active_power_up_type = None # 目前啟動的道具類型
        self.power_up_timer = 0          # 道具效果剩餘時間計時器
        self.power_up_duration = 7 * self.fps # 道具持續7秒

    def create_enemies(self):
        """建立敵人陣列"""
        self.enemies.clear()
        rows = 5 # 敵人列數
        cols = 10 # 敵人行數 (增加敵人數量)
        
        # 根據波數調整敵人屬性
        extra_health_per_wave = self.wave // 3 # 每3波增加一點血量
        
        for row in range(rows):
            for col in range(cols):
                x = col * (self.enemy_width + 10) + 30 # 調整起始X和間距
                y = row * (self.enemy_height + 10) + 80 # 調整起始Y，使其更靠上
                
                enemy_type = min(row, 2) # 敵人類型，影響外觀和基礎血量
                
                self.enemies.append({
                    'rect': pygame.Rect(x, y, self.enemy_width, self.enemy_height), # 敵人的矩形區域
                    'type': enemy_type, # 敵人類型
                    'health': enemy_type + 1 + extra_health_per_wave, # 敵人生命值
                    'original_health': enemy_type + 1 + extra_health_per_wave # 原始生命值，用於計算顏色變化
                })

    def create_barriers(self):
        """建立掩體"""
        self.barrier_blocks = [] # 儲存所有掩體方塊的列表
        num_barriers = 4 # 掩體數量
        # barrier_width_units = 6 # 每個掩體的寬度單位數 (未使用，改用 barrier_shape)
        # barrier_height_units = 4 # 每個掩體的高度單位數 (未使用，改用 barrier_shape)
        
        # 掩體形狀定義 (1 代表實心方塊, 0 代表空格)
        barrier_shape = [
            [0, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 1, 1], # 中間有個更大的洞
            [1, 0, 0, 0, 0, 1]
        ]
        barrier_width_units = len(barrier_shape[0]) # 根據形狀定義寬度
        barrier_height_units = len(barrier_shape)   # 根據形狀定義高度

        # 計算所有掩體加上間隙的總寬度，以使其居中
        total_barriers_width = num_barriers * barrier_width_units * self.barrier_block_size
        total_gaps_width = (num_barriers - 1) * (self.barrier_block_size * 3) # 每個間隙約3個方塊寬
        combined_width = total_barriers_width + total_gaps_width
        
        start_x_offset = (self.width - combined_width) // 2 # 計算第一個掩體的起始X座標

        # 掩體Y軸位置，在玩家上方一段距離
        barrier_base_y = self.player_y - self.player_height - barrier_height_units * self.barrier_block_size - 30

        for i in range(num_barriers):
            # 計算每個掩體的左上角X座標
            barrier_base_x = start_x_offset + i * (barrier_width_units * self.barrier_block_size + (self.barrier_block_size*3))
            
            for row_idx, row_data in enumerate(barrier_shape):
                for col_idx, cell in enumerate(row_data):
                    if cell == 1: # 如果形狀定義中為1，則建立一個方塊
                        block_x = barrier_base_x + col_idx * self.barrier_block_size
                        block_y = barrier_base_y + row_idx * self.barrier_block_size
                        self.barrier_blocks.append({
                            'rect': pygame.Rect(block_x, block_y, self.barrier_block_size, self.barrier_block_size),
                            'health': self.initial_barrier_block_health, # 方塊生命值
                            'max_health': self.initial_barrier_block_health # 方塊最大生命值
                        })

    def move_player(self, direction_key):
        """移動玩家飛船"""
        if direction_key == "left":
            self.player_x = max(0, self.player_x - self.player_speed) # 向左移動，不超出左邊界
        elif direction_key == "right":
            self.player_x = min(self.width - self.player_width, self.player_x + self.player_speed) # 向右移動，不超出右邊界

    def shoot(self):
        """玩家射擊"""
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_delay: # 檢查射擊冷卻時間
            # 子彈從玩家飛船中央頂部射出
            bullet_x = self.player_x + (self.player_width // 2) - (self.bullet_width // 2)
            bullet_y = self.player_y
            self.bullets.append(pygame.Rect(bullet_x, bullet_y, self.bullet_width, self.bullet_height))
            self.last_shot_time = current_time # 更新上次射擊時間
            if self.buzzer:
                self.buzzer.play_tone(frequency=1000, duration=0.05) # 玩家射擊音效

    def enemy_shoot(self):
        """敵人射擊"""
        self.enemy_shot_timer += 1 # 增加敵人射擊計時器
        if self.enemy_shot_timer >= self.enemy_shot_interval: # 達到射擊間隔
            self.enemy_shot_timer = 0 # 重置計時器
            if self.enemies: # 如果還有敵人
                # 嘗試讓下方的敵人優先射擊，增加遊戲挑戰性
                shooters_in_column = {} # 儲存每一列最下方的敵人
                for enemy in self.enemies:
                    col_key = enemy['rect'].x // (self.enemy_width + 10) # 簡單的列索引計算
                    # 如果該列還沒有記錄敵人，或者當前敵人比已記錄的更下方，則更新
                    if col_key not in shooters_in_column or enemy['rect'].y > shooters_in_column[col_key]['rect'].y:
                        shooters_in_column[col_key] = enemy
                
                if shooters_in_column: # 如果找到了可射擊的敵人
                    shooter = random.choice(list(shooters_in_column.values())) # 從這些最下方的敵人中隨機選一個
                    # 子彈從選定敵人的中央底部射出
                    bullet_x = shooter['rect'].centerx - (self.enemy_bullet_width // 2)
                    bullet_y = shooter['rect'].bottom
                    self.enemy_bullets.append(pygame.Rect(bullet_x, bullet_y, self.enemy_bullet_width, self.enemy_bullet_height))
                    # 可在此添加敵人射擊音效
                    if self.buzzer: self.buzzer.play_tone(frequency=300, duration=0.08) # 敵人射擊音效


    def update_bullets(self):
        """更新所有子彈位置並移除螢幕外的子彈"""
        # 更新玩家子彈 (向上移動)
        for bullet in self.bullets[:]: # 使用切片副本以安全移除
            bullet.y -= self.bullet_speed
            if bullet.bottom < 0: # 如果子彈超出螢幕頂部
                self.bullets.remove(bullet)

        # 更新敵人子彈 (向下移動)
        for bullet in self.enemy_bullets[:]: # 使用切片副本以安全移除
            bullet.y += self.enemy_bullet_speed
            if bullet.top > self.height: # 如果子彈超出螢幕底部
                self.enemy_bullets.remove(bullet)

    def update_enemies(self):
        """更新敵人位置，處理邊界碰撞和觸底"""
        if not self.enemies: # 如果沒有敵人了，直接返回
            return

        move_down = False # 標記敵人是否需要向下移動
        current_enemy_speed = self.enemy_speed_x * self.enemy_direction # 當前敵人X軸移動速度和方向

        # 檢查是否有敵人碰到左右邊界
        for enemy in self.enemies:
            if (enemy['rect'].right + current_enemy_speed > self.width and self.enemy_direction > 0) or \
               (enemy['rect'].left + current_enemy_speed < 0 and self.enemy_direction < 0):
                move_down = True # 需要向下移動並改變方向
                break
        
        if move_down: # 如果需要向下移動
            self.enemy_direction *= -1 # 改變X軸移動方向
            for enemy in self.enemies:
                enemy['rect'].y += self.enemy_speed_y # 所有敵人向下移動
        else: # 否則，正常左右移動
            for enemy in self.enemies:
                enemy['rect'].x += current_enemy_speed

        # 檢查是否有敵人觸底 (碰到玩家區域)
        for enemy in self.enemies:
            if enemy['rect'].bottom >= self.player_y - self.player_height //2 : # 稍微調整觸底判斷
                self.game_over = True # 遊戲結束
                if self.buzzer: self.buzzer.play_tone(sound_name="game_over_melody_invaders") # 播放遊戲結束音效
                return # 遊戲結束，無需進一步處理

    def update_ufo(self):
        """更新UFO的出現和移動"""
        if not self.ufo_active: # 如果UFO當前未活動
            self.ufo_spawn_timer += 1 # 增加UFO出現計時器
            if self.ufo_spawn_timer >= self.ufo_spawn_interval: # 達到出現間隔
                self.ufo_active = True # 啟動UFO
                self.ufo_spawn_timer = 0 # 重置計時器
                self.ufo_spawn_interval = random.randint(int(10 * self.fps), int(25 * self.fps)) # 重設下次出現間隔
                
                direction = random.choice([-1, 1]) # 隨機UFO飛行方向 (左或右)
                start_x = -self.ufo_width if direction == 1 else self.width # UFO起始X座標 (螢幕外)
                self.ufo = {
                    'rect': pygame.Rect(start_x, self.ufo_y_pos, self.ufo_width, self.ufo_height),
                    'direction': direction, # UFO飛行方向
                    'score': random.choice([50, 100, 150, 200, 300]) # UFO分數
                }
                if self.buzzer: self.buzzer.play_tone(sound_name="ufo_flying_sound", loop=True) # 播放UFO飛行音效 (循環)
        else: # 如果UFO已活動
            if self.ufo:
                self.ufo['rect'].x += self.ufo_speed * self.ufo['direction'] # UFO移動
                # 如果UFO飛出螢幕
                if (self.ufo['direction'] == 1 and self.ufo['rect'].left > self.width) or \
                   (self.ufo['direction'] == -1 and self.ufo['rect'].right < 0):
                    self.ufo_active = False # UFO變為非活動
                    self.ufo = None
                    if self.buzzer: self.buzzer.play_tone(sound_name="ufo_flying_sound", stop=True) # 停止UFO飛行音效

    def update_power_ups(self):
        """更新道具位置和效果計時"""
        # 移動畫面上所有道具 (向下掉落)
        for pu in self.power_ups[:]: # 使用切片副本以安全移除
            pu['rect'].y += 2 # 道具下降速度
            if pu['rect'].top > self.height: # 如果道具掉出螢幕
                self.power_ups.remove(pu)

        # 如果有啟動中的道具效果
        if self.active_power_up_type:
            self.power_up_timer -= 1 # 減少道具效果剩餘時間
            if self.power_up_timer <= 0: # 如果效果時間到
                if self.active_power_up_type == "rapid_fire": # 如果是快速射擊道具
                    self.shot_delay = self.shot_delay_normal # 恢復正常射擊間隔
                self.active_power_up_type = None # 清除啟動的道具類型
                if self.buzzer: self.buzzer.play_tone(sound_name="power_down_sound") # 播放道具效果結束音效


    def check_collisions(self):
        """檢查各種碰撞"""
        # 玩家子彈 vs 敵人
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.colliderect(enemy['rect']): # 如果子彈碰到敵人
                    if bullet in self.bullets: self.bullets.remove(bullet) # 移除子彈
                    enemy['health'] -= 1 # 敵人生命值減少
                    if enemy['health'] <= 0: # 如果敵人生命值耗盡
                        self.enemies.remove(enemy) # 移除敵人
                        self.score += (enemy['type'] + 1) * 10 * self.wave # 增加分數 (分數也跟波數有關)
                        if self.buzzer: self.buzzer.play_tone(frequency=600 + enemy['type']*100, duration=0.06) # 敵人被擊中音效
                    break # 一顆子彈只打一個敵人

            # 玩家子彈 vs UFO
            if self.ufo_active and self.ufo and bullet.colliderect(self.ufo['rect']): # 如果子彈碰到UFO
                if bullet in self.bullets: self.bullets.remove(bullet) # 移除子彈
                self.score += self.ufo['score'] # 增加UFO分數
                if self.buzzer:
                    self.buzzer.play_tone(sound_name="ufo_flying_sound", stop=True) # 停止UFO飛行音效
                    self.buzzer.play_tone(sound_name="ufo_hit_sound") # 播放UFO被擊中音效
                
                # UFO被擊落，掉落道具 (快速射擊)
                pu_x = self.ufo['rect'].centerx - self.power_up_width // 2
                pu_y = self.ufo['rect'].centery
                self.power_ups.append({
                    'rect': pygame.Rect(pu_x, pu_y, self.power_up_width, self.power_up_height),
                    'type': 'rapid_fire' 
                })

                self.ufo_active = False # UFO變為非活動
                self.ufo = None
                break # 子彈已消耗，無需再檢查其他碰撞

        # 敵人子彈 vs 玩家
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height) # 玩家的矩形區域
        for bullet in self.enemy_bullets[:]:
            if bullet.colliderect(player_rect): # 如果敵人子彈碰到玩家
                self.enemy_bullets.remove(bullet) # 移除子彈
                self.lives -= 1 # 玩家生命值減少
                if self.buzzer: self.buzzer.play_tone(frequency=200, duration=0.2) # 玩家被擊中音效
                if self.lives <= 0: # 如果生命值耗盡
                    self.game_over = True # 遊戲結束
                    if self.buzzer: self.buzzer.play_tone(sound_name="game_over_melody_invaders") # 播放遊戲結束音效
                return # 避免一幀內多次受傷判定

        # 子彈 (玩家和敵人) vs 掩體
        for bullet_list in [self.bullets, self.enemy_bullets]: # 遍歷玩家子彈列表和敵人子彈列表
            for bullet in bullet_list[:]:
                for block in self.barrier_blocks[:]:
                    if bullet.colliderect(block['rect']): # 如果子彈碰到掩體方塊
                        if bullet in bullet_list: bullet_list.remove(bullet) # 移除子彈
                        block['health'] -= 1 # 掩體方塊生命值減少
                        if block['health'] <= 0: # 如果掩體方塊生命值耗盡
                            self.barrier_blocks.remove(block) # 移除掩體方塊
                        # 可添加掩體被擊中音效
                        if self.buzzer: self.buzzer.play_tone(frequency=150, duration=0.03) # 掩體被擊中音效
                        break # 一顆子彈只打一個方塊，跳出內層循環

        # 玩家 vs 道具
        for pu in self.power_ups[:]:
            if player_rect.colliderect(pu['rect']): # 如果玩家碰到道具
                self.power_ups.remove(pu) # 移除道具
                if pu['type'] == 'rapid_fire': # 如果是快速射擊道具
                    self.active_power_up_type = 'rapid_fire' # 設定啟動的道具類型
                    self.shot_delay = self.shot_delay_rapid_fire # 設定為快速射擊間隔
                    self.power_up_timer = self.power_up_duration # 設定道具效果持續時間
                    if self.buzzer: self.buzzer.play_tone(sound_name="power_up_collect_sound") # 播放拾取道具音效


    def check_wave_complete(self):
        """檢查當前波是否完成"""
        if not self.enemies and not self.game_over: # 如果所有敵人都被消滅且遊戲未結束
            self.wave += 1 # 波數增加
            self.score += self.wave * 50 # 過關獎勵分數
            self.create_enemies() # 建立新一波敵人
            # self.create_barriers() # 可選擇是否每波都重置掩體 (目前不重置)
            
            # 增加遊戲難度
            self.enemy_speed_x = min(self.enemy_speed_x_initial + (self.wave -1) * 0.2, 5) # 敵人X速度隨波數增加，但有上限
            self.enemy_shot_interval = max(20, self.enemy_shot_interval_initial - self.wave * 3) # 敵人射擊間隔減少，但有下限
            
            # 清空現有子彈和道具，避免影響下一波
            self.bullets.clear()
            self.enemy_bullets.clear()
            self.power_ups.clear()
            if self.active_power_up_type == "rapid_fire": # 如果有射速提升，結束它
                 self.shot_delay = self.shot_delay_normal
                 self.active_power_up_type = None
                 self.power_up_timer = 0

            if self.buzzer: self.buzzer.play_tone(sound_name="wave_complete_sound") # 播放過關音效

    def update(self, controller_input=None):
        """更新遊戲狀態"""
        if self.game_over or self.paused: # 如果遊戲結束或暫停
            if controller_input and controller_input.get("start_pressed"):
                # 添加延遲避免因按住開始鍵而立即觸發多次
                if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    if self.game_over:
                        self.reset_game() # 如果遊戲結束，重置遊戲
                    else:
                        self.paused = False # 如果是暫停，取消暫停
                    self.last_start_press_time = time.time() # 記錄本次按下時間
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}

        # 輸入處理
        if controller_input:
            # Initialize stick parameters if not exists
            if not hasattr(self, 'stick_threshold'):
                self.stick_threshold = 0.3  # Lower threshold for continuous movement
                self.stick_speed_multiplier = 1.0  # Adjust stick sensitivity
            
            # Left stick input processing (continuous movement)
            stick_x = controller_input.get("left_stick_x", 0.0)
            stick_movement = False
            
            # Apply stick movement with scaling
            if abs(stick_x) > self.stick_threshold:
                # Scale movement based on stick deflection
                movement_amount = self.player_speed * (abs(stick_x) * self.stick_speed_multiplier)
                if stick_x < -self.stick_threshold:  # Left
                    self.player_x = max(0, self.player_x - movement_amount)
                    stick_movement = True
                elif stick_x > self.stick_threshold:  # Right
                    self.player_x = min(self.width - self.player_width, self.player_x + movement_amount)
                    stick_movement = True
            
            # D-pad input (preserve original logic, takes priority)
            d_pad_movement = False
            if controller_input.get("left_pressed"):
                self.move_player("left")
                d_pad_movement = True
            if controller_input.get("right_pressed"):
                self.move_player("right")
                d_pad_movement = True
            
            # Shooting input (both A button and stick are supported)
            if controller_input.get("a_pressed"):
                self.shoot()
            
            # Pause/Start input
            if controller_input.get("start_pressed"):
                 if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    self.paused = not self.paused # 切換暫停狀態
                    self.last_start_press_time = time.time()
                    if self.buzzer: self.buzzer.play_tone(frequency=400, duration=0.1) # 暫停音效
                    return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}
        
        # 遊戲邏輯更新
        self.update_bullets()    # 更新子彈
        self.update_enemies()    # 更新敵人
        self.enemy_shoot()       # 敵人射擊邏輯
        self.update_ufo()        # 更新UFO
        self.update_power_ups()  # 更新道具
        self.check_collisions()  # 檢查碰撞
        self.check_wave_complete() # 檢查是否過關 (必須在 collision 之後，確保敵人列表已更新)

        return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}

    def render(self, screen):
        """渲染遊戲畫面"""
        screen.fill(self.BLACK) # 以黑色填充螢幕背景

        # 繪製星空背景 (每次繪製不同，產生閃爍效果)
        for _ in range(30): # 減少星星數量，避免太花
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            pygame.draw.circle(screen, self.WHITE, (x, y), random.randint(1,2)) # 星星大小隨機

        # 繪製掩體
        for block in self.barrier_blocks:
            # 根據血量改變顏色
            health_ratio = block['health'] / block['max_health']
            if health_ratio > 0.6: color = self.GREEN
            elif health_ratio > 0.3: color = self.YELLOW
            else: color = self.RED
            pygame.draw.rect(screen, color, block['rect'])

        # 繪製玩家飛船 (三角形)
        player_points = [
            (self.player_x, self.player_y + self.player_height),
            (self.player_x + self.player_width // 2, self.player_y),
            (self.player_x + self.player_width, self.player_y + self.player_height)
        ]
        pygame.draw.polygon(screen, self.GREEN, player_points)
        # 繪製一個小駕駛艙
        cockpit_rect = pygame.Rect(self.player_x + self.player_width // 2 - 5, self.player_y + self.player_height // 2 -3 , 10, 6)
        pygame.draw.rect(screen, self.CYAN, cockpit_rect)


        # 繪製玩家子彈
        for bullet in self.bullets:
            pygame.draw.rect(screen, self.BLUE, bullet)

        # 繪製敵人子彈
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, self.RED, bullet)

        # 繪製敵人
        for enemy in self.enemies:
            if enemy['type'] == 0: color = self.GREEN
            elif enemy['type'] == 1: color = self.YELLOW
            else: color = self.RED
            # 根據血量稍微變暗
            health_factor = 0.5 + 0.5 * (enemy['health'] / enemy['original_health']) # 0.5 to 1.0
            final_color = (int(color[0]*health_factor), int(color[1]*health_factor), int(color[2]*health_factor))
            pygame.draw.rect(screen, final_color, enemy['rect'])
            # 繪製敵人 "眼睛" (簡單示意)
            eye_y = enemy['rect'].centery - 5
            pygame.draw.circle(screen, self.WHITE, (enemy['rect'].centerx - 7, eye_y), 3)
            pygame.draw.circle(screen, self.WHITE, (enemy['rect'].centerx + 7, eye_y), 3)


        # 繪製UFO
        if self.ufo_active and self.ufo:
            pygame.draw.ellipse(screen, self.PURPLE, self.ufo['rect']) # UFO 用橢圓形
            # UFO上的小燈
            pygame.draw.circle(screen, self.YELLOW, (self.ufo['rect'].centerx, self.ufo['rect'].top + 5), 4)


        # 繪製道具
        for pu in self.power_ups:
            if pu['type'] == 'rapid_fire':
                pygame.draw.rect(screen, self.CYAN, pu['rect'])
                # 可以在道具上畫個標誌，例如 "F"
                if self.font_small:
                    text_surf = self.font_small.render("F", True, self.BLACK) # "F" 代表 Fast/Fire
                    screen.blit(text_surf, (pu['rect'].centerx - text_surf.get_width()//2, pu['rect'].centery - text_surf.get_height()//2))


        # 繪製分數、波數和生命
        score_text = self.font_medium.render(f"分數: {self.score}", True, self.WHITE)
        wave_text = self.font_medium.render(f"波數: {self.wave}", True, self.WHITE)
        lives_text = self.font_medium.render(f"生命: {self.lives}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(wave_text, (self.width // 2 - wave_text.get_width() // 2, 10)) # 波數顯示在中間
        screen.blit(lives_text, (self.width - lives_text.get_width() - 10, 10)) # 生命顯示在右邊

        # 顯示道具剩餘時間
        if self.active_power_up_type and self.font_small:
            power_up_display_text = f"{self.active_power_up_type.replace('_',' ').title()}: {self.power_up_timer // self.fps + 1}秒" # 顯示道具類型和剩餘秒數
            pu_text_surf = self.font_small.render(power_up_display_text, True, self.CYAN)
            screen.blit(pu_text_surf, (10, self.height - pu_text_surf.get_height() - 10)) # 顯示在左下角


        # 遊戲結束或暫停畫面
        if self.game_over:
            self.draw_game_over_or_pause(screen, "遊戲結束", self.RED, "按 開始鍵 重新開始")
        elif self.paused:
            self.draw_game_over_or_pause(screen, "已暫停", self.YELLOW, "按 開始鍵 繼續遊戲")

    def draw_game_over_or_pause(self, screen, title_text, title_color, subtitle_text):
        """統一繪製遊戲結束或暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA) # 建立一個帶Alpha通道的表面
        overlay.fill((0, 0, 0, 150)) # 半透明黑色遮罩
        screen.blit(overlay, (0, 0)) # 將遮罩繪製到主螢幕

        title_surf = self.font_large.render(title_text, True, title_color) # 渲染標題文字
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, self.height // 2 - 80)) # 標題置中偏上

        if title_text == "遊戲結束": # 如果是遊戲結束畫面，額外顯示最終分數
            final_score_surf = self.font_medium.render(f"最終分數: {self.score} (波數 {self.wave})", True, self.WHITE)
            screen.blit(final_score_surf, (self.width // 2 - final_score_surf.get_width() // 2, self.height // 2 )) # 分數置中
        
        subtitle_surf = self.font_medium.render(subtitle_text, True, self.WHITE) # 渲染副標題文字 (提示操作)
        screen.blit(subtitle_surf, (self.width // 2 - subtitle_surf.get_width() // 2, self.height // 2 + 60)) # 副標題置中偏下

    def cleanup(self):
        """清理遊戲資源 (目前未使用，但保留以備擴展)"""
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        pygame.init() # 初始化 Pygame
        if not pygame.font.get_init(): # 確保字型模組已初始化
            pygame.font.init()

        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height)) # 設定遊戲視窗
        pygame.display.set_caption("太空侵略者遊戲測試 (增強版)") # 設定視窗標題

        # 簡易 Buzzer 模擬 (用於測試，實際應傳入真實的 Buzzer 物件)
        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None, sound_name=None, loop=False, stop=False):
                # 模擬播放音效的行為，實際應用中會與硬體互動
                if sound_name:
                    print(f"Buzzer 模擬: 播放 '{sound_name}' (循環={loop}, 停止={stop})")
                elif frequency and duration :
                    print(f"Buzzer 模擬: 播放音調 freq={frequency}, dur={duration}")
                elif stop: # 模擬停止特定聲音
                     print(f"Buzzer 模擬: 停止 '{sound_name if sound_name else '目前音效'}'")


        mock_buzzer_instance = MockBuzzer() # 建立模擬蜂鳴器實例
        game = SpaceInvadersGame(screen_width, screen_height, buzzer=mock_buzzer_instance) # 建立遊戲實例

        # 按鍵映射 (將鍵盤按鍵對應到遊戲內動作)
        key_mapping = {
            pygame.K_LEFT: "left_pressed",    # 左方向鍵
            pygame.K_RIGHT: "right_pressed",   # 右方向鍵
            pygame.K_SPACE: "a_pressed",      # 空白鍵 (射擊)
            pygame.K_RETURN: "start_pressed"  # Enter/Return鍵 (開始/暫停)
        }
        
        # game_clock = pygame.time.Clock() # 使用遊戲實例的時鐘 (此行多餘，已在game實例中創建)
        running = True # 遊戲主迴圈運行標記
        while running:
            controller_input = {key: False for key in key_mapping.values()} # 初始化控制器輸入狀態
            
            # 事件處理迴圈
            for event in pygame.event.get():
                if event.type == pygame.QUIT: # 如果點擊關閉按鈕
                    running = False # 結束遊戲迴圈
            
            # 獲取當前按下的按鍵狀態
            keys = pygame.key.get_pressed()
            for key_code, input_name in key_mapping.items():
                if keys[key_code]: # 如果對應的按鍵被按下
                    controller_input[input_name] = True # 設定對應的輸入狀態為 True
            
            game_state = game.update(controller_input) # 更新遊戲邏輯並獲取遊戲狀態
            game.render(screen) # 渲染遊戲畫面
            pygame.display.flip() # 更新整個螢幕顯示
            
            game.clock.tick(game.fps) # 控制遊戲幀率 (使用遊戲實例的fps和時鐘)
            
        game.cleanup() # 清理遊戲資源 (目前為空)
        pygame.quit() # 退出 Pygame
    
    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        import traceback
        traceback.print_exc() # 印出完整的錯誤堆疊訊息，方便除錯
        pygame.quit() # 發生錯誤時也嘗試退出 Pygame

