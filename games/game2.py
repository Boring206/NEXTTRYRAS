#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game2.py - 打磚塊遊戲實現

import random
import pygame
import time
import math
from pygame.locals import *

class BrickBreakerGame:
    """打磚塊遊戲類"""
    
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
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 球和板子的初始參數
        self.paddle_width = 100
        self.paddle_height = 15
        self.ball_radius = 10
        self.ball_speed = 5
        
        # 磚塊參數
        self.brick_width = 75
        self.brick_height = 20
        self.brick_rows = 5
        self.brick_cols = 10
        self.brick_gap = 2
        
        # 音效計時
        self.last_paddle_hit_time = 0
        self.last_brick_hit_time = 0
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 板子初始位置
        self.paddle_x = (self.width - self.paddle_width) // 2
        self.paddle_y = self.height - 40
        
        # 球的初始位置和速度
        self.ball_x = self.width // 2
        self.ball_y = self.height - 60
        self.ball_dx = self.ball_speed * (1 if random.random() > 0.5 else -1)
        self.ball_dy = -self.ball_speed
        
        # 遊戲狀態
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.paused = False
        self.ball_launched = False  # 是否已發射球
        
        # 創建磚塊
        self.create_bricks()
    
    def handle_ball_paddle_collision(self):
        """處理球與擋板碰撞，增強音效"""
        current_time = time.time()
        
        # 計算碰撞位置影響球的角度
        hit_pos = (self.ball_x - self.paddle_x) / self.paddle_width
        angle_influence = (hit_pos - 0.5) * 0.5  # -0.25 到 0.25
        
        self.ball_dy = -abs(self.ball_dy)  # 確保向上
        self.ball_dx += angle_influence * self.ball_speed
        
        # 音效回饋
        if self.buzzer and current_time - self.last_paddle_hit_time > 0.1:
            # 根據擊球位置調整音調
            base_freq = 400
            freq_variation = int(hit_pos * 200)  # -100 to 100
            self.buzzer.play_tone(frequency=base_freq + freq_variation, duration=0.1)
            self.last_paddle_hit_time = current_time
    
    def handle_ball_brick_collision(self, brick_type):
        """處理球與磚塊碰撞，增強音效和分數"""
        current_time = time.time()
        
        # 根據磚塊類型給分
        score_values = {
            'red': 50,
            'orange': 40,
            'yellow': 30,
            'green': 20,
            'blue': 10
        }
        
        self.score += score_values.get(brick_type, 10)
        
        # 音效回饋
        if self.buzzer and current_time - self.last_brick_hit_time > 0.05:
            freq_map = {
                'red': 1000,
                'orange': 900,
                'yellow': 800,
                'green': 700,
                'blue': 600
            }
            frequency = freq_map.get(brick_type, 500)
            self.buzzer.play_tone(frequency=frequency, duration=0.1)
            self.last_brick_hit_time = current_time

    def create_bricks(self):
        """創建磚塊，增加顏色分層"""
        self.bricks = []
        colors = [self.RED, self.ORANGE, self.YELLOW, self.GREEN, self.BLUE]
        color_names = ['red', 'orange', 'yellow', 'green', 'blue']
        
        for row in range(self.brick_rows):
            for col in range(self.brick_cols):
                brick_x = col * (self.brick_width + self.brick_gap) + 50
                brick_y = row * (self.brick_height + self.brick_gap) + 50
                
                brick = {
                    'x': brick_x,
                    'y': brick_y,
                    'width': self.brick_width,
                    'height': self.brick_height,
                    'rect': pygame.Rect(brick_x, brick_y, self.brick_width, self.brick_height),
                    'color': colors[row % len(colors)],
                    'type': color_names[row % len(color_names)],
                    'active': True,
                    'hits': 1  # 磚塊需要被擊中的次數
                }
                self.bricks.append(brick)
    
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
        
        # 處理輸入
        if controller_input:
            # 移動板子
            paddle_speed = 10
            if controller_input.get("left_pressed"):
                self.paddle_x = max(0, self.paddle_x - paddle_speed)
            if controller_input.get("right_pressed"):
                self.paddle_x = min(self.width - self.paddle_width, self.paddle_x + paddle_speed)
            
            # 發射球
            if not self.ball_launched and controller_input.get("a_pressed"):
                self.ball_launched = True
                if self.buzzer:
                    self.buzzer.play_tone("select")
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 如果球還沒發射，讓它跟隨板子
        if not self.ball_launched:
            self.ball_x = self.paddle_x + self.paddle_width // 2
            self.ball_y = self.paddle_y - self.ball_radius
            return {"game_over": self.game_over, "score": self.score}
        
        # 移動球
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy
        
        # 檢查是否碰到牆壁
        if self.ball_x <= self.ball_radius or self.ball_x >= self.width - self.ball_radius:
            self.ball_dx = -self.ball_dx
            if self.buzzer:
                self.buzzer.play_tone("navigate")
        
        if self.ball_y <= self.ball_radius:
            self.ball_dy = -self.ball_dy
            if self.buzzer:
                self.buzzer.play_tone("navigate")
        
        # 檢查是否球落下
        if self.ball_y >= self.height:
            self.lives -= 1
            if self.buzzer:
                self.buzzer.play_tone("error")
            
            if self.lives <= 0:
                self.game_over = True
                if self.buzzer:
                    self.buzzer.play_game_over_melody()
            else:
                # 重置球的位置
                self.ball_launched = False
                self.ball_x = self.paddle_x + self.paddle_width // 2
                self.ball_y = self.paddle_y - self.ball_radius
                self.ball_dx = self.ball_speed * (1 if random.random() > 0.5 else -1)
                self.ball_dy = -self.ball_speed
        
        # 檢查球是否碰到板子
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        ball_rect = pygame.Rect(self.ball_x - self.ball_radius, self.ball_y - self.ball_radius, 
                              self.ball_radius * 2, self.ball_radius * 2)
        
        if ball_rect.colliderect(paddle_rect) and self.ball_dy > 0:
            # 根據撞擊點調整反彈角度
            relative_intersect_x = (self.paddle_x + self.paddle_width / 2) - self.ball_x
            normalized_intersect_x = relative_intersect_x / (self.paddle_width / 2)
            bounce_angle = normalized_intersect_x * (math.pi / 3)  # 最大角度為 60 度
            
            self.ball_dx = -self.ball_speed * math.sin(bounce_angle)
            self.ball_dy = -self.ball_speed * math.cos(bounce_angle)
            
            # 使用增強碰撞處理
            self.handle_ball_paddle_collision()
        
        # 檢查球是否碰到磚塊
        for brick in self.bricks[:]:
            if ball_rect.colliderect(brick['rect']):
                # 減少磚塊生命值
                brick['hits'] -= 1
                
                if brick['hits'] <= 0:
                    # 移除磚塊
                    self.bricks.remove(brick)
                    # 使用增強碰撞處理
                    self.handle_ball_brick_collision(brick['type'])
                else:
                    # 改變磚塊顏色
                    brick['color'] = (
                        min(255, brick['color'][0] + 30),
                        min(255, brick['color'][1] + 30),
                        min(255, brick['color'][2] + 30)
                    )
                    if self.buzzer:
                        self.buzzer.play_tone("navigate")
                
                # 根據碰撞位置反彈球
                # 簡化的碰撞檢測：只檢查上下碰撞還是左右碰撞
                brick_rect = brick['rect']
                
                # 檢查上下碰撞
                if abs(self.ball_y - brick_rect.top) < 5 or abs(self.ball_y - brick_rect.bottom) < 5:
                    self.ball_dy = -self.ball_dy
                else:
                    self.ball_dx = -self.ball_dx
                
                break  # 一次只處理一個碰撞
        
        # 檢查是否通關
        if len(self.bricks) == 0:
            # 增加難度並重設
            self.ball_speed += 1
            self.create_bricks()
            self.ball_launched = False
            self.score += 50  # 通關獎勵
            
            if self.buzzer:
                self.buzzer.play_win_melody()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製板子
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        pygame.draw.rect(screen, self.BLUE, paddle_rect)
        
        # 繪製球
        pygame.draw.circle(screen, self.WHITE, (int(self.ball_x), int(self.ball_y)), self.ball_radius)
        
        # 繪製磚塊
        for brick in self.bricks:
            pygame.draw.rect(screen, brick['color'], brick['rect'])
        
        # 繪製分數和生命值
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        lives_text = font.render(f"生命: {self.lives}", True, self.WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (self.width - 120, 10))
        
        # 繪製遊戲指示
        if not self.ball_launched:
            hint_text = font.render("按 A 鈕發射球", True, self.YELLOW)
            screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 20))
        
        # 遊戲結束畫面
        if self.game_over:
            game_over_text = font.render("遊戲結束！按 Start 重新開始", True, self.WHITE)
            text_rect = game_over_text.get_rect(center=(self.width // 2, self.height // 2))
            screen.blit(game_over_text, text_rect)
            
            final_score_text = font.render(f"最終分數: {self.score}", True, self.WHITE)
            score_rect = final_score_text.get_rect(center=(self.width // 2, self.height // 2 + 40))
            screen.blit(final_score_text, score_rect)
        
        # 暫停畫面
        elif self.paused:
            pause_text = font.render("遊戲暫停", True, self.WHITE)
            text_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))
            screen.blit(pause_text, text_rect)
    
    def cleanup(self):
        """清理遊戲資源"""
        # 目前無需特殊清理，但保留此方法以便未來擴充
        pass

# 測試函式 - 當直接執行此腳本時運行
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 設置視窗
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("打磚塊遊戲測試")
        
        # 建立遊戲實例
        game = BrickBreakerGame(screen_width, screen_height)
        
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