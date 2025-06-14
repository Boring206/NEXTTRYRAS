#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game4.py - Tic Tac Toe Game Implementation (Enhanced)
# game4.py - 井字遊戲實作（增強版）

import random
import pygame
import time
from pygame.locals import *

class TicTacToeGame:
    """Tic Tac Toe Game Class (Enhanced)"""
    # 井字遊戲類別（增強版）

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width    # 遊戲區域寬度
        self.height = height   # 遊戲區域高度
        self.buzzer = buzzer   # 蜂鳴器實例，用於聲音反饋

        # 顏色定義
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (220, 50, 50)   # X 的顏色 (稍作調整)
        self.BLUE = (50, 50, 220)  # O 的顏色 (稍作調整)
        self.GREEN = (0, 180, 0)   # 獲勝線的顏色
        self.YELLOW = (255, 220, 0) # 游標顏色
        self.GRAY = (128, 128, 128) # 提示文字顏色
        self.LIGHT_GRAY = (200, 200, 200) # 棋盤背景

        # 遊戲元素尺寸
        self.board_size = min(width, height) - 150 # 棋盤大小，留出更多空間給UI
        self.grid_size = self.board_size // 3      # 每格大小
        self.board_x = (width - self.board_size) // 2 # 棋盤左上角X座標
        self.board_y = (height - self.board_size) // 2 + 20 # 棋盤左上角Y座標 (稍微向下移)
        self.line_width = 8 # 格線寬度
        self.piece_line_width = 10 # X和O的線條寬度

        # 字型初始化
        try:
            self.font_large = pygame.font.Font(None, 72)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 28) # 用於提示
            print("字型載入成功。")
        except Exception as e:
            print(f"字型載入失敗: {e}")
            self.font_large = pygame.font.SysFont("arial", 68)
            self.font_medium = pygame.font.SysFont("arial", 32)
            self.font_small = pygame.font.SysFont("arial", 24)

        # 遊戲速度設定
        self.clock = pygame.time.Clock()
        self.fps = 30 # 井字遊戲不需要太高幀率

        # 分數記錄
        self.score_x = 0
        self.score_o = 0
        self.score_draw = 0

        # 初始化遊戲狀態
        self.reset_game()

    def reset_game(self):
        """重置遊戲狀態以開始新的一局"""
        # 遊戲棋盤 (3x3), 0=空格, 1=X, 2=O
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        # 游標位置 (0, 1, 2)
        self.cursor_row = 1
        self.cursor_col = 1

        # 目前玩家 (1=X, 2=O)
        self.current_player = 1 # X 先手

        # 遊戲狀態
        self.game_over = False
        self.paused = False # 目前未使用，但保留結構
        self.winner = 0      # 0=平手, 1=X贏, 2=O贏
        self.winning_line_coords = None # 獲勝線的起始和結束座標

        # 輸入延遲控制
        self.last_input_time = time.time()
        self.input_delay = 0.18  # 秒 (稍微縮短輸入延遲)

        # 電腦玩家設定
        self.vs_computer = False # 修改點：預設為雙人對戰 (原為 True)
        self.computer_delay = 0.7  # 電腦思考延遲 (秒)
        self.computer_last_move_time = 0 # 電腦上次移動時間，用於控制電腦移動頻率

    def make_move(self, row, col):
        """玩家或電腦下棋"""
        if self.board[row][col] != 0: # 如果格子已被佔據
            if self.buzzer: self.buzzer.play_tone(frequency=200, duration=0.1) # 無效移動音效
            return False # 移動無效

        self.board[row][col] = self.current_player # 放置棋子

        if self.buzzer:
            freq = 600 if self.current_player == 1 else 700
            self.buzzer.play_tone(frequency=freq, duration=0.15) # 下棋音效

        # 檢查遊戲是否結束
        if self.check_win():
            self.game_over = True
            self.winner = self.current_player
            self.update_score()
            if self.buzzer: self.buzzer.play_tone(frequency=1000, duration=0.5) # 勝利音效
        elif self.check_draw():
            self.game_over = True
            self.winner = 0 # 0 代表平手
            self.update_score()
            if self.buzzer: self.buzzer.play_tone(frequency=400, duration=0.8) # 平手音效
        else:
            # 切換玩家
            self.current_player = 2 if self.current_player == 1 else 1
            if self.vs_computer and self.current_player == 2:
                self.computer_last_move_time = time.time() # 重置電腦移動計時器

        return True

    def update_score(self):
        """更新分數統計"""
        if self.winner == 1:
            self.score_x += 1
        elif self.winner == 2:
            self.score_o += 1
        elif self.winner == 0 and self.game_over: # 確保是平局結束
            self.score_draw += 1

    def check_win(self):
        """檢查目前玩家是否獲勝，並記錄獲勝線座標"""
        player = self.current_player
        board_coords = lambda r, c: (
            self.board_x + c * self.grid_size + self.grid_size // 2,
            self.board_y + r * self.grid_size + self.grid_size // 2
        )

        # 檢查行
        for r in range(3):
            if all(self.board[r][c] == player for c in range(3)):
                self.winning_line_coords = (board_coords(r, 0), board_coords(r, 2))
                return True
        # 檢查列
        for c in range(3):
            if all(self.board[r][c] == player for r in range(3)):
                self.winning_line_coords = (board_coords(0, c), board_coords(2, c))
                return True
        # 檢查對角線
        if all(self.board[i][i] == player for i in range(3)):
            self.winning_line_coords = (board_coords(0, 0), board_coords(2, 2))
            return True
        if all(self.board[i][2 - i] == player for i in range(3)):
            self.winning_line_coords = (board_coords(0, 2), board_coords(2, 0))
            return True
        return False

    def check_draw(self):
        """檢查是否平手 (所有格子都已填滿且無人獲勝)"""
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0: # 只要有空格，就不是平手
                    return False
        return True # 沒有空格了，就是平手

    def computer_move(self):
        """電腦AI下棋邏輯"""
        if not self.vs_computer or self.current_player != 2 or self.game_over:
            return False # 不是電腦的回合或遊戲已結束

        current_time = time.time()
        if current_time - self.computer_last_move_time < self.computer_delay:
            return False # 電腦思考中

        # 1. 檢查電腦是否能贏
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0:
                    self.board[r][c] = 2 # 假設電腦下在這裡
                    if self.check_win_for_player(2): # 檢查是否能贏
                        self.board[r][c] = 0 # 恢復棋盤
                        self.make_move(r, c)
                        return True
                    self.board[r][c] = 0 # 恢復棋盤

        # 2. 檢查玩家是否快要贏了，進行阻擋
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0:
                    self.board[r][c] = 1 # 假設玩家下在這裡
                    if self.check_win_for_player(1): # 檢查玩家是否能贏
                        self.board[r][c] = 0 # 恢復棋盤
                        self.make_move(r, c) # 電腦阻擋
                        return True
                    self.board[r][c] = 0 # 恢復棋盤

        # 3. 嘗試佔領中間位置
        if self.board[1][1] == 0:
            self.make_move(1, 1)
            return True

        # 4. 嘗試佔領角落位置
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
        random.shuffle(corners) # 隨機打亂角落順序
        for r, c in corners:
            if self.board[r][c] == 0:
                self.make_move(r, c)
                return True

        # 5. 嘗試佔領邊中間位置
        sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
        random.shuffle(sides) # 隨機打亂邊中間順序
        for r, c in sides:
            if self.board[r][c] == 0:
                self.make_move(r, c)
                return True
        
        # 6. 如果以上都沒有，隨機選擇一個空格 (理論上不太會到這一步，除非棋盤已滿)
        empty_cells = []
        for r_idx in range(3):
            for c_idx in range(3):
                if self.board[r_idx][c_idx] == 0:
                    empty_cells.append((r_idx, c_idx))
        if empty_cells:
            r_choice, c_choice = random.choice(empty_cells)
            self.make_move(r_choice, c_choice)
            return True
            
        return False # 沒有可下的位置 (不太可能發生)

    def check_win_for_player(self, player_id):
        """檢查指定玩家是否獲勝 (用於AI判斷)"""
        # 檢查行
        for r in range(3):
            if all(self.board[r][c] == player_id for c in range(3)): return True
        # 檢查列
        for c in range(3):
            if all(self.board[r][c] == player_id for r in range(3)): return True
        # 檢查對角線
        if all(self.board[i][i] == player_id for i in range(3)): return True
        if all(self.board[i][2 - i] == player_id for i in range(3)): return True
        return False

    def update(self, controller_input=None):
        """更新遊戲狀態"""
        current_time = time.time()

        if self.game_over: # 如果遊戲已結束
            if controller_input and controller_input.get("start_pressed"):
                if current_time - self.last_input_time >= self.input_delay * 2: # 需要更長的延遲來重置
                    self.reset_game()
                    # 當從遊戲結束畫面重置時，若之前是人機，Y鍵切換後reset_game會設為雙人
                    # 若希望保持切換後的模式，則reset_game不應強制修改vs_computer
                    # 但目前的修改是讓reset_game總是設為雙人，所以這裡行為一致
                    self.last_input_time = current_time
            return {"game_over": self.game_over, "winner": self.winner, "scores": self.get_scores()}

        # 處理電腦移動 (只有在人機模式且輪到電腦時)
        if self.vs_computer and self.current_player == 2 and not self.game_over:
            self.computer_move() # AI下棋

        # 處理玩家輸入 (人機模式下只有玩家1可以輸入，雙人模式下兩個玩家都可以輸入)
        if not (self.vs_computer and self.current_player == 2):
            # Initialize left stick parameters if not exists
            if not hasattr(self, 'stick_threshold'):
                self.stick_threshold = 0.7  # Higher threshold for precise cursor movement
                self.last_stick_direction = None
            
            moved_cursor = False
            action_taken = False # 用於區分移動和確認/切換模式等動作，確保輸入延遲正確應用

            if controller_input:
                # Handle Y button for mode switching (separate timing control)
                if controller_input.get("y_pressed"):
                    if current_time - self.last_input_time >= self.input_delay: # 使用標準延遲
                        # 在切換模式時，保留總分，僅重置棋盤和當前遊戲狀態
                        current_score_x = self.score_x
                        current_score_o = self.score_o
                        current_score_draw = self.score_draw
                        
                        self.vs_computer = not self.vs_computer
                        self.reset_game() # reset_game 會將 vs_computer 設為預設值 (現在是False)
                                          # 如果希望Y鍵切換後保持該模式，reset_game中vs_computer的賦值需要調整
                                          # 或者，在這裡手動設定回切換後的值
                        
                        # 恢復分數，因為 reset_game 會清零它們
                        self.score_x = current_score_x
                        self.score_o = current_score_o
                        self.score_draw = current_score_draw
                        
                        # 如果 reset_game 將 vs_computer 設為固定值 (如 False),
                        # Y鍵切換後需要再根據切換的意圖重新設置它。
                        # 更好的做法是 reset_game 不要動 vs_computer，或者傳參數
                        # 為了簡單，我們讓 Y 鍵切換後，reset_game 會重置為預設的雙人
                        # 如果按 Y 從雙人切到人機，則再手動設定
                        if not self.vs_computer: # 如果 reset_game 設為 False, 但我們是想切到 True
                             # 這裡的邏輯需要小心，因為 reset_game 會強制設為 False
                             # 假設 Y 的作用就是 toggle
                             # self.vs_computer = not self.vs_computer # 這一行已經做了toggle
                             # 所以 reset_game 之後，vs_computer 的值是 toggle 之後的
                             pass # reset_game 之後 vs_computer 的值是正確的 toggle 後的值 (如果 reset_game 不動它)

                        # 目前 reset_game 將 vs_computer 強制設為 False。
                        # 所以如果原先是 True, 按 Y, vs_computer 變成 False, reset_game 維持 False (正確)
                        # 如果原先是 False, 按 Y, vs_computer 變成 True, reset_game 又設回 False (錯誤)
                        # 因此，Y鍵切換邏輯需要調整
                        
                        # 正確的 Y 鍵切換邏輯 (假設 reset_game 不 건드리는 vs_computer)
                        # self.vs_computer = not self.vs_computer
                        # temp_vs_computer = self.vs_computer # 保存切換後狀態
                        # self.reset_game()
                        # self.vs_computer = temp_vs_computer # 恢復切換後狀態

                        # 考慮到 reset_game 將 vs_computer 設為 False（我們的修改）
                        # Y 鍵按下時：
                        # 1. 記錄當前分數
                        # 2. 切換 vs_computer 的狀態 ( toggle )
                        # 3. 調用 reset_game (它會將 vs_computer 設為 False, current_player=1 等)
                        # 4. 如果 toggle 後的目標是 True (人機), 則在 reset_game 後再把 vs_computer 設回 True
                        
                        target_vs_computer = not self.vs_computer # 這是按下Y後的目標狀態
                        self.reset_game() # 這會將 self.vs_computer 設為 False
                        self.vs_computer = target_vs_computer # 將其設為真正的目標狀態
                        
                        # 恢復分數 (因為 reset_game 會清零)
                        self.score_x = current_score_x
                        self.score_o = current_score_o
                        self.score_draw = current_score_draw
                        
                        action_taken = True
                        if self.buzzer: 
                            if self.vs_computer:
                                self.buzzer.play_tone(frequency=600, duration=0.2)  # 切換到人機模式
                            else:
                                self.buzzer.play_tone(frequency=800, duration=0.2)  # 切換到雙人模式
                        self.last_input_time = current_time

                # Handle Start button for game reset (separate timing control)
                # Start鍵應保留當前模式並重置遊戲，但保留總分
                if controller_input.get("start_pressed") and not action_taken: # 避免Y鍵後立即觸發
                    if current_time - self.last_input_time >= self.input_delay:
                        # 保留當前模式和總分
                        current_mode_vs_computer = self.vs_computer
                        current_score_x = self.score_x
                        current_score_o = self.score_o
                        current_score_draw = self.score_draw
                        
                        self.reset_game() # reset_game 會將 vs_computer 設為 False
                        self.vs_computer = current_mode_vs_computer # 恢復原模式
                        
                        self.score_x = current_score_x
                        self.score_o = current_score_o
                        self.score_draw = current_score_draw
                        
                        action_taken = True
                        if self.buzzer: self.buzzer.play_tone(frequency=300, duration=0.3)
                        self.last_input_time = current_time
                
                # Only proceed with movement/action if enough time has passed since last *specific* input type
                if not action_taken and (current_time - self.last_input_time >= self.input_delay):
                    # Left stick input processing
                    stick_x = controller_input.get("left_stick_x", 0.0)
                    stick_y = controller_input.get("left_stick_y", 0.0)
                    current_stick_direction = None
                    
                    if abs(stick_x) > self.stick_threshold or abs(stick_y) > self.stick_threshold:
                        if abs(stick_x) > abs(stick_y):
                            if stick_x > self.stick_threshold: current_stick_direction = "right"
                            elif stick_x < -self.stick_threshold: current_stick_direction = "left"
                        else:
                            if stick_y > self.stick_threshold: current_stick_direction = "down"
                            elif stick_y < -self.stick_threshold: current_stick_direction = "up"
                    
                    if current_stick_direction and current_stick_direction != self.last_stick_direction:
                        if current_stick_direction == "up" and self.cursor_row > 0: self.cursor_row -= 1; moved_cursor = True
                        elif current_stick_direction == "down" and self.cursor_row < 2: self.cursor_row += 1; moved_cursor = True
                        elif current_stick_direction == "left" and self.cursor_col > 0: self.cursor_col -= 1; moved_cursor = True
                        elif current_stick_direction == "right" and self.cursor_col < 2: self.cursor_col += 1; moved_cursor = True
                        
                        if moved_cursor:
                            self.last_input_time = current_time
                            if self.buzzer: self.buzzer.play_tone(frequency=250, duration=0.05)
                    self.last_stick_direction = current_stick_direction # Update regardless of movement for continuous check

                    # D-pad input (takes priority if stick didn't move cursor, or if stick not used)
                    if not moved_cursor: # Only process D-pad if stick didn't cause a move in this frame
                        dpad_moved = False
                        if controller_input.get("up_pressed") and self.cursor_row > 0: self.cursor_row -= 1; dpad_moved = True
                        elif controller_input.get("down_pressed") and self.cursor_row < 2: self.cursor_row += 1; dpad_moved = True
                        elif controller_input.get("left_pressed") and self.cursor_col > 0: self.cursor_col -= 1; dpad_moved = True
                        elif controller_input.get("right_pressed") and self.cursor_col < 2: self.cursor_col += 1; dpad_moved = True
                        
                        if dpad_moved:
                            moved_cursor = True # Mark that cursor moved for this update cycle
                            self.last_input_time = current_time
                            if self.buzzer: self.buzzer.play_tone(frequency=250, duration=0.05)

                    # Action button (A)
                    if controller_input.get("a_pressed"):
                        if self.make_move(self.cursor_row, self.cursor_col):
                            action_taken = True # Successful move is an action
                            self.last_input_time = current_time # Reset timer after successful action
                        else: # Invalid move
                            self.last_input_time = current_time # Reset timer even for invalid to prevent quick re-trigger
                
                # If only cursor moved (not a game action like place piece/reset/mode change), update last_input_time
                # This was handled inside move blocks. Redundant `if moved_cursor and not action_taken:` removed.

        return {"game_over": self.game_over, "winner": self.winner, "scores": self.get_scores()}

    def get_scores(self):
        """返回目前分數"""
        return {"X": self.score_x, "O": self.score_o, "Draw": self.score_draw}

    def render(self, screen):
        """渲染遊戲畫面"""
        screen.fill(self.BLACK) # 黑色背景

        # 繪製棋盤背景
        board_surface_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(screen, self.LIGHT_GRAY, board_surface_rect, border_radius=10) # 圓角棋盤

        # 繪製格線
        for i in range(1, 3):
            # 垂直線
            pygame.draw.line(screen, self.BLACK,
                             (self.board_x + i * self.grid_size, self.board_y),
                             (self.board_x + i * self.grid_size, self.board_y + self.board_size),
                             self.line_width)
            # 水平線
            pygame.draw.line(screen, self.BLACK,
                             (self.board_x, self.board_y + i * self.grid_size),
                             (self.board_x + self.board_size, self.board_y + i * self.grid_size),
                             self.line_width)

        # 繪製棋子 (X 和 O)
        for r in range(3):
            for c in range(3):
                if self.board[r][c] != 0:
                    center_x = self.board_x + c * self.grid_size + self.grid_size // 2
                    center_y = self.board_y + r * self.grid_size + self.grid_size // 2
                    
                    if self.board[r][c] == 1: # 繪製 X
                        size = self.grid_size // 3 # X 的大小
                        pygame.draw.line(screen, self.RED,
                                         (center_x - size, center_y - size),
                                         (center_x + size, center_y + size), self.piece_line_width)
                        pygame.draw.line(screen, self.RED,
                                         (center_x + size, center_y - size),
                                         (center_x - size, center_y + size), self.piece_line_width)
                    else: # 繪製 O
                        radius = self.grid_size // 3 # O 的半徑
                        pygame.draw.circle(screen, self.BLUE, (center_x, center_y), radius, self.piece_line_width)
        
        # 繪製獲勝線
        if self.winning_line_coords:
            start_pos, end_pos = self.winning_line_coords
            pygame.draw.line(screen, self.GREEN, start_pos, end_pos, self.line_width + 2) # 獲勝線加粗

        # 繪製游標 (在雙人模式下始終顯示，在人機模式下只有輪到玩家時顯示)
        if not self.game_over and (not self.vs_computer or self.current_player == 1):
            cursor_rect_x = self.board_x + self.cursor_col * self.grid_size
            cursor_rect_y = self.board_y + self.cursor_row * self.grid_size
            cursor_rect = pygame.Rect(cursor_rect_x, cursor_rect_y, self.grid_size, self.grid_size)
            pygame.draw.rect(screen, self.YELLOW, cursor_rect, self.line_width // 2) # 游標框線

        # 顯示遊戲資訊 (目前玩家、模式、分數)
        # 目前玩家
        if not self.game_over:
            player_turn_text = "WHO MOVE: "
            if self.current_player == 1:
                player_turn_text += "X"
                if self.vs_computer:
                    player_turn_text += " (YOU)"
                else:
                    player_turn_text += " (PLAYER1)"
                player_color = self.RED
            else: # current_player == 2
                player_turn_text += "O"
                if self.vs_computer:
                    player_turn_text += " (COM)"
                else:
                    player_turn_text += " (PLAYER2)"
                player_color = self.BLUE
            player_surf = self.font_medium.render(player_turn_text, True, player_color)
            screen.blit(player_surf, (20, 20))

        # 遊戲模式
        mode_text = "MODE: " + ("PLAYER vs COM" if self.vs_computer else "PLY vs PLY") # 修改點: PLY/PLY -> PLY vs PLY
        mode_surf = self.font_medium.render(mode_text, True, self.WHITE)
        screen.blit(mode_surf, (self.width - mode_surf.get_width() - 20, 20))

        # 分數顯示
        score_display_text = f"X: {self.score_x}   O: {self.score_o}   tie: {self.score_draw}" # 稍微增加空格
        score_surf = self.font_medium.render(score_display_text, True, self.WHITE)
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 20))

        # 操作提示
        hint_text_lines = [
            "JOYSTICK: MOVE",         # 修改點: JOYSTICL -> JOYSTICK
            "PRESS A: CONFIRM MOVE",
            "PRESS Y: CHANGE MODE", # 修改點: PREE -> PRESS, 移除多餘空格
            "PRESS START: RESET GAME",
        ]
        hint_y_start = self.height - 30 - (len(hint_text_lines) * (self.font_small.get_height() + 2))

        for i, line in enumerate(hint_text_lines):
            hint_surf = self.font_small.render(line, True, self.GRAY)
            screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, hint_y_start + i * (self.font_small.get_height() + 2)))

        # 遊戲結束畫面
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # 半透明黑色遮罩
            screen.blit(overlay, (0, 0))

            result_text = ""
            result_color = self.WHITE
            if self.winner == 0:
                result_text = "TIE!" # 改為大寫
                result_color = self.YELLOW
            elif self.winner == 1:
                result_text = "X WIN!"
                if not self.vs_computer:
                    result_text += " (PLAYER1)"
                result_color = self.RED
            elif self.winner == 2:
                result_text = "O WIN!"
                if self.vs_computer: 
                    result_text += " (COM)"
                else: 
                    result_text += " (PLAYER2)"
                result_color = self.BLUE
            
            result_surf = self.font_large.render(result_text, True, result_color)
            screen.blit(result_surf, (self.width // 2 - result_surf.get_width() // 2, self.height // 2 - 60))

            restart_surf = self.font_medium.render("PRESS START TO RESTART", True, self.WHITE)
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 20))

    def cleanup(self):
        """清理遊戲資源 (目前未使用)"""
        pass

# 若獨立執行此腳本，用於測試 (main 部分保持不變)
if __name__ == "__main__":
    try:
        pygame.init()
        if not pygame.font.get_init(): # 確保字型模組已初始化
            pygame.font.init()

        screen_width_main = 800
        screen_height_main = 600
        main_screen = pygame.display.set_mode((screen_width_main, screen_height_main))
        pygame.display.set_caption("井字遊戲測試 (增強版)")

        # 簡易 Buzzer 模擬
        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None, sound_name=None):
                if sound_name:
                    print(f"Buzzer 模擬: 播放 '{sound_name}'")
                elif frequency and duration:
                    print(f"Buzzer 模擬: 播放音調 freq={frequency}, dur={duration}")

        game_instance = TicTacToeGame(screen_width_main, screen_height_main, buzzer=MockBuzzer())
        
        # Track key states for proper input handling
        # (這部分在獨立測試時模擬控制器輸入，可以保持不變)
        keys_pressed = {
            "up": False, "down": False, "left": False, "right": False,
            "a": False, "y": False, "start": False
        }
        
        running = True
        while running:
            # 事件處理
            controller_input_map = {
                "up_pressed": False, "down_pressed": False, "left_pressed": False, "right_pressed": False,
                "a_pressed": False, "y_pressed": False, "start_pressed": False,
                "left_stick_x": 0.0, "left_stick_y": 0.0 # 確保測試時有這些鍵
            }
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Handle key press events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP: controller_input_map["up_pressed"] = True
                    if event.key == pygame.K_DOWN: controller_input_map["down_pressed"] = True
                    if event.key == pygame.K_LEFT: controller_input_map["left_pressed"] = True
                    if event.key == pygame.K_RIGHT: controller_input_map["right_pressed"] = True
                    if event.key == pygame.K_a: controller_input_map["a_pressed"] = True
                    if event.key == pygame.K_y: controller_input_map["y_pressed"] = True
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        controller_input_map["start_pressed"] = True
                # (KEYUP 事件處理可以簡化或移除，因為 update 函數現在處理的是單次觸發)
                # 為了模擬搖桿，我們這裡不處理 KEYUP，讓 controller_input_map 在每幀開始時重置

            # 模擬搖桿持續輸入 (如果需要測試搖桿邏輯)
            # pressed_keys_pygame = pygame.key.get_pressed()
            # if pressed_keys_pygame[pygame.K_LEFT]: controller_input_map["left_stick_x"] = -1.0
            # if pressed_keys_pygame[pygame.K_RIGHT]: controller_input_map["left_stick_x"] = 1.0
            # if pressed_keys_pygame[pygame.K_UP]: controller_input_map["left_stick_y"] = -1.0 # Pygame Y軸向下為正
            # if pressed_keys_pygame[pygame.K_DOWN]: controller_input_map["left_stick_y"] = 1.0

            # 更新遊戲狀態
            game_state = game_instance.update(controller_input_map)
            
            # 渲染遊戲畫面
            game_instance.render(main_screen)
            pygame.display.flip() # 更新顯示
            
            game_instance.clock.tick(game_instance.fps) # 控制幀率
            
        game_instance.cleanup()
        pygame.quit()
    except Exception as e_main:
        print(f"主程式執行錯誤: {e_main}")
        import traceback
        traceback.print_exc()
        pygame.quit()