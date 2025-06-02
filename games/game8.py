#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game8.py - 俄羅斯方塊遊戲實現

import random
import pygame
import time
from pygame.locals import *

class TetrisLikeGame:
    """俄羅斯方塊遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # 遊戲區域寬度
        self.height = height     # 遊戲區域高度
        self.buzzer = buzzer     # 蜂鳴器實例，用於音效回饋
        
        # 遊戲參數
        self.grid_width = 10     # 遊戲區域寬度 (方塊數)
        self.grid_height = 20    # 遊戲區域高度 (方塊數)
        self.block_size = min(width // 20, height // 22)
        
        # 遊戲區域位置
        self.board_x = (width - self.grid_width * self.block_size) // 2
        self.board_y = height - self.grid_height * self.block_size - 20
        
        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (128, 128, 128)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.CYAN = (0, 255, 255)
        self.MAGENTA = (255, 0, 255)
        self.ORANGE = (255, 165, 0)
        
        # 方塊顏色
        self.BLOCK_COLORS = [
            self.RED,
            self.GREEN,
            self.BLUE,
            self.YELLOW,
            self.CYAN,
            self.MAGENTA,
            self.ORANGE
        ]
        
        # 方塊形狀 (各種排列方式)
        # 每個形狀都是一個 4x4 的網格，其中 1 表示方塊存在，0 表示空白
        self.SHAPES = [
            # I 形
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # J 形
            [
                [1, 0, 0, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # L 形
            [
                [0, 0, 1, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # O 形
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # S 形
            [
                [0, 1, 1, 0],
                [1, 1, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # T 形
            [
                [0, 1, 0, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # Z 形
            [
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ]
        ]
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        
        # 遊戲區域 (0表示空白，大於0表示方塊的顏色索引)
        self.board = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # 當前下落的方塊
        self.current_shape = None
        self.current_color = None
        self.current_x = 0
        self.current_y = 0
        self.current_rotation = 0
        
        # 生成第一個方塊
        self.generate_new_shape()
        
        # 下落時間控制
        self.last_drop_time = time.time()
        self.drop_interval = 1.0  # 初始下落間隔 (秒)
        
        # 輸入控制
        self.last_input_time = time.time()
        self.input_delay = 0.1  # 秒
        
        # 快速下落標記
        self.fast_drop = False
    
    def generate_new_shape(self):
        """生成一個新的隨機方塊"""
        # 選擇隨機形狀和顏色
        shape_idx = random.randint(0, len(self.SHAPES) - 1)
        self.current_shape = self.SHAPES[shape_idx]
        self.current_color = shape_idx + 1  # 顏色索引從 1 開始，0 表示空白
        
        # 設置初始位置 (居中)
        self.current_x = self.grid_width // 2 - 2
        self.current_y = 0
        self.current_rotation = 0
        
        # 檢查遊戲是否結束 (如果新方塊與已有方塊重疊)
        if self.is_collision():
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_game_over_melody()
    
    def rotate_shape(self, shape):
        """旋轉方塊 (順時針旋轉90度)"""
        # 轉置矩陣
        transposed = [[shape[y][x] for y in range(4)] for x in range(4)]
        
        # 反轉每行 (順時針旋轉)
        rotated = [row[::-1] for row in transposed]
        
        return rotated
    
    def is_collision(self):
        """檢查當前方塊是否與邊界或其他方塊碰撞"""
        for y in range(4):
            for x in range(4):
                if self.current_shape[y][x] == 0:
                    continue
                    
                board_x = self.current_x + x
                board_y = self.current_y + y
                
                # 檢查是否超出邊界
                if (board_x < 0 or board_x >= self.grid_width or
                    board_y < 0 or board_y >= self.grid_height):
                    return True
                
                # 檢查是否與已有方塊重疊
                if board_y >= 0 and self.board[board_y][board_x] > 0:
                    return True
                    
        return False
    
    def move_left(self):
        """嘗試將當前方塊向左移動"""
        self.current_x -= 1
        if self.is_collision():
            self.current_x += 1
            return False
        
        if self.buzzer:
            self.buzzer.play_tone("navigate")
        return True
    
    def move_right(self):
        """嘗試將當前方塊向右移動"""
        self.current_x += 1
        if self.is_collision():
            self.current_x -= 1
            return False
        
        if self.buzzer:
            self.buzzer.play_tone("navigate")
        return True
    
    def move_down(self):
        """嘗試將當前方塊向下移動"""
        self.current_y += 1
        if self.is_collision():
            self.current_y -= 1
            self.lock_shape()
            return False
        return True
    
    def rotate(self):
        """嘗試旋轉當前方塊"""
        original_shape = self.current_shape
        self.current_shape = self.rotate_shape(self.current_shape)
        
        # 如果旋轉後碰撞，嘗試左右移動調整位置
        if self.is_collision():
            # 嘗試向左移動
            self.current_x -= 1
            if self.is_collision():
                # 嘗試向右移動
                self.current_x += 2
                if self.is_collision():
                    # 如果仍然無法旋轉，恢復原始形狀和位置
                    self.current_x -= 1
                    self.current_shape = original_shape
                    return False
        
        if self.buzzer:
            self.buzzer.play_tone("select")
        return True
    
    def hard_drop(self):
        """快速下落方塊到底部"""
        while self.move_down():
            pass
        
        if self.buzzer:
            self.buzzer.play_tone("score")
    
    def lock_shape(self):
        """將當前方塊鎖定到遊戲區域"""
        for y in range(4):
            for x in range(4):
                if self.current_shape[y][x] == 0:
                    continue
                
                board_y = self.current_y + y
                board_x = self.current_x + x
                
                # 確保在遊戲區域內
                if 0 <= board_y < self.grid_height and 0 <= board_x < self.grid_width:
                    self.board[board_y][board_x] = self.current_color
        
        # 檢查並清除滿行
        self.check_lines()
        
        # 生成新方塊
        self.generate_new_shape()
    
    def check_lines(self):
        """檢查並清除滿行"""
        lines_to_clear = []
        
        # 檢查哪些行已滿
        for y in range(self.grid_height):
            if all(self.board[y][x] > 0 for x in range(self.grid_width)):
                lines_to_clear.append(y)
        
        # 清除行
        for line in lines_to_clear:
            # 將上方行向下移動
            for y in range(line, 0, -1):
                self.board[y] = self.board[y - 1][:]
            
            # 頂部行設為空
            self.board[0] = [0] * self.grid_width
        
        # 計算得分
        if lines_to_clear:
            # 基本分數: 行數 * 100 * 等級
            points = len(lines_to_clear) * 100 * self.level
            self.score += points
            
            # 增加已清除行數
            self.lines_cleared += len(lines_to_clear)
            
            # 每清除 10 行，等級提升
            if self.lines_cleared // 10 > (self.lines_cleared - len(lines_to_clear)) // 10:
                self.level_up()
            
            # 播放清除行音效
            if self.buzzer:
                if len(lines_to_clear) >= 4:
                    self.buzzer.play_win_melody()  # 一次清除 4 行（Tetris）
                else:
                    self.buzzer.play_tone("level_up")
    
    def level_up(self):
        """提升等級，增加速度"""
        self.level += 1
        self.drop_interval = max(0.1, 1.0 - 0.05 * (self.level - 1))
        
        # 增強音效系統
        if self.buzzer:
            # 播放等級提升音效序列
            frequencies = [523, 659, 784, 1047]  # C5, E5, G5, C6
            for freq in frequencies:
                self.buzzer.play_tone(frequency=freq, duration=0.15)
                time.sleep(0.05)
    
    def clear_lines(self, lines_to_clear):
        """清除滿行，增強視覺和音效效果"""
        if not lines_to_clear:
            return
        
        # 閃爍效果
        for flash in range(3):
            for row in lines_to_clear:
                for col in range(self.grid_width):
                    self.grid[row][col] = 9  # 特殊標記
            time.sleep(0.1)
            
            for row in lines_to_clear:
                for col in range(self.grid_width):
                    self.grid[row][col] = 0
            time.sleep(0.1)
        
        # 移除行並添加新行
        for row in sorted(lines_to_clear, reverse=True):
            del self.grid[row]
            self.grid.insert(0, [0] * self.grid_width)
        
        # 更新分數和音效
        lines_count = len(lines_to_clear)
        base_score = [0, 100, 300, 500, 800][min(lines_count, 4)]
        self.score += base_score * self.level
        self.lines_cleared += lines_count
        
        # 音效回饋
        if self.buzzer:
            if lines_count == 4:  # Tetris
                self.buzzer.play_tetris_fanfare()
            elif lines_count >= 2:
                self.buzzer.play_multi_line_clear()
            else:
                self.buzzer.play_single_line_clear()
        
        # 等級檢查
        if self.lines_cleared >= self.level * 10:
            self.level_up()

    def update(self, controller_input=None):
        """更新遊戲狀態，增強輸入處理"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        current_time = time.time()
        
        # 處理輸入
        if controller_input:
            # 移動控制（防止過快輸入）
            if current_time - self.last_input_time > 0.1:
                moved = False
                
                if controller_input.get("left_pressed"):
                    if self.move_piece(-1, 0):
                        moved = True
                elif controller_input.get("right_pressed"):
                    if self.move_piece(1, 0):
                        moved = True
                elif controller_input.get("down_pressed"):
                    if self.move_piece(0, 1):
                        moved = True
                        self.score += 1  # 軟降分數
                
                if moved:
                    self.last_input_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=400, duration=0.05)
            
            # 旋轉控制
            if controller_input.get("up_pressed") and current_time - self.last_rotate_time > 0.2:
                if self.rotate_piece():
                    self.last_rotate_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=600, duration=0.1)
            
            # 硬降控制
            if controller_input.get("a_pressed") and current_time - self.last_hard_drop_time > 0.3:
                drop_distance = self.hard_drop_piece()
                if drop_distance > 0:
                    self.score += drop_distance * 2
                    self.last_hard_drop_time = current_time
                    if self.buzzer:
                        self.buzzer.play_hard_drop()
            
            # 暫停控制
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        # 自動下降邏輯
        if current_time - self.last_drop_time >= self.drop_interval:
            if not self.move_piece(0, 1):
                self.lock_piece()
                lines_to_clear = self.check_for_lines()
                if lines_to_clear:
                    self.clear_lines(lines_to_clear)
                
                self.spawn_new_piece()
                
                if self.check_collision():
                    self.game_over = True
                    if self.buzzer:
                        self.buzzer.play_game_over_melody()
            
            self.last_drop_time = current_time
        
        return {"game_over": self.game_over, "level": self.level, "score": self.score}
    
    def render(self, screen):
        """
        渲染遊戲畫面
        
        參數:
            screen: pygame 螢幕物件
        """
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製遊戲區域邊框
        board_rect = pygame.Rect(
            self.board_x - 1,
            self.board_y - 1,
            self.grid_width * self.block_size + 2,
            self.grid_height * self.block_size + 2
        )
        pygame.draw.rect(screen, self.WHITE, board_rect, 2)
        
        # 繪製已鎖定的方塊
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.board[y][x] > 0:
                    color_idx = self.board[y][x] - 1
                    color = self.BLOCK_COLORS[color_idx]
                    
                    block_rect = pygame.Rect(
                        self.board_x + x * self.block_size,
                        self.board_y + y * self.block_size,
                        self.block_size,
                        self.block_size
                    )
                    pygame.draw.rect(screen, color, block_rect)
                    pygame.draw.rect(screen, self.WHITE, block_rect, 1)
        
        # 繪製當前下落的方塊
        if self.current_shape:
            for y in range(4):
                for x in range(4):
                    if self.current_shape[y][x] > 0:
                        color = self.BLOCK_COLORS[self.current_color - 1]
                        
                        block_rect = pygame.Rect(
                            self.board_x + (self.current_x + x) * self.block_size,
                            self.board_y + (self.current_y + y) * self.block_size,
                            self.block_size,
                            self.block_size
                        )
                        pygame.draw.rect(screen, color, block_rect)
                        pygame.draw.rect(screen, self.WHITE, block_rect, 1)
        
        # 繪製遊戲資訊
        font = pygame.font.Font(None, 36)
        
        # 分數
        score_text = font.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (20, 20))
        
        # 等級
        level_text = font.render(f"等級: {self.level}", True, self.WHITE)
        screen.blit(level_text, (20, 60))
        
        # 已清除行數
        lines_text = font.render(f"行數: {self.lines_cleared}", True, self.WHITE)
        screen.blit(lines_text, (20, 100))
        
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
        
        level_text = font.render(f"達成等級: {self.level}", True, self.WHITE)
        screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, self.height // 2 + 50))
        
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
        pygame.display.set_caption("俄羅斯方塊遊戲測試")
        
        # 建立遊戲實例
        game = TetrisLikeGame(screen_width, screen_height)
        
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
