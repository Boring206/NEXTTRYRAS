#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game4.py - 井字遊戲實現

import random
import pygame
import time
from pygame.locals import *

class TicTacToeGame:
    """井字遊戲類"""
    
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
        self.GRAY = (128, 128, 128)
        
        # 遊戲元素大小
        self.board_size = min(width, height) - 100
        self.grid_size = self.board_size // 3
        self.board_x = (width - self.board_size) // 2
        self.board_y = (height - self.board_size) // 2
        self.line_width = 5
        
        # 遊戲速度相關
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # 初始化遊戲狀態
        self.reset_game()
    
    def reset_game(self):
        """重置遊戲狀態"""
        # 遊戲板 (3x3)，0=空, 1=X, 2=O
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # 游標位置
        self.cursor_x = 1
        self.cursor_y = 1
        
        # 當前玩家 (1=X, 2=O)
        self.current_player = 1
        
        # 遊戲狀態
        self.game_over = False
        self.paused = False
        self.winner = 0  # 0=平局, 1=X贏, 2=O贏
        
        # 最後的輸入時間 (用於控制輸入頻率)
        self.last_input_time = time.time()
        self.input_delay = 0.2  # 秒
        
        # 電腦玩家
        self.vs_computer = True
        self.computer_delay = 1.0  # 電腦決策延遲 (秒)
        self.computer_last_move = time.time()
    
    def make_move(self, x, y):
        """進行遊戲回合"""
        # 如果該格子已被佔用，則不做任何事
        if self.board[y][x] != 0:
            return False
        
        # 放置棋子
        self.board[y][x] = self.current_player
        
        # 播放音效
        if self.buzzer:
            self.buzzer.play_tone(frequency=600, duration=0.2)
        
        # 檢查遊戲是否結束
        if self.check_win():
            self.game_over = True
            self.winner = self.current_player
            if self.buzzer:
                self.buzzer.play_tone(frequency=1000, duration=0.5)
        elif self.check_draw():
            self.game_over = True
            self.winner = 0
            if self.buzzer:
                self.buzzer.play_tone(frequency=400, duration=0.8)
        else:
            # 切換玩家
            self.current_player = 2 if self.current_player == 1 else 1
        
        return True
    
    def check_win(self):
        """檢查是否有人獲勝"""
        player = self.current_player
        
        # 檢查水平線
        for y in range(3):
            if all(self.board[y][x] == player for x in range(3)):
                return True
        
        # 檢查垂直線
        for x in range(3):
            if all(self.board[y][x] == player for y in range(3)):
                return True
        
        # 檢查對角線
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True
        
        return False
    
    def check_draw(self):
        """檢查是否平局"""
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    return False
        return True
    
    def computer_move(self):
        """電腦玩家進行回合"""
        # 檢查是否該電腦行動
        if not self.vs_computer or self.current_player != 2:
            return False
        
        current_time = time.time()
        if current_time - self.computer_last_move < self.computer_delay:
            return False
        
        self.computer_last_move = current_time
        
        # 檢查是否可以贏
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    self.board[y][x] = 2
                    if self.check_win_for_player(2):
                        self.board[y][x] = 0
                        return self.make_move(x, y)
                    self.board[y][x] = 0
        
        # 檢查是否需要阻擋對手
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    self.board[y][x] = 1
                    if self.check_win_for_player(1):
                        self.board[y][x] = 0
                        return self.make_move(x, y)
                    self.board[y][x] = 0
        
        # 嘗試佔據中央
        if self.board[1][1] == 0:
            return self.make_move(1, 1)
        
        # 隨機移動
        empty_cells = []
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    empty_cells.append((x, y))
        
        if empty_cells:
            x, y = random.choice(empty_cells)
            return self.make_move(x, y)
        
        return False
    
    def check_win_for_player(self, player):
        """檢查指定玩家是否獲勝"""
        # 檢查水平線
        for y in range(3):
            if all(self.board[y][x] == player for x in range(3)):
                return True
        
        # 檢查垂直線
        for x in range(3):
            if all(self.board[y][x] == player for y in range(3)):
                return True
        
        # 檢查對角線
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True
        
        return False
    
    def update(self, controller_input=None):
        """更新遊戲狀態"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "winner": self.winner}
        
        # 處理電腦移動
        if self.vs_computer and self.current_player == 2:
            self.computer_move()
        
        # 處理玩家輸入
        current_time = time.time()
        if current_time - self.last_input_time < self.input_delay:
            return {"game_over": self.game_over, "winner": self.winner}
        
        if controller_input:
            moved = False
            
            if controller_input.get("up_pressed") and self.cursor_y > 0:
                self.cursor_y -= 1
                moved = True
            elif controller_input.get("down_pressed") and self.cursor_y < 2:
                self.cursor_y += 1
                moved = True
            elif controller_input.get("left_pressed") and self.cursor_x > 0:
                self.cursor_x -= 1
                moved = True
            elif controller_input.get("right_pressed") and self.cursor_x < 2:
                self.cursor_x += 1
                moved = True
            elif controller_input.get("a_pressed"):
                if not self.vs_computer or self.current_player == 1:
                    self.make_move(self.cursor_x, self.cursor_y)
                moved = True
            elif controller_input.get("y_pressed"):
                self.vs_computer = not self.vs_computer
                moved = True
            elif controller_input.get("start_pressed"):
                self.paused = True
                moved = True
            
            if moved:
                self.last_input_time = current_time
        
        return {"game_over": self.game_over, "winner": self.winner}
    
    def render(self, screen):
        """渲染遊戲畫面"""
        # 清除螢幕
        screen.fill(self.BLACK)
        
        # 繪製遊戲板背景
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(screen, self.WHITE, board_rect)
        
        # 繪製網格線
        for i in range(1, 3):
            # 垂直線
            start_pos = (self.board_x + i * self.grid_size, self.board_y)
            end_pos = (self.board_x + i * self.grid_size, self.board_y + self.board_size)
            pygame.draw.line(screen, self.BLACK, start_pos, end_pos, self.line_width)
            
            # 水平線
            start_pos = (self.board_x, self.board_y + i * self.grid_size)
            end_pos = (self.board_x + self.board_size, self.board_y + i * self.grid_size)
            pygame.draw.line(screen, self.BLACK, start_pos, end_pos, self.line_width)
        
        # 繪製棋子
        for y in range(3):
            for x in range(3):
                if self.board[y][x] != 0:
                    center_x = self.board_x + x * self.grid_size + self.grid_size // 2
                    center_y = self.board_y + y * self.grid_size + self.grid_size // 2
                    
                    if self.board[y][x] == 1:  # X
                        size = self.grid_size // 3
                        pygame.draw.line(screen, self.RED,
                                       (center_x - size, center_y - size),
                                       (center_x + size, center_y + size), 8)
                        pygame.draw.line(screen, self.RED,
                                       (center_x + size, center_y - size),
                                       (center_x - size, center_y + size), 8)
                    else:  # O
                        radius = self.grid_size // 3
                        pygame.draw.circle(screen, self.BLUE, (center_x, center_y), radius, 8)
        
        # 繪製游標
        if not self.game_over and not self.paused and (not self.vs_computer or self.current_player == 1):
            cursor_x = self.board_x + self.cursor_x * self.grid_size
            cursor_y = self.board_y + self.cursor_y * self.grid_size
            cursor_rect = pygame.Rect(cursor_x, cursor_y, self.grid_size, self.grid_size)
            pygame.draw.rect(screen, self.YELLOW, cursor_rect, 5)
        
        # 繪製遊戲資訊
        font = pygame.font.Font(None, 36)
        
        # 顯示當前玩家
        if not self.game_over and not self.paused:
            player_text = f"當前玩家: {'X (你)' if self.current_player == 1 else 'O (電腦)' if self.vs_computer else 'O (玩家2)'}"
            player_surface = font.render(player_text, True, self.WHITE)
            screen.blit(player_surface, (20, 20))
        
        # 顯示遊戲模式
        mode_text = "模式: " + ("VS 電腦" if self.vs_computer else "雙人對戰")
        mode_surface = font.render(mode_text, True, self.WHITE)
        screen.blit(mode_surface, (self.width - mode_surface.get_width() - 20, 20))
        
        # 顯示控制提示
        hint_text = "按 Y 切換模式，A 選擇，方向鍵移動"
        hint_surface = font.render(hint_text, True, self.GRAY)
        screen.blit(hint_surface, (self.width // 2 - hint_surface.get_width() // 2, self.height - 40))
        
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
        
        font = pygame.font.Font(None, 72)
        
        if self.winner == 0:
            result_text = "平局！"
            color = self.YELLOW
        else:
            if self.winner == 1:
                result_text = "X 獲勝！"
                color = self.RED
            else:
                result_text = "O 獲勝！" + (" (電腦贏了)" if self.vs_computer else " (玩家2贏了)")
                color = self.BLUE
        
        text = font.render(result_text, True, color)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        restart_text = font.render("按 Start 重新開始", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 20))
    
    def draw_pause(self, screen):
        """繪製暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("暫停", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))

    
    def cleanup(self):
        """清理遊戲資源"""
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("井字遊戲測試")
        
        game = TicTacToeGame(800, 600)
        clock = pygame.time.Clock()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            keys = pygame.key.get_pressed()
            controller_input = {
                "up_pressed": keys[pygame.K_UP],
                "down_pressed": keys[pygame.K_DOWN],
                "left_pressed": keys[pygame.K_LEFT],
                "right_pressed": keys[pygame.K_RIGHT],
                "a_pressed": keys[pygame.K_a],
                "y_pressed": keys[pygame.K_y],
                "start_pressed": keys[pygame.K_RETURN]
            }
            
            game.update(controller_input)
            game.render(screen)
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
    except Exception as e:
        print(f"遊戲執行錯誤: {e}")
        pygame.quit()
