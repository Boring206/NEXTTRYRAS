#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game3.py - Space Invaders Game Implementation (Enhanced)

import random
import pygame
import time
from pygame.locals import *

class SpaceInvadersGame:
    """Space Invaders Game Class (Enhanced)"""

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
        self.initial_barrier_block_health = 5

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
            self.font_large = pygame.font.SysFont("arial", 68)
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
        self.enemy_direction = 1
        self.enemy_speed_x = self.enemy_speed_x_initial

        self.last_shot_time = 0
        self.shot_delay = self.shot_delay_normal # 當前射擊間隔

        self.enemy_shot_timer = 0
        self.enemy_shot_interval_initial = 70 # 初始敵人射擊間隔 (幀)
        self.enemy_shot_interval = self.enemy_shot_interval_initial

        self.wave = 1
        self.score = 0
        self.lives = 3

        self.game_over = False
        self.paused = False

        self.create_enemies()
        self.create_barriers()

        # UFO 重置
        self.ufo = None
        self.ufo_active = False
        self.ufo_spawn_timer = 0
        # 稍微提早UFO出現時間
        self.ufo_spawn_interval = random.randint(int(8 * self.fps), int(15 * self.fps))
        self.ufo_y_pos = 50 # UFO出現的Y軸位置

        # 道具重置
        self.power_ups = []
        self.active_power_up_type = None
        self.power_up_timer = 0
        self.power_up_duration = 7 * self.fps # 道具持續7秒

    def create_enemies(self):
        """建立敵人陣列"""
        self.enemies.clear()
        rows = 5
        cols = 10 # 增加敵人數量
        
        # 根據波數調整敵人屬性
        extra_health_per_wave = self.wave // 3 # 每3波增加一點血量
        
        for row in range(rows):
            for col in range(cols):
                x = col * (self.enemy_width + 10) + 30 # 調整起始X和間距
                y = row * (self.enemy_height + 10) + 80 # 調整起始Y，使其更靠上
                
                enemy_type = min(row, 2) 
                
                self.enemies.append({
                    'rect': pygame.Rect(x, y, self.enemy_width, self.enemy_height),
                    'type': enemy_type,
                    'health': enemy_type + 1 + extra_health_per_wave,
                    'original_health': enemy_type + 1 + extra_health_per_wave
                })

    def create_barriers(self):
        """建立掩體"""
        self.barrier_blocks = []
        num_barriers = 4
        barrier_width_units = 6 # 每個掩體的寬度單位數
        barrier_height_units = 4 # 每個掩體的高度單位數
        
        # 計算所有掩體加上間隙的總寬度，以使其居中
        total_barriers_width = num_barriers * barrier_width_units * self.barrier_block_size
        total_gaps_width = (num_barriers - 1) * (self.barrier_block_size * 3) # 每個間隙約3個方塊寬
        combined_width = total_barriers_width + total_gaps_width
        
        start_x_offset = (self.width - combined_width) // 2

        barrier_shape = [ # 1 代表實心方塊
            [0, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 1, 1], # 中間有個更大的洞
            [1, 0, 0, 0, 0, 1]
        ]

        for i in range(num_barriers):
            barrier_base_x = start_x_offset + i * (barrier_width_units * self.barrier_block_size + (self.barrier_block_size*3))
            barrier_base_y = self.player_y - self.player_height - barrier_height_units * self.barrier_block_size - 30

            for row_idx, row_data in enumerate(barrier_shape):
                for col_idx, cell in enumerate(row_data):
                    if cell == 1:
                        block_x = barrier_base_x + col_idx * self.barrier_block_size
                        block_y = barrier_base_y + row_idx * self.barrier_block_size
                        self.barrier_blocks.append({
                            'rect': pygame.Rect(block_x, block_y, self.barrier_block_size, self.barrier_block_size),
                            'health': self.initial_barrier_block_health,
                            'max_health': self.initial_barrier_block_health
                        })

    def move_player(self, direction_key):
        """移動玩家飛船"""
        if direction_key == "left":
            self.player_x = max(0, self.player_x - self.player_speed)
        elif direction_key == "right":
            self.player_x = min(self.width - self.player_width, self.player_x + self.player_speed)

    def shoot(self):
        """玩家射擊"""
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_delay:
            bullet_x = self.player_x + (self.player_width // 2) - (self.bullet_width // 2)
            bullet_y = self.player_y
            self.bullets.append(pygame.Rect(bullet_x, bullet_y, self.bullet_width, self.bullet_height))
            self.last_shot_time = current_time
            if self.buzzer:
                self.buzzer.play_tone(frequency=1000, duration=0.05) # 玩家射擊音效

    def enemy_shoot(self):
        """敵人射擊"""
        self.enemy_shot_timer += 1
        if self.enemy_shot_timer >= self.enemy_shot_interval:
            self.enemy_shot_timer = 0
            if self.enemies:
                # 嘗試讓下方的敵人優先射擊
                shooters_in_column = {}
                for enemy in self.enemies:
                    col_key = enemy['rect'].x // (self.enemy_width + 10) # 簡單的列索引
                    if col_key not in shooters_in_column or enemy['rect'].y > shooters_in_column[col_key]['rect'].y:
                        shooters_in_column[col_key] = enemy
                
                if shooters_in_column:
                    shooter = random.choice(list(shooters_in_column.values()))
                    bullet_x = shooter['rect'].centerx - (self.enemy_bullet_width // 2)
                    bullet_y = shooter['rect'].bottom
                    self.enemy_bullets.append(pygame.Rect(bullet_x, bullet_y, self.enemy_bullet_width, self.enemy_bullet_height))
                    # 可在此添加敵人射擊音效
                    # if self.buzzer: self.buzzer.play_tone(frequency=300, duration=0.08)


    def update_bullets(self):
        """更新所有子彈位置並移除螢幕外的子彈"""
        for bullet in self.bullets[:]:
            bullet.y -= self.bullet_speed
            if bullet.bottom < 0:
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.y += self.enemy_bullet_speed
            if bullet.top > self.height:
                self.enemy_bullets.remove(bullet)

    def update_enemies(self):
        """更新敵人位置，處理邊界碰撞和觸底"""
        if not self.enemies:
            return

        move_down = False
        current_enemy_speed = self.enemy_speed_x * self.enemy_direction

        for enemy in self.enemies:
            if (enemy['rect'].right + current_enemy_speed > self.width and self.enemy_direction > 0) or \
               (enemy['rect'].left + current_enemy_speed < 0 and self.enemy_direction < 0):
                move_down = True
                break
        
        if move_down:
            self.enemy_direction *= -1
            for enemy in self.enemies:
                enemy['rect'].y += self.enemy_speed_y
        else:
            for enemy in self.enemies:
                enemy['rect'].x += current_enemy_speed

        for enemy in self.enemies:
            if enemy['rect'].bottom >= self.player_y - self.player_height //2 : # 稍微調整觸底判斷
                self.game_over = True
                if self.buzzer: self.buzzer.play_tone("game_over_melody_invaders") # 假設有此音效
                return # 遊戲結束，無需進一步處理

    def update_ufo(self):
        """更新UFO的出現和移動"""
        if not self.ufo_active:
            self.ufo_spawn_timer += 1
            if self.ufo_spawn_timer >= self.ufo_spawn_interval:
                self.ufo_active = True
                self.ufo_spawn_timer = 0
                self.ufo_spawn_interval = random.randint(int(10 * self.fps), int(25 * self.fps)) # 重設下次出現時間
                
                direction = random.choice([-1, 1])
                start_x = -self.ufo_width if direction == 1 else self.width
                self.ufo = {
                    'rect': pygame.Rect(start_x, self.ufo_y_pos, self.ufo_width, self.ufo_height),
                    'direction': direction,
                    'score': random.choice([50, 100, 150, 200, 300])
                }
                if self.buzzer: self.buzzer.play_tone("ufo_flying_sound", loop=True) # 假設可以循環播放
        else:
            if self.ufo:
                self.ufo['rect'].x += self.ufo_speed * self.ufo['direction']
                if (self.ufo['direction'] == 1 and self.ufo['rect'].left > self.width) or \
                   (self.ufo['direction'] == -1 and self.ufo['rect'].right < 0):
                    self.ufo_active = False
                    self.ufo = None
                    if self.buzzer: self.buzzer.play_tone("ufo_flying_sound", stop=True) # 假設可以停止

    def update_power_ups(self):
        """更新道具位置和效果計時"""
        for pu in self.power_ups[:]:
            pu['rect'].y += 2 # 道具下降速度
            if pu['rect'].top > self.height:
                self.power_ups.remove(pu)

        if self.active_power_up_type:
            self.power_up_timer -= 1
            if self.power_up_timer <= 0:
                if self.active_power_up_type == "rapid_fire":
                    self.shot_delay = self.shot_delay_normal
                self.active_power_up_type = None
                if self.buzzer: self.buzzer.play_tone("power_down_sound")


    def check_collisions(self):
        """檢查各種碰撞"""
        # 玩家子彈 vs 敵人
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.colliderect(enemy['rect']):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    enemy['health'] -= 1
                    if enemy['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.score += (enemy['type'] + 1) * 10 * self.wave # 分數也跟波數有關
                        if self.buzzer: self.buzzer.play_tone(frequency=600 + enemy['type']*100, duration=0.06) # 敵人被擊中音效
                    break 

            # 玩家子彈 vs UFO
            if self.ufo_active and self.ufo and bullet.colliderect(self.ufo['rect']):
                if bullet in self.bullets: self.bullets.remove(bullet)
                self.score += self.ufo['score']
                if self.buzzer:
                    self.buzzer.play_tone("ufo_flying_sound", stop=True)
                    self.buzzer.play_tone("ufo_hit_sound")
                
                # UFO被擊落，掉落道具
                pu_x = self.ufo['rect'].centerx - self.power_up_width // 2
                pu_y = self.ufo['rect'].centery
                self.power_ups.append({
                    'rect': pygame.Rect(pu_x, pu_y, self.power_up_width, self.power_up_height),
                    'type': 'rapid_fire' 
                })

                self.ufo_active = False
                self.ufo = None
                break # 子彈已消耗

        # 敵人子彈 vs 玩家
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
        for bullet in self.enemy_bullets[:]:
            if bullet.colliderect(player_rect):
                self.enemy_bullets.remove(bullet)
                self.lives -= 1
                if self.buzzer: self.buzzer.play_tone(frequency=200, duration=0.2) # 玩家被擊中
                if self.lives <= 0:
                    self.game_over = True
                    if self.buzzer: self.buzzer.play_tone("game_over_melody_invaders")
                return # 避免一幀內多次受傷判定

        # 子彈 vs 掩體
        for bullet_list in [self.bullets, self.enemy_bullets]:
            for bullet in bullet_list[:]:
                for block in self.barrier_blocks[:]:
                    if bullet.colliderect(block['rect']):
                        if bullet in bullet_list: bullet_list.remove(bullet) # 子彈消耗
                        block['health'] -= 1
                        if block['health'] <= 0:
                            self.barrier_blocks.remove(block)
                        # 可添加掩體被擊中音效
                        # if self.buzzer: self.buzzer.play_tone(frequency=150, duration=0.03)
                        break # 一顆子彈只打一個方塊

        # 玩家 vs 道具
        for pu in self.power_ups[:]:
            if player_rect.colliderect(pu['rect']):
                self.power_ups.remove(pu)
                if pu['type'] == 'rapid_fire':
                    self.active_power_up_type = 'rapid_fire'
                    self.shot_delay = self.shot_delay_rapid_fire
                    self.power_up_timer = self.power_up_duration
                    if self.buzzer: self.buzzer.play_tone("power_up_collect_sound")


    def check_wave_complete(self):
        """檢查當前波是否完成"""
        if not self.enemies and not self.game_over: # 確保遊戲未結束
            self.wave += 1
            self.score += self.wave * 50 # 過關獎勵
            self.create_enemies()
            # self.create_barriers() # 可選擇是否每波都重置掩體
            
            self.enemy_speed_x = min(self.enemy_speed_x_initial + (self.wave -1) * 0.2, 5) # 敵人X速度隨波數增加，但有上限
            self.enemy_shot_interval = max(20, self.enemy_shot_interval_initial - self.wave * 3) # 敵人射擊間隔減少
            
            # 清空現有子彈和道具，避免影響下一波
            self.bullets.clear()
            self.enemy_bullets.clear()
            self.power_ups.clear()
            if self.active_power_up_type == "rapid_fire": # 如果有射速提升，結束它
                 self.shot_delay = self.shot_delay_normal
                 self.active_power_up_type = None
                 self.power_up_timer = 0

            if self.buzzer: self.buzzer.play_tone("wave_complete_sound") # 假設有過關音效

    def update(self, controller_input=None):
        """更新遊戲狀態"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                # 添加延遲避免立即觸發
                if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.paused = False
                    self.last_start_press_time = time.time()
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}

        # 輸入處理
        if controller_input:
            if controller_input.get("left_pressed"):
                self.move_player("left")
            if controller_input.get("right_pressed"):
                self.move_player("right")
            if controller_input.get("a_pressed"):
                self.shoot()
            if controller_input.get("start_pressed"):
                 if not hasattr(self, 'last_start_press_time') or time.time() - self.last_start_press_time > 0.5:
                    self.paused = not self.paused
                    self.last_start_press_time = time.time()
                    if self.buzzer: self.buzzer.play_tone(frequency=400, duration=0.1) # 暫停音效
                    return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}
        
        # 遊戲邏輯更新
        self.update_bullets()
        self.update_enemies()
        self.enemy_shoot() # 敵人射擊邏輯
        self.update_ufo()
        self.update_power_ups()
        self.check_collisions()
        self.check_wave_complete() # 必須在 collision 之後，確保敵人列表已更新

        return {"game_over": self.game_over, "score": self.score, "paused": self.paused, "wave": self.wave}

    def render(self, screen):
        """渲染遊戲畫面"""
        screen.fill(self.BLACK)

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
                    text_surf = self.font_small.render("F", True, self.BLACK)
                    screen.blit(text_surf, (pu['rect'].centerx - text_surf.get_width()//2, pu['rect'].centery - text_surf.get_height()//2))


        # 繪製分數、波數和生命
        score_text = self.font_medium.render(f"Score: {self.score}", True, self.WHITE)
        wave_text = self.font_medium.render(f"Wave: {self.wave}", True, self.WHITE)
        lives_text = self.font_medium.render(f"Lives: {self.lives}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(wave_text, (self.width // 2 - wave_text.get_width() // 2, 10))
        screen.blit(lives_text, (self.width - lives_text.get_width() - 10, 10))

        # 顯示道具剩餘時間
        if self.active_power_up_type and self.font_small:
            power_up_display_text = f"{self.active_power_up_type.replace('_',' ').title()}: {self.power_up_timer // self.fps + 1}s"
            pu_text_surf = self.font_small.render(power_up_display_text, True, self.CYAN)
            screen.blit(pu_text_surf, (10, self.height - pu_text_surf.get_height() - 10))


        # 遊戲結束或暫停畫面
        if self.game_over:
            self.draw_game_over_or_pause(screen, "Game Over", self.RED, "Press Start to Restart")
        elif self.paused:
            self.draw_game_over_or_pause(screen, "Paused", self.YELLOW, "Press Start to Continue")

    def draw_game_over_or_pause(self, screen, title_text, title_color, subtitle_text):
        """統一繪製遊戲結束或暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) # 半透明黑色遮罩
        screen.blit(overlay, (0, 0))

        title_surf = self.font_large.render(title_text, True, title_color)
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, self.height // 2 - 80))

        if title_text == "Game Over":
            final_score_surf = self.font_medium.render(f"Final Score: {self.score} (Wave {self.wave})", True, self.WHITE)
            screen.blit(final_score_surf, (self.width // 2 - final_score_surf.get_width() // 2, self.height // 2 ))
        
        subtitle_surf = self.font_medium.render(subtitle_text, True, self.WHITE)
        screen.blit(subtitle_surf, (self.width // 2 - subtitle_surf.get_width() // 2, self.height // 2 + 60))

    def cleanup(self):
        """清理遊戲資源"""
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        pygame.init()
        if not pygame.font.get_init(): # 確保字型模組已初始化
            pygame.font.init()

        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Space Invaders Game Test (Enhanced)")

        # 簡易 Buzzer 模擬 (用於測試，實際應傳入真實的 Buzzer 物件)
        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None, sound_name=None, loop=False, stop=False):
                if sound_name:
                    print(f"Buzzer: Playing '{sound_name}' (loop={loop}, stop={stop})")
                elif frequency and duration :
                    print(f"Buzzer: Playing tone freq={frequency}, dur={duration}")
                elif stop: # 模擬停止特定聲音
                     print(f"Buzzer: Stopping '{sound_name if sound_name else 'current sound'}'")


        mock_buzzer_instance = MockBuzzer()
        game = SpaceInvadersGame(screen_width, screen_height, buzzer=mock_buzzer_instance)

        key_mapping = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_SPACE: "a_pressed", # 將 'a' 鍵改為空白鍵射擊
            pygame.K_RETURN: "start_pressed"
        }
        
        game_clock = pygame.time.Clock() # 使用遊戲實例的時鐘
        running = True
        while running:
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            keys = pygame.key.get_pressed()
            for key_code, input_name in key_mapping.items():
                if keys[key_code]:
                    controller_input[input_name] = True
            
            game_state = game.update(controller_input) # 更新遊戲並獲取狀態
            game.render(screen)
            pygame.display.flip()
            
            game.clock.tick(game.fps) # 使用遊戲實例的fps和時鐘
            
        game.cleanup()
        pygame.quit()
    
    except Exception as e:
        print(f"Game execution error: {e}")
        import traceback
        traceback.print_exc() # 印出完整的錯誤堆疊
        pygame.quit()