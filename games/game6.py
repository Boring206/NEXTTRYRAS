#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game6.py - Simple Maze Game Implementation

import random
import pygame
import time
from pygame.locals import *

class SimpleMazeGame:
    """Simple Maze Game Class"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # Game area width
        self.height = height     # Game area height
        self.buzzer = buzzer     # Buzzer instance for audio feedback
        
        # Game element size
        self.block_size = 30     # Maze block size
        self.grid_width = self.width // self.block_size
        self.grid_height = self.height // self.block_size
        
        # Color definitions
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
        
        # Game speed settings
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Maze generation parameters
        self.min_maze_size = 15  # Minimum maze size
        self.max_maze_size = 20  # Maximum maze size
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Game state
        self.game_over = False
        self.paused = False
        self.level = 1
        self.moves = 0
        self.start_time = time.time()
        
        # Generate maze
        self.generate_maze()
        
        # Set player position at the entrance
        self.player_pos = self.entrance
        
        # For controlling input frequency
        self.last_input_time = time.time()
        self.input_delay = 0.15  # seconds
    
    def generate_maze(self):
        """Generate maze"""
        # Adjust maze size based on level
        size = min(self.min_maze_size + self.level - 1, self.max_maze_size)
        
        # Ensure maze size is odd for algorithm convenience
        if size % 2 == 0:
            size += 1
        
        self.maze_size = size
        
        # Initialize maze, 0 for wall, 1 for path
        self.maze = [[0 for _ in range(size)] for _ in range(size)]
        
        # Generate maze using Depth-First Search (DFS)
        self._generate_maze_dfs(1, 1)
        
        # Set entrance and exit
        self.entrance = (1, 0)  # Entrance at the top
        self.exit = (size - 2, size - 1)  # Exit at the bottom
        
        # Ensure entrance and exit are paths
        self.maze[0][1] = 1
        self.maze[size-1][size-2] = 1
    
    def _generate_maze_dfs(self, x, y):
        """Generate maze using Depth-First Search"""
        # Mark current position as path
        self.maze[y][x] = 1
        
        # Directions: up, right, down, left
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check if within bounds
            if 0 <= nx < self.maze_size and 0 <= ny < self.maze_size and self.maze[ny][nx] == 0:
                # Set the in-between cell as path
                self.maze[y + dy//2][x + dx//2] = 1
                
                # Recur to continue generating
                self._generate_maze_dfs(nx, ny)
    
    def is_valid_move(self, new_pos):
        """Check if the move is valid"""
        x, y = new_pos
        
        # Check if within maze bounds
        if not (0 <= y < self.maze_size and 0 <= x < self.maze_size):
            return True if new_pos == self.exit else False
        
        # Check if it's a wall
        return self.maze[y][x] == 1
    
    def update(self, controller_input=None):
        """
        Update game state
        
        Parameters:
            controller_input: Input dictionary from controller
        
        Returns:
            Dictionary containing game state
        """
        if self.game_over or self.paused:
            # Handle input in game over or paused state
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            
            return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
        
        # Handle player input
        current_time = time.time()
        if current_time - self.last_input_time < self.input_delay:
            # In input delay, don't process input
            return {"game_over": self.game_over, "level": self.level}
        
        # Handle input
        if controller_input:
            input_detected = False
            x, y = self.player_pos
            new_pos = (x, y)
            
            # Direction controls
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
            
            # Pause control
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                input_detected = True
                return {"game_over": self.game_over, "level": self.level, "paused": self.paused}
            
            # If input is detected, reset input delay timer
            if input_detected:
                self.last_input_time = current_time
                
                # Check if the move is valid
                if self.is_valid_move(new_pos):
                    old_pos = self.player_pos
                    self.player_pos = new_pos
                    self.moves += 1
                    
                    # Play move sound effect
                    if self.buzzer:
                        self.buzzer.play_tone("navigate")
                    
                    # Check if reached the exit
                    if self.player_pos == self.exit:
                        # Level up
                        self.level += 1
                        
                        # Play victory sound effect
                        if self.buzzer:
                            # Enhanced victory sound sequence
                            victory_notes = [523, 659, 784, 1047, 1319]  # C major scale ascending
                            for note in victory_notes:
                                self.buzzer.play_tone(frequency=note, duration=0.2)
                                time.sleep(0.1)
                        
                        # Generate new, more complex maze
                        self.generate_maze()
                        self.player_pos = self.entrance
                        
                        return {"game_over": False, "level_complete": True, "level": self.level}
                else:
                    # Play invalid move sound effect
                    if self.buzzer:
                        self.buzzer.play_tone("error")
        
        return {"game_over": self.game_over, "level": self.level}
    
    def render(self, screen):
        """
        Render game screen
        
        Parameters:
            screen: pygame screen object
        """
        # Clear screen
        screen.fill(self.BLACK)
        
        # Calculate starting position for maze drawing to center it
        cell_size = min(self.width // self.maze_size, self.height // self.maze_size)
        start_x = (self.width - self.maze_size * cell_size) // 2
        start_y = (self.height - self.maze_size * cell_size) // 2
        
        # Draw maze
        for y in range(self.maze_size):
            for x in range(self.maze_size):
                rect = pygame.Rect(
                    start_x + x * cell_size,
                    start_y + y * cell_size,
                    cell_size,
                    cell_size
                )
                
                # Draw wall or path
                if self.maze[y][x] == 0:
                    pygame.draw.rect(screen, self.WALL_COLOR, rect)
                else:
                    pygame.draw.rect(screen, self.PATH_COLOR, rect)
                    
                # Add grid line effect
                pygame.draw.rect(screen, self.BLACK, rect, 1)
        
        # Draw entrance and exit
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
        
        # Draw player
        player_rect = pygame.Rect(
            start_x + self.player_pos[0] * cell_size,
            start_y + self.player_pos[1] * cell_size,
            cell_size,
            cell_size
        )
        pygame.draw.rect(screen, self.PLAYER_COLOR, player_rect)
        
        # Draw game info
        font = pygame.font.Font(None, 36)
        
        # Level info
        level_text = font.render(f"Level: {self.level}", True, self.WHITE)
        screen.blit(level_text, (10, 10))
        
        # Move count
        moves_text = font.render(f"Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (10, 50))
        
        # Game time
        elapsed_time = int(time.time() - self.start_time)
        time_text = font.render(f"Time: {elapsed_time}s", True, self.WHITE)
        screen.blit(time_text, (10, 90))
        
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
        level_text = font.render(f"Level Reached: {self.level}", True, self.WHITE)
        screen.blit(level_text, (self.width // 2 - level_text.get_width() // 2, self.height // 2 + 10))
        
        moves_text = font.render(f"Total Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width // 2 - moves_text.get_width() // 2, self.height // 2 + 50))
        
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
        # Currently no special cleanup needed, but keep this method for future expansion
        pass

# If this script is run standalone, for testing
if __name__ == "__main__":
    try:
        # Initialize pygame
        pygame.init()
        
        # Setup window
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Simple Maze Game Test")
        
        # Create game instance
        game = SimpleMazeGame(screen_width, screen_height)
        
        # Simulate controller input key mapping
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_y: "y_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # Game main loop
        running = True
        clock = pygame.time.Clock()
        
        while running:
            # Handle events
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # Get current key states
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
            clock.tick(30)

    except Exception as e:
        print(f"Game execution error: {e}")
    finally:
        pygame.quit()
        print("Simple Maze Game test ended")
