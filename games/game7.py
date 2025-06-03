#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game7.py - Whac-A-Mole Game Implementation

import random
import pygame
import time
from pygame.locals import *

class WhacAMoleGame:
    """Whac-A-Mole Game Class"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # Game area width
        self.height = height     # Game area height
        self.buzzer = buzzer     # Buzzer instance for audio feedback
        
        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.BROWN = (165, 42, 42)
        self.LIGHT_BROWN = (222, 184, 135)
        
        # Game parameters
        self.grid_size = 3       # 3x3 grid
        self.hole_radius = 50    # Hole radius
        self.mole_radius = 40    # Mole radius
        self.hammer_size = 70    # Hammer size
        
        # Calculate grid positions
        self.calculate_grid()
        
        # Game speed related
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Initialize game state
        self.reset_game()
        
        # Load resources
        self.load_resources()
    
    def load_resources(self):
        """Load game resources, such as images, sounds, etc."""
        # Here you can load images for moles, hammers, etc.
        # But in this version, we use simple geometric shapes for drawing
        pass
    
    def calculate_grid(self):
        """Calculate grid positions"""
        self.grid_positions = []
        
        # Calculate margins
        margin_x = self.width // 6
        margin_y = self.height // 6
        
        # Calculate spacing
        spacing_x = (self.width - 2 * margin_x) // (self.grid_size - 1)
        spacing_y = (self.height - 2 * margin_y) // (self.grid_size - 1)
        
        # Generate grid coordinates
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                pos_x = margin_x + x * spacing_x
                pos_y = margin_y + y * spacing_y
                self.grid_positions.append((pos_x, pos_y))
    
    def reset_game(self):
        """Reset game state"""
        # Game state
        self.game_over = False
        self.paused = False
        self.score = 0
        self.misses = 0
        self.time_left = 60  # 60 seconds game time
        self.start_time = time.time()
        
        # Mole state
        self.moles = [False] * (self.grid_size * self.grid_size)  # Whether the mole appears
        self.mole_timers = [0] * (self.grid_size * self.grid_size)  # Mole display time
        
        # Hammer position (initially in the center)
        self.hammer_pos = (self.width // 2, self.height // 2)
        self.hammer_idx = (self.grid_size * self.grid_size) // 2  # Center position index
        self.hammer_active = False  # Is the hammer currently hitting?
        self.hammer_angle = 0  # Hammer rotation angle
        
        # Difficulty parameters
        self.mole_show_time_min = 1.0  # Minimum display time
        self.mole_show_time_max = 2.5  # Maximum display time
        self.mole_spawn_interval = 1.0  # Spawn interval
        self.last_spawn_time = time.time()
        
        # For controlling input frequency
        self.last_input_time = time.time()
        self.input_delay = 0.2  # seconds
        
        # Combo system
        self.combo = 0
        self.last_hit_time = 0
        self.hits = 0
    
    def spawn_mole(self):
        """Randomly spawn a mole"""
        # Find all holes without moles
        empty_holes = [i for i, mole in enumerate(self.moles) if not mole]
        
        if empty_holes:
            # Randomly select a hole
            hole_idx = random.choice(empty_holes)
            
            # Mole appears
            self.moles[hole_idx] = True
            
            # Set display time
            show_time = random.uniform(self.mole_show_time_min, self.mole_show_time_max)
            self.mole_timers[hole_idx] = show_time
    
    def update_moles(self, delta_time):
        """Update mole states"""
        for i in range(len(self.moles)):
            if self.moles[i]:
                # Decrease display time
                self.mole_timers[i] -= delta_time
                
                # If time's up, mole disappears
                if self.mole_timers[i] <= 0:
                    self.moles[i] = False
                    self.misses += 1  # Not hitting counts as a miss
                    
                    # Enhanced audio feedback
                    if self.buzzer:
                        # Mole escape sound
                        self.buzzer.play_tone(frequency=200, duration=0.3)
    
    def hit_mole(self, position_idx):
        """Hit the mole, enhance feedback effect"""
        if 0 <= position_idx < len(self.moles) and self.moles[position_idx]:
            self.moles[position_idx] = False
            self.score += 10
            self.hits += 1
            
            # Combo system
            current_time = time.time()
            if current_time - self.last_hit_time < 1.0:  # Combo within 1 second
                self.combo += 1
                combo_bonus = self.combo * 5
                self.score += combo_bonus
            else:
                self.combo = 1
            
            self.last_hit_time = current_time
            
            # Enhanced audio feedback
            if self.buzzer:
                if self.combo > 5:
                    # High combo sound
                    self.buzzer.play_tone(frequency=1200, duration=0.2)
                elif self.combo > 3:
                    # Medium combo sound
                    self.buzzer.play_tone(frequency=1000, duration=0.2)
                else:
                    # Normal hit sound
                    base_freq = 800 + (self.combo * 50)
                    self.buzzer.play_tone(frequency=base_freq, duration=0.15)
            
            return True
        return False
    
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
            
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # Update game time
        current_time = time.time()
        delta_time = current_time - self.start_time
        self.time_left = max(0, 60 - int(delta_time))
        
        # Time's up, game over
        if self.time_left <= 0:
            self.game_over = True
            
            # Play game over sound
            if self.buzzer:
                self.buzzer.play_tone(frequency=200, duration=0.5)
            
            return {"game_over": True, "score": self.score}
        
        # Spawn new mole
        if current_time - self.last_spawn_time >= self.mole_spawn_interval:
            self.spawn_mole()
            self.last_spawn_time = current_time
        
        # Update mole states
        self.update_moles(current_time - self.last_input_time)
        self.last_input_time = current_time
        
        # Hammer animation
        if self.hammer_active:
            self.hammer_angle += 15
            if self.hammer_angle >= 60:
                self.hammer_active = False
                self.hammer_angle = 0
        
        # Handle player input
        if controller_input and current_time - self.last_input_time >= self.input_delay:
            # Initialize left stick parameters if not exists
            if not hasattr(self, 'stick_threshold'):
                self.stick_threshold = 0.7
                self.last_stick_direction = None
            
            input_detected = False
            
            # Left stick input processing (single-trigger movement)
            stick_x = controller_input.get("left_stick_x", 0.0)
            stick_y = controller_input.get("left_stick_y", 0.0)
            stick_direction = None
            
            if abs(stick_x) > self.stick_threshold or abs(stick_y) > self.stick_threshold:
                if abs(stick_x) > abs(stick_y):
                    if stick_x > self.stick_threshold:
                        stick_direction = "right"
                    elif stick_x < -self.stick_threshold:
                        stick_direction = "left"
                else:
                    if stick_y > self.stick_threshold:
                        stick_direction = "down"
                    elif stick_y < -self.stick_threshold:
                        stick_direction = "up"
            
            # Apply stick movement (single-trigger with delay)
            if stick_direction and stick_direction != self.last_stick_direction:
                if stick_direction == "up":
                    self.hammer_idx = max(0, self.hammer_idx - self.grid_size)
                    input_detected = True
                elif stick_direction == "down":
                    self.hammer_idx = min(len(self.grid_positions) - 1, self.hammer_idx + self.grid_size)
                    input_detected = True
                elif stick_direction == "left":
                    if self.hammer_idx % self.grid_size > 0:
                        self.hammer_idx -= 1
                    input_detected = True
                elif stick_direction == "right":
                    if self.hammer_idx % self.grid_size < self.grid_size - 1:
                        self.hammer_idx += 1
                    input_detected = True
                self.last_stick_direction = stick_direction
            elif not stick_direction:
                self.last_stick_direction = None
            
            # D-pad input (preserve original logic, takes priority)
            if controller_input.get("up_pressed"):
                self.hammer_idx = max(0, self.hammer_idx - self.grid_size)
                input_detected = True
            elif controller_input.get("down_pressed"):
                self.hammer_idx = min(len(self.grid_positions) - 1, self.hammer_idx + self.grid_size)
                input_detected = True
            
            if controller_input.get("left_pressed"):
                if self.hammer_idx % self.grid_size > 0:
                    self.hammer_idx -= 1
                input_detected = True
            elif controller_input.get("right_pressed"):
                if self.hammer_idx % self.grid_size < self.grid_size - 1:
                    self.hammer_idx += 1
                input_detected = True
            
            # Update hammer position
            if 0 <= self.hammer_idx < len(self.grid_positions):
                self.hammer_pos = self.grid_positions[self.hammer_idx]
            
            # Hit control
            if controller_input.get("a_pressed") and not self.hammer_active:
                self.hammer_active = True
                self.hammer_angle = 0
                self.hit_mole(self.hammer_idx)
                input_detected = True
            
            # Pause control
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                input_detected = True
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
            
            # If input is detected, play sound and update input timing
            if input_detected:
                self.last_input_time = current_time
                if self.buzzer and not controller_input.get("a_pressed"):
                    self.buzzer.play_tone(frequency=300, duration=0.05)
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        Render game screen
        
        Parameters:
            screen: pygame screen object
        """
        # Clear screen
        screen.fill(self.BLACK)
        
        # Draw background (grass)
        pygame.draw.rect(screen, (34, 139, 34), (0, 0, self.width, self.height))
        
        # Draw holes and moles
        for i, (x, y) in enumerate(self.grid_positions):
            # Draw hole
            pygame.draw.circle(screen, self.BROWN, (x, y), self.hole_radius)
            pygame.draw.circle(screen, self.BLACK, (x, y), self.hole_radius - 5)
            
            # If there is a mole, draw the mole
            if self.moles[i]:
                pygame.draw.circle(screen, self.LIGHT_BROWN, (x, y - 15), self.mole_radius)
                
                # Draw mole's eyes
                pygame.draw.circle(screen, self.BLACK, (x - 15, y - 25), 5)
                pygame.draw.circle(screen, self.BLACK, (x + 15, y - 25), 5)
                
                # Draw mole's nose and mouth
                pygame.draw.circle(screen, self.BLACK, (x, y - 15), 5)
                pygame.draw.arc(screen, self.BLACK, (x - 20, y - 15, 40, 20), 0, 3.14, 2)
        
        # Draw hammer
        hammer_center = self.hammer_pos
        # Draw hammer head
        hammer_head_points = [
            (hammer_center[0] - 20, hammer_center[1] - 60 + self.hammer_angle),
            (hammer_center[0] + 20, hammer_center[1] - 60 + self.hammer_angle),
            (hammer_center[0] + 20, hammer_center[1] - 30 + self.hammer_angle),
            (hammer_center[0] - 20, hammer_center[1] - 30 + self.hammer_angle)
        ]
        pygame.draw.polygon(screen, (150, 75, 0), hammer_head_points)
        # Draw hammer handle
        pygame.draw.line(screen, (101, 67, 33), 
                         (hammer_center[0], hammer_center[1] - 30 + self.hammer_angle),
                         (hammer_center[0], hammer_center[1] + 30),
                         5)
        
        # Draw game info
        font = pygame.font.Font(None, 36)
        
        # Score
        score_text = font.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (10, 10))
        
        # Misses
        misses_text = font.render(f"Misses: {self.misses}", True, self.WHITE)
        screen.blit(misses_text, (10, 50))
        
        # Time left
        time_text = font.render(f"Time: {self.time_left}", True, self.WHITE)
        screen.blit(time_text, (self.width - 150, 10))
        
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
        
        miss_text = font.render(f"Total Misses: {self.misses}", True, self.WHITE)
        screen.blit(miss_text, (self.width // 2 - miss_text.get_width() // 2, self.height // 2 + 50))
        
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
        # Currently no special cleanup is required, but this method is kept for future expansion
        pass

# If this script is run independently, for testing
if __name__ == "__main__":
    try:
        # Initialize pygame
        pygame.init()
        
        # Set up window
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Whac-A-Mole Game Test")
        
        # Simple Buzzer simulation (for testing, actual should pass in real Buzzer object)
        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None):
                print(f"Buzzer: freq={frequency}, dur={duration}")
        
        # Create game instance
        game = WhacAMoleGame(screen_width, screen_height, buzzer=MockBuzzer())
        
        # Simulate controller input key mapping
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
        last_time = time.time()
        
        while running:
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            # Handle events
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
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
            pygame.time.Clock().tick(60)
        
        # Quit pygame
        pygame.quit()
    
    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()
