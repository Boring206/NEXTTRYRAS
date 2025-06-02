#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game1.py - 增強版貪吃蛇遊戲實現

import random
import pygame
import time
import math
from pygame.locals import *

class EnhancedSnakeGame:
    """增強版貪吃蛇遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width
        self.height = height
        self.buzzer = buzzer
        
        # 遊戲元素大小
        self.block_size = 20
        self.grid_width = self.width // self.block_size
        self.grid_height = self.height // self.block_size
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (255, 0, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        
        # 特殊食物顏色
        self.GOLDEN_FOOD = (255, 215, 0)
        self.SPEED_FOOD = (255, 100, 100)
        self.MULTI_FOOD = (100, 255, 100)
        self.BONUS_FOOD = (255, 20, 147)
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.base_speed = 8
        self.speed_boost = 15
        self.current_speed = self.base_speed
        
        # 道具系統
        self.powerups = {
            'invincible': {'active': False, 'timer': 0, 'duration': 5.0},
            'speed_boost': {'active': False, 'timer': 0, 'duration': 3.0},
            'score_multiplier': {'active': False, 'timer': 0, 'duration': 10.0},
            'wall_phase': {'active': False, 'timer': 0, 'duration': 8.0}
        }
        
        # 粒子效果系統
        self.particles = []
        
        # 音效增強
        self.combo_count = 0
        self.last_eat_time = 0
        self.combo_window = 2.0  # 連擊窗口時間
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 蛇的初始位置
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0)
        
        # 食物系統
        self.foods = []
        self.generate_food()
        
        # 特殊食物計時器
        self.special_food_timer = 0
        self.special_food_interval = 10.0  # 10秒生成一個特殊食物
        
        # 遊戲狀態
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.boosting = False
        
        # 增強功能
        self.score_multiplier = 1
        self.total_eaten = 0
        self.combo_count = 0
        
        # 重置道具
        for powerup in self.powerups.values():
            powerup['active'] = False
            powerup['timer'] = 0
        
        # 清空粒子
        self.particles.clear()
        
        # 移動控制
        self.last_move_time = time.time()
        self.move_interval = 1.0 / self.base_speed
    
    def generate_food(self, food_type='normal'):
        """生成食物"""
        while True:
            pos = (random.randint(0, self.grid_width - 1), 
                  random.randint(0, self.grid_height - 1))
            
            # 確保不在蛇身上
            if pos not in self.snake and not any(food['pos'] == pos for food in self.foods):
                food = {
                    'pos': pos,
                    'type': food_type,
                    'spawn_time': time.time(),
                    'lifetime': 15.0 if food_type != 'normal' else float('inf')
                }
                
                # 特殊食物屬性
                if food_type == 'golden':
                    food['points'] = 5
                    food['growth'] = 2
                elif food_type == 'speed':
                    food['points'] = 3
                    food['powerup'] = 'speed_boost'
                elif food_type == 'multi':
                    food['points'] = 2
                    food['powerup'] = 'score_multiplier'
                elif food_type == 'bonus':
                    food['points'] = 10
                    food['powerup'] = 'invincible'
                elif food_type == 'phase':
                    food['points'] = 4
                    food['powerup'] = 'wall_phase'
                else:  # normal
                    food['points'] = 1
                    food['growth'] = 1
                
                self.foods.append(food)
                break
    
    def update_special_foods(self):
        """更新特殊食物生成"""
        current_time = time.time()
        
        # 生成特殊食物
        if current_time - self.special_food_timer >= self.special_food_interval:
            special_types = ['golden', 'speed', 'multi', 'bonus', 'phase']
            # 根據等級調整特殊食物出現概率
            weights = [3, 2, 2, 1, 1]  # 黃金食物出現率最高
            special_type = random.choices(special_types, weights=weights)[0]
            
            self.generate_food(special_type)
            self.special_food_timer = current_time
            
            # 隨著等級提升，特殊食物生成間隔縮短
            self.special_food_interval = max(5.0, 10.0 - self.level * 0.5)
        
        # 移除過期的特殊食物
        self.foods = [food for food in self.foods 
                     if food['type'] == 'normal' or 
                     (current_time - food['spawn_time']) < food['lifetime']]
    
    def update_powerups(self, delta_time):
        """更新道具效果"""
        for name, powerup in self.powerups.items():
            if powerup['active']:
                powerup['timer'] -= delta_time
                if powerup['timer'] <= 0:
                    powerup['active'] = False
                    # 道具結束效果
                    if name == 'score_multiplier':
                        self.score_multiplier = 1
                    elif name == 'speed_boost':
                        self.current_speed = self.base_speed
    
    def activate_powerup(self, powerup_type):
        """激活道具效果"""
        if powerup_type in self.powerups:
            powerup = self.powerups[powerup_type]
            powerup['active'] = True
            powerup['timer'] = powerup['duration']
            
            # 立即效果
            if powerup_type == 'score_multiplier':
                self.score_multiplier = 3
            elif powerup_type == 'speed_boost':
                self.current_speed = self.base_speed * 1.5
            
            # 播放道具音效
            if self.buzzer:
                self.buzzer.play_tone(frequency=800, duration=0.3)
    
    def create_particles(self, pos, color, count=5):
        """創建粒子效果"""
        for _ in range(count):
            particle = {
                'x': pos[0] * self.block_size + self.block_size // 2,
                'y': pos[1] * self.block_size + self.block_size // 2,
                'vx': random.uniform(-50, 50),
                'vy': random.uniform(-50, 50),
                'life': 1.0,
                'color': color,
                'size': random.uniform(2, 6)
            }
            self.particles.append(particle)
    
    def update_particles(self, delta_time):
        """更新粒子效果"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time * 2
            particle['vy'] += 100 * delta_time  # 重力效果
            
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
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # 處理輸入
        if controller_input:
            # 方向控制
            if controller_input.get("up_pressed") and self.direction != (0, 1):
                self.direction = (0, -1)
            elif controller_input.get("down_pressed") and self.direction != (0, -1):
                self.direction = (0, 1)
            elif controller_input.get("left_pressed") and self.direction != (1, 0):
                self.direction = (-1, 0)
            elif controller_input.get("right_pressed") and self.direction != (-1, 0):
                self.direction = (1, 0)
            
            # 加速控制
            self.boosting = controller_input.get("a_pressed", False)
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # 更新移動速度
        move_speed = self.current_speed
        if self.boosting:
            move_speed = self.speed_boost
        
        self.move_interval = 1.0 / move_speed
        
        # 檢查是否該移動
        if current_time - self.last_move_time < self.move_interval:
            # 更新其他系統
            self.update_special_foods()
            self.update_powerups(delta_time)
            self.update_particles(delta_time)
            return {"game_over": self.game_over, "score": self.score}
        
        self.last_move_time = current_time
        
        # 移動蛇
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # 邊界處理
        if self.powerups['wall_phase']['active']:
            # 穿牆模式
            new_head = (new_head[0] % self.grid_width, new_head[1] % self.grid_height)
        else:
            # 正常邊界檢查
            if (new_head[0] < 0 or new_head[0] >= self.grid_width or 
                new_head[1] < 0 or new_head[1] >= self.grid_height):
                self.game_over = True
                if self.buzzer:
                    self.buzzer.play_tone(frequency=200, duration=1.0)
                return {"game_over": True, "score": self.score}
        
        # 檢查碰撞到自己
        if new_head in self.snake and not self.powerups['invincible']['active']:
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_tone(frequency=200, duration=1.0)
            return {"game_over": True, "score": self.score}
        
        # 添加新頭部
        self.snake.insert(0, new_head)
        
        # 檢查是否吃到食物
        eaten_food = None
        for food in self.foods[:]:
            if new_head == food['pos']:
                eaten_food = food
                self.foods.remove(food)
                break
        
        if eaten_food:
            # 處理連擊
            if current_time - self.last_eat_time < self.combo_window:
                self.combo_count += 1
            else:
                self.combo_count = 1
            self.last_eat_time = current_time
            
            # 計算分數
            base_points = eaten_food['points']
            combo_bonus = self.combo_count * 0.5
            total_points = int(base_points * (1 + combo_bonus) * self.score_multiplier)
            self.score += total_points
            
            # 蛇身增長
            growth = eaten_food.get('growth', 1)
            for _ in range(growth - 1):  # -1 因為已經添加了新頭部
                if self.snake:
                    self.snake.append(self.snake[-1])
            
            # 激活道具效果
            if 'powerup' in eaten_food:
                self.activate_powerup(eaten_food['powerup'])
            
            # 創建粒子效果
            food_colors = {
                'normal': self.RED,
                'golden': self.GOLDEN_FOOD,
                'speed': self.SPEED_FOOD,
                'multi': self.MULTI_FOOD,
                'bonus': self.BONUS_FOOD,
                'phase': self.PURPLE
            }
            self.create_particles(eaten_food['pos'], 
                                food_colors.get(eaten_food['type'], self.RED), 
                                count=8 if eaten_food['type'] != 'normal' else 5)
            
            # 播放音效
            if self.buzzer:
                if eaten_food['type'] == 'normal':
                    freq = min(800 + self.combo_count * 100, 1500)
                    self.buzzer.play_tone(frequency=freq, duration=0.2)
                else:
                    # 特殊食物音效
                    self.buzzer.play_tone(frequency=1000, duration=0.1)
                    self.buzzer.play_tone(frequency=1200, duration=0.1)
            
            # 生成新的普通食物
            if eaten_food['type'] == 'normal':
                self.generate_food()
            
            # 升級檢查
            self.total_eaten += 1
            if self.total_eaten % 10 == 0:
                self.level += 1
                self.base_speed += 1
                if not self.powerups['speed_boost']['active']:
                    self.current_speed = self.base_speed
                if self.buzzer:
                    self.buzzer.play_tone(frequency=1500, duration=0.5)
        else:
            # 沒吃到食物，移除尾巴
            self.snake.pop()
        
        # 確保至少有一個普通食物
        if not any(food['type'] == 'normal' for food in self.foods):
            self.generate_food()
        
        # 更新其他系統
        self.update_special_foods()
        self.update_powerups(delta_time)
        self.update_particles(delta_time)
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """渲染遊戲畫面"""
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製食物
        for food in self.foods:
            food_colors = {
                'normal': self.RED,
                'golden': self.GOLDEN_FOOD,
                'speed': self.SPEED_FOOD,
                'multi': self.MULTI_FOOD,
                'bonus': self.BONUS_FOOD,
                'phase': self.PURPLE
            }
            
            color = food_colors.get(food['type'], self.RED)
            
            food_rect = pygame.Rect(
                food['pos'][0] * self.block_size,
                food['pos'][1] * self.block_size,
                self.block_size,
                self.block_size
            )
            
            # 特殊食物閃爍效果
            if food['type'] != 'normal':
                current_time = time.time()
                remaining_time = food['lifetime'] - (current_time - food['spawn_time'])
                if remaining_time < 3.0:  # 最後3秒閃爍
                    if int(current_time * 4) % 2:  # 4Hz閃爍
                        color = tuple(min(255, c + 50) for c in color)
            
            pygame.draw.rect(screen, color, food_rect)
            
            # 特殊食物標記
            if food['type'] != 'normal':
                center = food_rect.center
                pygame.draw.circle(screen, self.WHITE, center, 3)
        
        # 繪製蛇
        for i, segment in enumerate(self.snake):
            color = self.BLUE if i == 0 else self.GREEN
            
            # 無敵狀態閃爍效果
            if self.powerups['invincible']['active'] and int(time.time() * 6) % 2:
                color = tuple(min(255, c + 100) for c in color)
            
            segment_rect = pygame.Rect(
                segment[0] * self.block_size,
                segment[1] * self.block_size,
                self.block_size,
                self.block_size
            )
            pygame.draw.rect(screen, color, segment_rect)
            
            # 蛇頭裝飾
            if i == 0:
                pygame.draw.circle(screen, self.WHITE, segment_rect.center, 3)
        
        # 繪製粒子效果
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                color = (*particle['color'], alpha)
                size = max(1, int(particle['size'] * particle['life']))
                
                # 創建半透明表面
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color, (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))
        
        # 繪製UI
        font = pygame.font.Font(None, 36)
        
        # 基本信息
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        
        level_text = font.render(f"等級: {self.level}", True, self.WHITE)
        screen.blit(level_text, (10, 50))
        
        speed_text = font.render(f"速度: {self.current_speed}", True, self.WHITE)
        screen.blit(speed_text, (10, 90))
        
        # 連擊顯示
        if self.combo_count > 1:
            combo_text = font.render(f"連擊 x{self.combo_count}!", True, self.YELLOW)
            screen.blit(combo_text, (self.width - 200, 10))
        
        # 道具狀態顯示
        y_offset = 130
        font_small = pygame.font.Font(None, 24)
        
        powerup_names = {
            'invincible': '無敵',
            'speed_boost': '加速',
            'score_multiplier': '分數加倍',
            'wall_phase': '穿牆'
        }
        
        for name, powerup in self.powerups.items():
            if powerup['active']:
                remaining = powerup['timer']
                text = font_small.render(f"{powerup_names[name]}: {remaining:.1f}s", True, self.CYAN)
                screen.blit(text, (10, y_offset))
                y_offset += 25
        
        # 遊戲結束畫面
        if self.game_over:
            self.draw_game_over(screen)
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """繪製遊戲結束畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font = pygame.font.Font(None, 36)
        
        # 標題
        text = font_large.render("遊戲結束", True, self.RED)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 150))
        
        # 統計信息
        stats = [
            f"最終分數: {self.score}",
            f"達到等級: {self.level}",
            f"總共吃了: {self.total_eaten} 個食物",
            f"最高連擊: {self.combo_count}"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = font.render(stat, True, self.WHITE)
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2, 
                                  self.height // 2 - 50 + i * 40))
        
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                 self.height // 2 + 120))
    
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
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, 
                                  self.height // 2 + 10))
    
    def cleanup(self):
        """清理遊戲資源"""
        pass

# 向後兼容
SnakeGame = EnhancedSnakeGame

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 設置視窗
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("貪吃蛇遊戲測試")
        
        # 建立遊戲實例
        game = SnakeGame(screen_width, screen_height)
        
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
