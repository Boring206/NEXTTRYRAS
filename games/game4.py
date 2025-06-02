#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game4.py - Tic Tac Toe Game Implementation

import random
import pygame
import time
from pygame.locals import *

class TicTacToeGame:
    """Tic Tac Toe Game Class"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # Game area width
        self.height = height     # Game area height
        self.buzzer = buzzer     # Buzzer instance for audio feedback
        
        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        
        # Game element sizes
        self.board_size = min(width, height) - 100
        self.grid_size = self.board_size // 3
        self.board_x = (width - self.board_size) // 2
        self.board_y = (height - self.board_size) // 2
        self.line_width = 5
        
        # Game speed settings
        self.clock = pygame.time.Clock()
        self.fps = 30
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Game board (3x3), 0=empty, 1=X, 2=O
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # Cursor position
        self.cursor_x = 1
        self.cursor_y = 1
        
        # Current player (1=X, 2=O)
        self.current_player = 1
        
        # Game state
        self.game_over = False
        self.paused = False
        self.winner = 0  # 0=draw, 1=X wins, 2=O wins
        
        # Last input time (for input frequency control)
        self.last_input_time = time.time()
        self.input_delay = 0.2  # seconds
        
        # Computer player
        self.vs_computer = True
        self.computer_delay = 1.0  # Computer decision delay (seconds)
        self.computer_last_move = time.time()
    
    def make_move(self, x, y):
        """Make a game move"""
        # If the cell is already occupied, do nothing
        if self.board[y][x] != 0:
            return False
        
        # Place the piece
        self.board[y][x] = self.current_player
        
        # Play sound effect
        if self.buzzer:
            self.buzzer.play_tone(frequency=600, duration=0.2)
        
        # Check if the game is over
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
            # Switch player
            self.current_player = 2 if self.current_player == 1 else 1
        
        return True
    
    def check_win(self):
        """Check if there is a winner"""
        player = self.current_player
        
        # Check rows
        for y in range(3):
            if all(self.board[y][x] == player for x in range(3)):
                return True
        
        # Check columns
        for x in range(3):
            if all(self.board[y][x] == player for y in range(3)):
                return True
        
        # Check diagonals
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True
        
        return False
    
    def check_draw(self):
        """Check if the game is a draw"""
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    return False
        return True
    
    def computer_move(self):
        """Computer player makes a move"""
        # Check if it's the computer's turn
        if not self.vs_computer or self.current_player != 2:
            return False
        
        current_time = time.time()
        if current_time - self.computer_last_move < self.computer_delay:
            return False
        
        self.computer_last_move = current_time
        
        # Check if the computer can win
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    self.board[y][x] = 2
                    if self.check_win_for_player(2):
                        self.board[y][x] = 0
                        return self.make_move(x, y)
                    self.board[y][x] = 0
        
        # Check if the computer needs to block the opponent
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    self.board[y][x] = 1
                    if self.check_win_for_player(1):
                        self.board[y][x] = 0
                        return self.make_move(x, y)
                    self.board[y][x] = 0
        
        # Try to take the center
        if self.board[1][1] == 0:
            return self.make_move(1, 1)
        
        # Random move
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
        """Check if the specified player has won"""
        # Check rows
        for y in range(3):
            if all(self.board[y][x] == player for x in range(3)):
                return True
        
        # Check columns
        for x in range(3):
            if all(self.board[y][x] == player for y in range(3)):
                return True
        
        # Check diagonals
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True
        
        return False
    
    def update(self, controller_input=None):
        """Update game state"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "winner": self.winner}
        
        # Handle computer move
        if self.vs_computer and self.current_player == 2:
            self.computer_move()
        
        # Handle player input
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
        """Render game screen"""
        # Clear the screen
        screen.fill(self.BLACK)
        
        # Draw game board background
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_size, self.board_size)
        pygame.draw.rect(screen, self.WHITE, board_rect)
        
        # Draw grid lines
        for i in range(1, 3):
            # Vertical lines
            start_pos = (self.board_x + i * self.grid_size, self.board_y)
            end_pos = (self.board_x + i * self.grid_size, self.board_y + self.board_size)
            pygame.draw.line(screen, self.BLACK, start_pos, end_pos, self.line_width)
            
            # Horizontal lines
            start_pos = (self.board_x, self.board_y + i * self.grid_size)
            end_pos = (self.board_x + self.board_size, self.board_y + i * self.grid_size)
            pygame.draw.line(screen, self.BLACK, start_pos, end_pos, self.line_width)
        
        # Draw pieces
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
        
        # Draw cursor
        if not self.game_over and not self.paused and (not self.vs_computer or self.current_player == 1):
            cursor_x = self.board_x + self.cursor_x * self.grid_size
            cursor_y = self.board_y + self.cursor_y * self.grid_size
            cursor_rect = pygame.Rect(cursor_x, cursor_y, self.grid_size, self.grid_size)
            pygame.draw.rect(screen, self.YELLOW, cursor_rect, 5)
        
        # Draw game info
        font = pygame.font.Font(None, 36)
        
        # Show current player
        if not self.game_over and not self.paused:
            player_text = f"Current Player: {'X (You)' if self.current_player == 1 else 'O (Computer)' if self.vs_computer else 'O (Player 2)'}"
            player_surface = font.render(player_text, True, self.WHITE)
            screen.blit(player_surface, (20, 20))
        
        # Show game mode
        mode_text = "Mode: " + ("VS Computer" if self.vs_computer else "Two Players")
        mode_surface = font.render(mode_text, True, self.WHITE)
        screen.blit(mode_surface, (self.width - mode_surface.get_width() - 20, 20))
        
        # Show control hints
        hint_text = "Press Y to toggle mode, A to select, arrows to move"
        hint_surface = font.render(hint_text, True, self.GRAY)
        screen.blit(hint_surface, (self.width // 2 - hint_surface.get_width() // 2, self.height - 40))
        
        # Game over screen
        if self.game_over:
            self.draw_game_over(screen)
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """Draw game over screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        
        if self.winner == 0:
            result_text = "Draw!"
            color = self.YELLOW
        else:
            if self.winner == 1:
                result_text = "X Wins!"
                color = self.RED
            else:
                result_text = "O Wins!" + (" (Computer wins)" if self.vs_computer else " (Player 2 wins)")
                color = self.BLUE
        
        text = font.render(result_text, True, color)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        restart_text = font.render("Press Start to Restart", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 20))
    
    def draw_pause(self, screen):
        """Draw pause screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("Paused", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))

    
    def cleanup(self):
        """清理遊戲資源"""
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Tic Tac Toe Game Test")
        
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
        print(f"Game execution error: {e}")
        pygame.quit()
