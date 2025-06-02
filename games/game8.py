#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game8.py - Tetris-like Game Implementation

import random
import pygame
import time
from pygame.locals import *

class TetrisLikeGame:
    """Tetris-like Game Class"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # Game area width
        self.height = height     # Game area height
        self.buzzer = buzzer     # Buzzer instance for audio feedback
        
        # Game parameters
        self.grid_width = 10     # Game area width (in blocks)
        self.grid_height = 20    # Game area height (in blocks)
        self.block_size = min(width // 20, height // 22)
        
        # Game area position
        self.board_x = (width - self.grid_width * self.block_size) // 2
        self.board_y = height - self.grid_height * self.block_size - 20
        
        # Color definitions
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
        
        # Block colors
        self.BLOCK_COLORS = [
            self.RED,
            self.GREEN,
            self.BLUE,
            self.YELLOW,
            self.CYAN,
            self.MAGENTA,
            self.ORANGE
        ]
        
        # Block shapes (various arrangements)
        # Each shape is a 4x4 grid, where 1 indicates block exists, 0 indicates empty
        self.SHAPES = [
            # I shape
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # J shape
            [
                [1, 0, 0, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # L shape
            [
                [0, 0, 1, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # O shape
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # S shape
            [
                [0, 1, 1, 0],
                [1, 1, 0, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # T shape
            [
                [0, 1, 0, 0],
                [1, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            # Z shape
            [
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ]
        ]
        
        # Game speed related
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Game state
        self.game_over = False
        self.paused = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        
        # Game board (0 indicates empty, >0 indicates block color index)
        self.board = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Current falling block
        self.current_shape = None
        self.current_color = None
        self.current_x = 0
        self.current_y = 0
        self.current_rotation = 0
        
        # Generate first block
        self.generate_new_shape()
        
        # Drop time control
        self.last_drop_time = time.time()
        self.drop_interval = 1.0  # Initial drop interval (seconds)
        
        # Input control
        self.last_input_time = time.time()
        self.input_delay = 0.1  # seconds
        
        # Fast drop flag
        self.fast_drop = False
    
    def generate_new_shape(self):
        """Generate a new random block"""
        # Select random shape and color
        shape_idx = random.randint(0, len(self.SHAPES) - 1)
        self.current_shape = self.SHAPES[shape_idx]
        self.current_color = shape_idx + 1  # Color index starts from 1, 0 indicates empty
        
        # Set initial position (centered)
        self.current_x = self.grid_width // 2 - 2
        self.current_y = 0
        self.current_rotation = 0
        
        # Check if game is over (if new block overlaps with existing blocks)
        if self.is_collision():
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_game_over_melody()
    
    def rotate_shape(self, shape):
        """Rotate block (clockwise 90 degrees)"""
        # Transpose matrix
        transposed = [[shape[y][x] for y in range(4)] for x in range(4)]
        
        # Reverse each row (clockwise rotation)
        rotated = [row[::-1] for row in transposed]
        
        return rotated
    
    def is_collision(self):
        """Check if current block collides with boundaries or other blocks"""
        for y in range(4):
            for x in range(4):
                if self.current_shape[y][x] == 0:
                    continue
                    
                board_x = self.current_x + x
                board_y = self.current_y + y
                
                # Check if out of bounds
                if (board_x < 0 or board_x >= self.grid_width or
                    board_y < 0 or board_y >= self.grid_height):
                    return True
                
                # Check if overlaps with existing blocks
                if board_y >= 0 and self.board[board_y][board_x] > 0:
                    return True
                    
        return False
    
    def move_left(self):
        """Try to move current block left"""
        self.current_x -= 1
        if self.is_collision():
            self.current_x += 1
            return False
        
        if self.buzzer:
            self.buzzer.play_tone("navigate")
        return True
    
    def move_right(self):
        """Try to move current block right"""
        self.current_x += 1
        if self.is_collision():
            self.current_x -= 1
            return False
        
        if self.buzzer:
            self.buzzer.play_tone("navigate")
        return True
    
    def move_down(self):
        """Try to move current block down"""
        self.current_y += 1
        if self.is_collision():
            self.current_y -= 1
            self.lock_shape()
            return False
        return True
    
    def rotate(self):
        """Try to rotate current block"""
        original_shape = self.current_shape
        self.current_shape = self.rotate_shape(self.current_shape)
        
        # If collision after rotation, try left/right adjustment
        if self.is_collision():
            # Try moving left
            self.current_x -= 1
            if self.is_collision():
                # Try moving right
                self.current_x += 2
                if self.is_collision():
                    # If still can't rotate, restore original shape and position
                    self.current_x -= 1
                    self.current_shape = original_shape
                    return False
        
        if self.buzzer:
            self.buzzer.play_tone("select")
        return True
    
    def hard_drop(self):
        """Quick drop block to bottom"""
        while self.move_down():
            pass
        
        if self.buzzer:
            self.buzzer.play_tone("score")
    
    def lock_shape(self):
        """Lock current block to game board"""
        for y in range(4):
            for x in range(4):
                if self.current_shape[y][x] == 0:
                    continue
                
                board_y = self.current_y + y
                board_x = self.current_x + x
                
                # Ensure within game area
                if 0 <= board_y < self.grid_height and 0 <= board_x < self.grid_width:
                    self.board[board_y][board_x] = self.current_color
        
        # Check and clear full lines
        self.check_lines()
        
        # Generate new block
        self.generate_new_shape()
    
    def check_lines(self):
        """Check and clear full lines"""
        lines_to_clear = []
        
        # Check which lines are full
        for y in range(self.grid_height):
            if all(self.board[y][x] > 0 for x in range(self.grid_width)):
                lines_to_clear.append(y)
        
        # Clear lines
        for line in lines_to_clear:
            # Move upper lines down
            for y in range(line, 0, -1):
                self.board[y] = self.board[y - 1][:]
            
            # Set top line to empty
            self.board[0] = [0] * self.grid_width
        
        # Calculate score
        if lines_to_clear:
            # Base score: lines * 100 * level
            points = len(lines_to_clear) * 100 * self.level
            self.score += points
            
            # Increase cleared lines count
            self.lines_cleared += len(lines_to_clear)
            
            # Level up every 10 lines cleared
            if self.lines_cleared // 10 > (self.lines_cleared - len(lines_to_clear)) // 10:
                self.level_up()
            
            # Play line clear sound effect
            if self.buzzer:
                if len(lines_to_clear) >= 4:
                    self.buzzer.play_win_melody()  # Clear 4 lines at once (Tetris)
                else:
                    self.buzzer.play_tone("level_up")
    
    def level_up(self):
        """Level up, increase speed"""
        self.level += 1
        self.drop_interval = max(0.1, 1.0 - 0.05 * (self.level - 1))
        
        # Enhanced audio system
        if self.buzzer:
            # Play level up sound effect sequence
            frequencies = [523, 659, 784, 1047]  # C5, E5, G5, C6
            for freq in frequencies:
                self.buzzer.play_tone(frequency=freq, duration=0.15)
                time.sleep(0.05)
    
    def clear_lines(self, lines_to_clear):
        """Clear full lines with enhanced visual and audio effects"""
        if not lines_to_clear:
            return
        
        # Flash effect
        for flash in range(3):
            for row in lines_to_clear:
                for col in range(self.grid_width):
                    self.grid[row][col] = 9  # Special marker
            time.sleep(0.1)
            
            for row in lines_to_clear:
                for col in range(self.grid_width):
                    self.grid[row][col] = 0
            time.sleep(0.1)
        
        # Remove lines and add new lines
        for row in sorted(lines_to_clear, reverse=True):
            del self.grid[row]
            self.grid.insert(0, [0] * self.grid_width)
        
        # Update score and sound effects
        lines_count = len(lines_to_clear)
        base_score = [0, 100, 300, 500, 800][min(lines_count, 4)]
        self.score += base_score * self.level
        self.lines_cleared += lines_count
        
        # Audio feedback
        if self.buzzer:
            if lines_count == 4:  # Tetris
                self.buzzer.play_tetris_fanfare()
            elif lines_count >= 2:
                self.buzzer.play_multi_line_clear()
            else:
                self.buzzer.play_single_line_clear()
        
        # Level check
        if self.lines_cleared >= self.level * 10:
            self.level_up()

    def update(self, controller_input=None):
        """Update game state with enhanced input handling"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        current_time = time.time()
        
        # Handle input
        if controller_input:
            # Movement control (prevent too fast input)
            if current_time - self.last_input_time > 0.1:
                moved = False
                
                if controller_input.get("left_pressed"):
                    if self.move_left():
                        moved = True
                elif controller_input.get("right_pressed"):
                    if self.move_right():
                        moved = True
                elif controller_input.get("down_pressed"):
                    if self.move_down():
                        moved = True
                        self.score += 1  # Soft drop score
                
                if moved:
                    self.last_input_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=400, duration=0.05)
            
            # Rotation control
            if controller_input.get("up_pressed") and current_time - getattr(self, 'last_rotate_time', 0) > 0.2:
                if self.rotate():
                    self.last_rotate_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=600, duration=0.1)
            
            # Hard drop control
            if controller_input.get("a_pressed") and current_time - getattr(self, 'last_hard_drop_time', 0) > 0.3:
                self.hard_drop()
                self.last_hard_drop_time = current_time
            
            # Pause control
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        # Auto drop logic
        if current_time - self.last_drop_time >= self.drop_interval:
            if not self.move_down():
                self.check_lines()
            
            self.last_drop_time = current_time
        
        return {"game_over": self.game_over, "level": self.level, "score": self.score}
    
    def render(self, screen):
        """
        Render game screen
        
        Parameters:
            screen: pygame screen object
        """
        # Clear screen
        screen.fill(self.BLACK)
        
        # Draw game area border
        board_rect = pygame.Rect(
            self.board_x - 1,
            self.board_y - 1,
            self.grid_width * self.block_size + 2,
            self.grid_height * self.block_size + 2
        )
        pygame.draw.rect(screen, self.WHITE, board_rect, 2)
        
        # Draw locked blocks
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
        
        # Draw current falling block
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
        
        # Draw game info
        font = pygame.font.Font(None, 36)
        
        # Score
        score_text = font.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (20, 20))
        
        # Level
        level_text = font.render(f"Level: {self.level}", True, self.WHITE)
        screen.blit(level_text, (20, 60))
        
        # Lines cleared
        lines_text = font.render(f"Lines: {self.lines_cleared}", True, self.WHITE)
        screen.blit(lines_text, (20, 100))
        
        # Game over screen
        if self.game_over:
            self.draw_game_over(screen)
        
        # Pause screen
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """Draw game over screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("Game Over", True, self.RED)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Final Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 2 + 10))
        
        level_text = font.render(f"Level Reached: {self.level}", True, self.WHITE)
        screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, self.height // 2 + 50))
        
        restart_text = font.render("Press Start to Restart", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 90))
    
    def draw_pause(self, screen):
        """Draw pause screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("Paused", True, self.YELLOW)
        screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
        
        font = pygame.font.Font(None, 36)
        continue_text = font.render("Press Start to Continue", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 10))
    
    def cleanup(self):
        """Clean up game resources"""
        # Currently no special cleanup needed, but keeping this method for future expansion
        pass

# If running this script independently, used for testing
if __name__ == "__main__":
    try:
        # Initialize pygame
        pygame.init()
        
        # Setup window
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Tetris-like Game Test")
        
        # Create game instance
        game = TetrisLikeGame(screen_width, screen_height)
        
        # Simulate controller input keyboard mapping
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # Game main loop
        running = True
        while running:
            # Handle events
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # Get current pressed key states
            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True
            
            # Update game
            game.update(controller_input)
            
            # Render
            game.render(screen)
            pygame.display.flip()
            
            # Control frame rate
            pygame.time.Clock().tick(60)
        
        # Exit pygame
        pygame.quit()
    
    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()
