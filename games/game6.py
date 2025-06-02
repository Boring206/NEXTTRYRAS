#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game6.py - 簡易迷宮遊戲實現

import random
import pygame
import time
from pygame.locals import *

class SimpleMazeGame:
    """簡易迷宮遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 遊戲元素大小
        self.block_size = 30     # 迷宮方塊尺寸
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
        self.WALL_COLOR = (100, 100, 100)
        self.PATH_COLOR = (200, 200, 200)
        self.PLAYER_COLOR = (0, 0, 255)
        self.EXIT_COLOR = (0, 255, 0)
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 迷宮生成參數
        self.min_maze_size = 15  # 最小迷宮大小
        self.max_maze_size = 20  # 最大迷宮大小
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.level = 1
        self.moves = 0
        self.start_time = time.time()
        
        # 生成迷宮
        self.generate_maze()
        
        # 設置玩家位置在入口
        self.player_pos = self.entrance
        
        # 用於控制輸入頻率
        self.last_input_time = time.time()
        self.input_delay = 0.15  # 秒
    
    def generate_maze(self):
        """生成迷宮"""
        # 根據等級調整迷宮大小
        size = min(self.min_maze_size + self.level - 1, self.max_maze_size)
        
        # 確保迷宮大小是奇數，便於生成算法
        if size % 2 == 0:
            size += 1
        
        self.maze_size = size
        
        # 初始化迷宮，0表示牆，1表示通路
        self.maze = [[0 for _ in range(size)] for _ in range(size)]
        
        # 使用深度優先搜索（DFS）生成迷宮
        self._generate_maze_dfs(1, 1)
        
        # 設置入口和出口
        self.entrance = (1, 0)  # 上方入口
        self.exit = (size - 2, size - 1)  # 下方出口
        
        # 確保入口和出口是通路
        self.maze[0][1] = 1
        self.maze[size-1][size-2] = 1
    
    def _generate_maze_dfs(self, x, y):
        """使用深度優先搜索生成迷宮"""
        # 標記當前位置為通路
        self.maze[y][x] = 1
        
        # 方向：上、右、下、左
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # 檢查是否在範圍內
            if 0 <= nx < self.maze_size and 0 <= ny < self.maze_size and self.maze[ny][nx] == 0:
                # 將中間的格子也設為通路
                self.maze[y + dy//2][x + dx//2] = 1
                
                # 遞迴繼續生成
                self._generate_maze_dfs(nx, ny)
    
    def is_valid_move(self, new_pos):
        """檢查是否是有效的移動"""
        x, y = new_pos
        
        # 檢查是否在迷宮範圍內
        if not (0 <= y < self.maze_size and 0 <= x < self.maze_size):
            return True if new_pos == self.exit else False
        
        # 檢查是否是牆
        return self.maze[y][x] == 1
    
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
            
            return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        # 處理玩家輸入
        current_time = time.time()
        if current_time - self.last_input_time < self.input_delay:
            # 輸入延遲中，不處理輸入
            return {"game_over": self.game_over, "level": self.level}
        
        # 處理輸入
        if controller_input:
            input_detected = False
            x, y = self.player_pos
            new_pos = (x, y)
            
            # 方向控制
            if controller_input.get("up_pressed"):
                new_pos = (x, y - 1)
                input_detected = True
            elif controller_input.get("down_pressed"):
                new_pos = (x, y + 1)
                input_detected = True
            elif controller_input.get("left_pressed"):
                new_pos = (x - 1, y)
                input_detected = True
            elif controller_input.get("right_pressed"):
                new_pos = (x + 1, y)
                input_detected = True
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                input_detected = True
                return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
            
            # 如果檢測到輸入，重置輸入延遲計時器
            if input_detected:
                self.last_input_time = current_time
                
                # 檢查移動是否有效
                if self.is_valid_move(new_pos):
                    old_pos = self.player_pos
                    self.player_pos = new_pos
                    self.moves += 1
                    
                    # 播放移動音效
                    if self.buzzer:
                        self.buzzer.play_tone("navigate")
                    
                    # 檢查是否到達出口
                    if self.player_pos == self.exit:
                        # 增加等級
                        self.level += 1
                        
                        # 播放通關音效
                        if self.buzzer:
                            # 增強通關音效序列
                            victory_notes = [523, 659, 784, 1047, 1319]  # C大調音階向上
                            for note in victory_notes:
                                self.buzzer.play_tone(frequency=note, duration=0.2)
                                time.sleep(0.1)
                        
                        # 生成新的更複雜迷宮
                        self.generate_maze()
                        self.player_pos = self.entrance
                        
                        return {"game_over": False, "level_complete": True, "level": self.level}
                else:
                    # 播放無效移動音效
                    if self.buzzer:
                        self.buzzer.play_tone("error")
        
        return {"game_over": self.game_over, "level": self.level}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 計算迷宮繪製的起始位置，使其居中
        cell_size = min(self.width // self.maze_size, self.height // self.maze_size)
        start_x = (self.width - self.maze_size * cell_size) // 2
        start_y = (self.height - self.maze_size * cell_size) // 2
        
        # 繪製迷宮
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                rect = pygame.Rect(
                    start_x + x * cell_size,
                    start_y + y * cell_size,
                    cell_size,
                    cell_size
                )
                
                # 繪製牆或通路
                if self.maze[y][x] == 0:
                    pygame.draw.rect(screen, self.WALL_COLOR, rect)
                else:
                    pygame.draw.rect(screen, self.PATH_COLOR, rect)
                    
                # 添加格線效果
                pygame.draw.rect(screen, self.BLACK, rect, 1)
        
        # 繪製入口和出口
        entrance_rect = pygame.Rect(
            start_x + self.entrance[0] * cell_size,
            start_y + self.entrance[1] * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, self.BLUE, entrance_rect)
        
        exit_rect = pygame.Rect(
            start_x + self.exit[0] * cell_size,
            start_y + self.exit[1] * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, self.EXIT_COLOR, exit_rect)
        
        # 繪製玩家
        player_rect = pygame.Rect(
            start_x + self.player_pos[0] * cell_size,
            start_y + self.player_pos[1] * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, self.PLAYER_COLOR, player_rect)
        
        # 繪製遊戲資訊
        font = pygame.font.Font(None, 36)
        
        # 等級信息
        level_text = font.render(f"等級: {self.level}", True, self.WHITE)
        screen.blit(level_text, (10, 10))
        
        # 移動次數
        moves_text = font.render(f"移動: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (10, 50))
        
        # 遊戲時間
        elapsed_time = int(time.time() - self.start_time)
        time_text = font.render(f"時間: {elapsed_time}秒", True, self.WHITE)
        screen.blit(time_text, (10, 90))
        
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
        level_text = font.render(f"達成等級: {self.level}", True, self.WHITE)
        screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, self.height // 2 + 10))
        
        moves_text = font.render(f"總移動次數: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width // 2 - moves_text.get_width() // 2, self.height // 2 + 50))
        
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
        pygame.display.set_caption("簡易迷宮遊戲測試")
        
        # 建立遊戲實例
        game = SimpleMazeGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_y: "y_pressed",
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
            game.update(controller_input)
            
            # 渲染
            game.render(screen)
            pygame.display.flip()
            
            # 控制幀率
            clock.tick(30)

    except Exception as e:
        print(f"遊戲執行過程中發生錯誤: {e}")
    finally:
        pygame.quit()
        print("簡易迷宮遊戲測試結束")
