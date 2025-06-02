#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game3.py - 太空侵略者遊戲實現

import random
import pygame
import time
from pygame.locals import *

class SpaceInvadersGame:
    """太空侵略者遊戲類"""
    
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
        
        # 遊戲元素大小
        self.player_width = 50
        self.player_height = 30
        self.enemy_width = 40
        self.enemy_height = 30
        self.bullet_width = 5
        self.bullet_height = 15
        self.enemy_bullet_width = 3
        self.enemy_bullet_height = 12
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player_speed = 5
        self.bullet_speed = 7
        self.enemy_speed_x = 2
        self.enemy_speed_y = 20
        self.enemy_bullet_speed = 4
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 玩家飛船初始位置
        self.player_x = (self.width - self.player_width) // 2
        self.player_y = self.height - 50
        
        # 子彈列表
        self.bullets = []
        self.enemy_bullets = []
        
        # 敵人飛船列表
        self.enemies = []
        self.create_enemies()
        
        # 方向，控制敵人移動
        self.enemy_direction = 1
        
        # 射擊計時 (限制射擊頻率)
        self.last_shot_time = 0
        self.shot_delay = 0.5  # 每次射擊之間的秒數
        
        # 敵人射擊計時
        self.enemy_shot_timer = 0
        self.enemy_shot_interval = 60  # 幀數
        
        # 當前波次和分數
        self.wave = 1
        self.score = 0
        self.lives = 3
        
        # 遊戲狀態
        self.game_over = False
        self.paused = False
    
    def create_enemies(self):
        """創建敵人飛船陣列"""
        rows = 5
        cols = 8
        
        for row in range(rows):
            for col in range(cols):
                x = col * (self.enemy_width + 10) + 50
                y = row * (self.enemy_height + 10) + 50
                
                # 敵人飛船的類型/顏色根據所在行數決定
                enemy_type = min(row, 2)  # 0=簡單, 1=中等, 2=困難
                
                self.enemies.append({
                    'x': x,
                    'y': y,
                    'type': enemy_type,
                    'health': enemy_type + 1  # 生命值: 簡單=1, 中等=2, 困難=3
                })
    
    def move_player(self, direction):
        """移動玩家飛船"""
        if direction == "left":
            self.player_x = max(0, self.player_x - self.player_speed)
        elif direction == "right":
            self.player_x = min(self.width - self.player_width, self.player_x + self.player_speed)
    
    def shoot(self):
        """玩家射擊"""
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_delay:
            # 在飛船中央發射子彈
            bullet_x = self.player_x + (self.player_width // 2) - (self.bullet_width // 2)
            bullet_y = self.player_y
            
            self.bullets.append({
                'x': bullet_x,
                'y': bullet_y
            })
            
            self.last_shot_time = current_time
            
            # 播放射擊音效
            if self.buzzer:
                self.buzzer.play_tone("select")
    
    def enemy_shoot(self):
        """敵人射擊"""
        self.enemy_shot_timer += 1
        
        if self.enemy_shot_timer >= self.enemy_shot_interval:
            self.enemy_shot_timer = 0
            
            # 隨機選擇一個敵人進行射擊
            if self.enemies:
                shooter = random.choice(self.enemies)
                
                bullet_x = shooter['x'] + (self.enemy_width // 2) - (self.enemy_bullet_width // 2)
                bullet_y = shooter['y'] + self.enemy_height
                
                self.enemy_bullets.append({
                    'x': bullet_x,
                    'y': bullet_y
                })
    
    def move_bullets(self):
        """移動所有子彈"""
        # 移動玩家子彈 (向上)
        for bullet in self.bullets[:]:
            bullet['y'] -= self.bullet_speed
            
            # 移除超出螢幕的子彈
            if bullet['y'] < 0:
                self.bullets.remove(bullet)
        
        # 移動敵人子彈 (向下)
        for bullet in self.enemy_bullets[:]:
            bullet['y'] += self.enemy_bullet_speed
            
            # 移除超出螢幕的子彈
            if bullet['y'] > self.height:
                self.enemy_bullets.remove(bullet)
    
    def move_enemies(self):
        """移動敵人"""
        change_direction = False
        
        # 檢查是否有敵人到達邊界
        for enemy in self.enemies:
            if (enemy['x'] + self.enemy_width >= self.width and self.enemy_direction > 0) or \
               (enemy['x'] <= 0 and self.enemy_direction < 0):
                change_direction = True
                break
        
        # 改變方向並向下移動
        if change_direction:
            self.enemy_direction = -self.enemy_direction
            for enemy in self.enemies:
                enemy['y'] += self.enemy_speed_y
        else:
            # 正常左右移動
            for enemy in self.enemies:
                enemy['x'] += self.enemy_speed_x * self.enemy_direction
        
        # 檢查敵人是否到達底部 (遊戲結束)
        for enemy in self.enemies:
            if enemy['y'] + self.enemy_height >= self.player_y:
                self.game_over = True
                if self.buzzer:
                    self.buzzer.play_game_over_melody()
                break
    
    def check_collisions(self):
        """檢查碰撞"""
        # 檢查玩家子彈與敵人碰撞
        for bullet in self.bullets[:]:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.bullet_width, self.bullet_height)
            
            for enemy in self.enemies[:]:
                enemy_rect = pygame.Rect(enemy['x'], enemy['y'], self.enemy_width, self.enemy_height)
                
                if bullet_rect.colliderect(enemy_rect):
                    # 敵人被擊中
                    enemy['health'] -= 1
                    
                    # 移除已擊中的子彈
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    # 敵人被擊敗
                    if enemy['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.score += (enemy['type'] + 1) * 10
                        
                        if self.buzzer:
                            self.buzzer.play_tone("score")
                    
                    break
        
        # 檢查敵人子彈與玩家碰撞
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
        
        for bullet in self.enemy_bullets[:]:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.enemy_bullet_width, self.enemy_bullet_height)
            
            if bullet_rect.colliderect(player_rect):
                # 玩家被擊中
                self.lives -= 1
                self.enemy_bullets.remove(bullet)
                
                if self.buzzer:
                    self.buzzer.play_tone("error")
                
                if self.lives <= 0:
                    self.game_over = True
                    if self.buzzer:
                        self.buzzer.play_game_over_melody()
    
    def check_wave_complete(self):
        """檢查當前波次是否完成"""
        if not self.enemies:
            self.wave += 1
            self.create_enemies()
            
            # 提高敵人速度
            self.enemy_speed_x += 0.5
            
            # 減少敵人射擊間隔
            self.enemy_shot_interval = max(20, self.enemy_shot_interval - 5)
            
            if self.buzzer:
                self.buzzer.play_win_melody()
    
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
        
        current_time = time.time()
        
        # 處理輸入
        if controller_input:
            # 移動控制（增強響應性）
            if controller_input.get("left_pressed"):
                self.move_player("left")
                if self.buzzer and current_time - getattr(self, 'last_move_sound', 0) > 0.1:
                    self.buzzer.play_tone(frequency=300, duration=0.05)
                    self.last_move_sound = current_time
                    
            if controller_input.get("right_pressed"):
                self.move_player("right")
                if self.buzzer and current_time - getattr(self, 'last_move_sound', 0) > 0.1:
                    self.buzzer.play_tone(frequency=300, duration=0.05)
                    self.last_move_sound = current_time
            
            # 射擊控制（防止過於頻繁）
            if controller_input.get("a_pressed"):
                if current_time - self.last_shot_time >= self.shot_cooldown:
                    self.shoot()
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=800, duration=0.1)
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 更新遊戲邏輯
        self.update_bullets()
        self.update_aliens()
        self.update_alien_bullets()
        self.check_collisions()
        
        # 檢查勝利條件
        if not self.aliens:
            self.spawn_new_wave()
            if self.buzzer:
                self.buzzer.play_victory_fanfare()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製星星背景
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            pygame.draw.circle(screen, self.WHITE, (x, y), 1)
        
        # 繪製玩家飛船
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
        pygame.draw.rect(screen, self.GREEN, player_rect)
        
        # 繪製三角形飛船形狀
        pygame.draw.polygon(screen, self.GREEN, [
            (self.player_x, self.player_y + self.player_height),
            (self.player_x + self.player_width // 2, self.player_y),
            (self.player_x + self.player_width, self.player_y + self.player_height)
        ])
        
        # 繪製玩家子彈
        for bullet in self.bullets:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.bullet_width, self.bullet_height)
            pygame.draw.rect(screen, self.BLUE, bullet_rect)
        
        # 繪製敵人子彈
        for bullet in self.enemy_bullets:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.enemy_bullet_width, self.enemy_bullet_height)
            pygame.draw.rect(screen, self.RED, bullet_rect)
        
        # 繪製敵人
        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy['x'], enemy['y'], self.enemy_width, self.enemy_height)
            
            # 根據敵人類型設定顏色
            if enemy['type'] == 0:
                color = self.GREEN
            elif enemy['type'] == 1:
                color = self.YELLOW
            else:
                color = self.RED
            
            pygame.draw.rect(screen, color, enemy_rect)
        
        # 繪製分數、波次和生命值
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        wave_text = font.render(f"波次: {self.wave}", True, self.WHITE)
        lives_text = font.render(f"生命: {self.lives}", True, self.WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(wave_text, (10, 50))
        screen.blit(lives_text, (self.width - 150, 10))
        
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
        
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 50))
    
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
        pygame.display.set_caption("太空侵略者遊戲測試")
        
        # 建立遊戲實例
        game = SpaceInvadersGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # 遊戲主迴圈
        running = True
        while running:
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
