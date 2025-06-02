#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filepath: d:\User\Desktop\SensorGAME\gamebox\games\game2.py # Original path comment
# game2.py - Brick Breaker Game Implementation

import random
import pygame
import time
import math
import os # Keep os for potential future use, though font paths are simplified
from pygame.locals import *

class BrickBreakerGame:
    """Brick Breaker Game Class"""

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width       # Game area width
        self.height = height     # Game area height
        self.buzzer = buzzer     # Buzzer instance for sound feedback

        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (255, 0, 255) # Not used, but kept for consistency
        self.CYAN = (0, 255, 255)   # Not used
        self.ORANGE = (255, 165, 0)
        self.GRAY = (100, 100, 100) # For multi-hit bricks

        # Game speed related
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Ball and paddle initial parameters
        self.paddle_width = 100
        self.paddle_height = 15
        self.ball_radius = 8 # Slightly smaller ball for better visuals with bricks
        self.initial_ball_speed = 5
        self.ball_speed = self.initial_ball_speed
        self.max_ball_speed = 10 # Max speed for the ball

        # Brick parameters
        self.brick_width = (self.width - 100 - (9*2)) // 10 # Adjusted for 10 cols, 50px margins, 2px gap
        self.brick_height = 20
        self.brick_rows = 5
        self.brick_cols = 10
        self.brick_gap = 2

        # Sound timing
        self.last_paddle_hit_time = 0
        self.last_brick_hit_time = 0
        self.last_wall_hit_time = 0

        # Initialize font
        self.init_font()

        # Initialize game state
        self.reset_game()

    def init_font(self):
        """Initialize font (simplified for English version)."""
        try:
            self.font = pygame.font.Font(None, 36) # Use Pygame's default font
            print("Successfully loaded default font.")
        except Exception as e:
            print(f"Failed to load default font, error: {e}")
            try:
                # Fallback to a common system font if default fails
                self.font = pygame.font.SysFont("arial", 30) 
                print("Using system Arial font as fallback.")
            except Exception as e_sys:
                print(f"Failed to load system Arial font: {e_sys}. Text might not render.")
                # If all fails, text rendering will be problematic.
                # Pygame usually can find some font with None.
                self.font = None # Indicate font loading failure


    def reset_game(self):
        """Reset game state"""
        # Paddle initial position
        self.paddle_x = (self.width - self.paddle_width) // 2
        self.paddle_y = self.height - 40

        # Ball initial position and speed
        self.ball_x = self.width // 2
        self.ball_y = self.paddle_y - self.ball_radius -1 # Start on top of paddle
        self.ball_speed = self.initial_ball_speed # Reset ball speed
        
        # Initial ball direction: random angle upwards
        angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25) # Upwards, between -135 and -45 deg
        self.ball_dx = self.ball_speed * math.cos(angle)
        self.ball_dy = self.ball_speed * math.sin(angle)


        # Game state
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.paused = False
        self.ball_launched = False  # Has the ball been launched?

        # Create bricks
        self.create_bricks()

    def handle_ball_paddle_collision(self):
        """Handle ball-paddle collision with improved bounce angle and sound."""
        current_time = time.time()

        # Calculate where the ball hit the paddle: -1 (left edge) to +1 (right edge)
        offset = (self.ball_x - (self.paddle_x + self.paddle_width / 2)) / (self.paddle_width / 2)
        offset = max(-1.0, min(1.0, offset))  # Clamp value between -1 and 1

        # Max bounce angle (e.g., 75 degrees or 5*pi/12 radians from vertical)
        # A smaller angle range makes it easier to control
        max_bounce_angle_rad = math.pi * (5/12) 
        bounce_angle_rad = offset * max_bounce_angle_rad # Angle relative to vertical (0 is straight up)

        # New direction based on angle, preserving current ball_speed
        self.ball_dx = self.ball_speed * math.sin(bounce_angle_rad)
        self.ball_dy = -self.ball_speed * math.cos(bounce_angle_rad)  # Negative for upward movement

        # Sound feedback
        if self.buzzer and current_time - self.last_paddle_hit_time > 0.05: # Reduced delay
            base_freq = 400
            # Frequency variation based on hit position (-100 to +100 Hz)
            freq_variation = int(offset * 100) 
            self.buzzer.play_tone(frequency=base_freq + freq_variation, duration=0.08) # Shorter duration
            self.last_paddle_hit_time = current_time
            
        # Prevent ball from getting stuck in paddle by moving it slightly above
        self.ball_y = self.paddle_y - self.ball_radius - 0.1


    def handle_ball_brick_collision(self, brick_type, brick_color_tuple):
        """Handle ball-brick collision, for score and sound."""
        current_time = time.time()

        # Score based on brick type (original color)
        score_values = {
            'red': 50, 'orange': 40, 'yellow': 30,
            'green': 20, 'blue': 10, 'gray': 15 # Score for multi-hit bricks
        }
        self.score += score_values.get(brick_type, 10) # Default 10 points

        # Sound feedback
        if self.buzzer and current_time - self.last_brick_hit_time > 0.05:
            freq_map = { # Frequency map based on original color type
                'red': 1000, 'orange': 900, 'yellow': 800,
                'green': 700, 'blue': 600, 'gray': 750
            }
            frequency = freq_map.get(brick_type, 500) # Default frequency
            self.buzzer.play_tone(frequency=frequency, duration=0.08)
            self.last_brick_hit_time = current_time

    def create_bricks(self):
        """Create bricks with color layers and varying hits."""
        self.bricks = []
        # Define original colors and types for scoring and multi-hit logic
        # Tuples: (Pygame Color, String Type, Hits)
        brick_definitions = [
            (self.RED, 'red', 3),       # Top row, 3 hits
            (self.ORANGE, 'orange', 2), # Second row, 2 hits
            (self.YELLOW, 'yellow', 1), # Third row, 1 hit
            (self.GREEN, 'green', 1),   # Fourth row, 1 hit
            (self.BLUE, 'blue', 1)      # Fifth row, 1 hit
        ]

        # Calculate brick width to fit self.brick_cols across the screen
        # (width - left_margin - right_margin - (cols-1)*gap) / cols
        total_gap_width = (self.brick_cols - 1) * self.brick_gap
        available_width_for_bricks = self.width - 100 # 50px margin on each side
        self.brick_width = (available_width_for_bricks - total_gap_width) / self.brick_cols


        for row in range(self.brick_rows):
            brick_color, brick_type, brick_hits = brick_definitions[row % len(brick_definitions)]
            for col in range(self.brick_cols):
                brick_x = 50 + col * (self.brick_width + self.brick_gap) # Start 50px from left
                brick_y = 50 + row * (self.brick_height + self.brick_gap) # Start 50px from top

                brick = {
                    'x': brick_x, 'y': brick_y,
                    'width': self.brick_width, 'height': self.brick_height,
                    'rect': pygame.Rect(brick_x, brick_y, self.brick_width, self.brick_height),
                    'original_color_tuple': brick_color, # Store original for reference
                    'current_color_tuple': brick_color,  # This will change on hit
                    'type': brick_type,         # For scoring/sound logic
                    'active': True,
                    'total_hits': brick_hits,   # Total hits required
                    'remaining_hits': brick_hits # Current hits remaining
                }
                self.bricks.append(brick)

    def update(self, controller_input=None):
        """
        Update game state.
        Args: controller_input: Dictionary of controller inputs.
        Returns: Dictionary containing game state.
        """
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                # Debounce start press
                if not hasattr(self, 'start_handled_time') or time.time() - self.start_handled_time > 0.5:
                    if self.game_over:
                        self.reset_game()
                    else: # Paused
                        self.paused = False
                    self.start_handled_time = time.time()
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}

        # Handle input
        if controller_input:
            paddle_move_speed = 12 # Increased paddle speed
            if controller_input.get("left_pressed"):
                self.paddle_x = max(0, self.paddle_x - paddle_move_speed)
            if controller_input.get("right_pressed"):
                self.paddle_x = min(self.width - self.paddle_width, self.paddle_x + paddle_move_speed)

            if not self.ball_launched and controller_input.get("a_pressed"):
                self.ball_launched = True
                if self.buzzer: self.buzzer.play_tone(frequency=600, duration=0.1) # "select" sound

            if controller_input.get("start_pressed"):
                if not hasattr(self, 'start_handled_time') or time.time() - self.start_handled_time > 0.5:
                    self.paused = not self.paused
                    self.start_handled_time = time.time()
                    if self.buzzer: self.buzzer.play_tone(frequency=500, duration=0.1)
                    return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        if not self.ball_launched:
            self.ball_x = self.paddle_x + self.paddle_width // 2
            self.ball_y = self.paddle_y - self.ball_radius - 1 # Ball sits on paddle
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}

        # Store previous ball position for more accurate collision detection
        ball_prev_x = self.ball_x
        ball_prev_y = self.ball_y

        # Move ball
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Wall collision
        current_time = time.time() # For sound timing
        wall_hit_sound_delay = 0.1
        if self.ball_x <= self.ball_radius:
            self.ball_x = self.ball_radius
            self.ball_dx = -self.ball_dx
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05) # "navigate" sound
                self.last_wall_hit_time = current_time
        elif self.ball_x >= self.width - self.ball_radius:
            self.ball_x = self.width - self.ball_radius
            self.ball_dx = -self.ball_dx
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05)
                self.last_wall_hit_time = current_time
        
        if self.ball_y <= self.ball_radius:
            self.ball_y = self.ball_radius
            self.ball_dy = -self.ball_dy
            if self.buzzer and current_time - self.last_wall_hit_time > wall_hit_sound_delay:
                self.buzzer.play_tone(frequency=250, duration=0.05)
                self.last_wall_hit_time = current_time

        # Ball missed (goes below paddle)
        if self.ball_y >= self.height - self.ball_radius: # Check against bottom edge
            self.lives -= 1
            if self.buzzer: self.buzzer.play_tone(frequency=150, duration=0.5) # "error" sound
            
            if self.lives <= 0:
                self.game_over = True
                if self.buzzer: self.buzzer.play_tone(frequency=100, duration=1.0) # "game_over" sound
            else: # Reset ball if lives remaining
                self.ball_launched = False
                # self.ball_x = self.paddle_x + self.paddle_width // 2 # Set by !ball_launched block
                # self.ball_y = self.paddle_y - self.ball_radius - 1
                angle = random.uniform(-math.pi * 0.75, -math.pi * 0.25)
                self.ball_dx = self.ball_speed * math.cos(angle)
                self.ball_dy = self.ball_speed * math.sin(angle)
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}


        # Ball-paddle collision
        paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        # Approximate ball as a rect for initial collision check
        ball_rect = pygame.Rect(self.ball_x - self.ball_radius, self.ball_y - self.ball_radius,
                                self.ball_radius * 2, self.ball_radius * 2)

        if ball_rect.colliderect(paddle_rect) and self.ball_dy > 0: # Moving downwards
            self.handle_ball_paddle_collision()

        # Ball-brick collision
        for brick in self.bricks[:]: # Iterate over a copy for safe removal
            if not brick['active']: continue

            if ball_rect.colliderect(brick['rect']):
                brick['remaining_hits'] -= 1
                self.handle_ball_brick_collision(brick['type'], brick['original_color_tuple']) # Pass original color for consistent sound/score

                if brick['remaining_hits'] <= 0:
                    brick['active'] = False # Mark for removal or visual change
                    self.bricks.remove(brick) # Remove immediately
                else:
                    # Change color for multi-hit bricks (e.g., make it a shade of gray or lighter)
                    # Example: Blend with gray based on remaining hits
                    hit_ratio = brick['remaining_hits'] / brick['total_hits']
                    r = int(brick['original_color_tuple'][0] * hit_ratio + self.GRAY[0] * (1 - hit_ratio))
                    g = int(brick['original_color_tuple'][1] * hit_ratio + self.GRAY[1] * (1 - hit_ratio))
                    b = int(brick['original_color_tuple'][2] * hit_ratio + self.GRAY[2] * (1 - hit_ratio))
                    brick['current_color_tuple'] = (r,g,b)


                # --- Improved Bounce Logic for Bricks ---
                # Calculate overlap. If the ball was already overlapping, this simple check might not be enough.
                # A more robust way is to check the ball's previous position.
                
                # Determine collision side
                # Horizontal overlap amount with the brick
                overlap_left = (ball_prev_x + self.ball_radius) - brick['rect'].left
                overlap_right = brick['rect'].right - (ball_prev_x - self.ball_radius)
                # Vertical overlap amount with the brick
                overlap_top = (ball_prev_y + self.ball_radius) - brick['rect'].top
                overlap_bottom = brick['rect'].bottom - (ball_prev_y - self.ball_radius)

                coll_from_left = ball_prev_x + self.ball_radius <= brick['rect'].left and self.ball_x + self.ball_radius > brick['rect'].left
                coll_from_right = ball_prev_x - self.ball_radius >= brick['rect'].right and self.ball_x - self.ball_radius < brick['rect'].right
                coll_from_top = ball_prev_y + self.ball_radius <= brick['rect'].top and self.ball_y + self.ball_radius > brick['rect'].top
                coll_from_bottom = ball_prev_y - self.ball_radius >= brick['rect'].bottom and self.ball_y - self.ball_radius < brick['rect'].bottom
                
                # Check if the ball's center in the previous frame was outside the brick's x-range or y-range
                # This helps determine the primary direction of impact.
                prev_ball_center_x, prev_ball_center_y = ball_prev_x, ball_prev_y
                
                # Time of collision for horizontal and vertical movement
                time_to_coll_x = float('inf')
                if self.ball_dx > 0: # Moving right
                    time_to_coll_x = (brick['rect'].left - (prev_ball_center_x + self.ball_radius)) / self.ball_dx
                elif self.ball_dx < 0: # Moving left
                    time_to_coll_x = (brick['rect'].right - (prev_ball_center_x - self.ball_radius)) / self.ball_dx
                
                time_to_coll_y = float('inf')
                if self.ball_dy > 0: # Moving down
                    time_to_coll_y = (brick['rect'].top - (prev_ball_center_y + self.ball_radius)) / self.ball_dy
                elif self.ball_dy < 0: # Moving up
                    time_to_coll_y = (brick['rect'].bottom - (prev_ball_center_y - self.ball_radius)) / self.ball_dy

                time_to_coll_x = max(0, time_to_coll_x if time_to_coll_x is not None else float('inf'))
                time_to_coll_y = max(0, time_to_coll_y if time_to_coll_y is not None else float('inf'))

                # Determine if it's primarily a horizontal or vertical collision based on which would happen sooner
                if time_to_coll_x < time_to_coll_y and time_to_coll_x < 1.0 : # Horizontal collision is more likely
                    self.ball_dx = -self.ball_dx
                    # Correct position to prevent sticking
                    if self.ball_dx < 0: # bounced off right side of brick
                         self.ball_x = brick['rect'].right + self.ball_radius + 0.1
                    else: # bounced off left side of brick
                         self.ball_x = brick['rect'].left - self.ball_radius - 0.1
                elif time_to_coll_y < time_to_coll_x and time_to_coll_y < 1.0: # Vertical collision is more likely
                    self.ball_dy = -self.ball_dy
                    if self.ball_dy < 0: # bounced off bottom side
                        self.ball_y = brick['rect'].bottom + self.ball_radius + 0.1
                    else: # bounced off top side
                        self.ball_y = brick['rect'].top - self.ball_radius - 0.1
                else: # Corner hit or exact simultaneous - simple fallback
                    # Check overlap (as a fallback, might not be perfect for fast balls)
                    overlap_x = (self.ball_radius + brick['rect'].width / 2) - abs(self.ball_x - brick['rect'].centerx)
                    overlap_y = (self.ball_radius + brick['rect'].height / 2) - abs(self.ball_y - brick['rect'].centery)
                    if overlap_x < overlap_y : # Collision is more vertical
                        self.ball_dy = -self.ball_dy
                    else: # Collision is more horizontal
                        self.ball_dx = -self.ball_dx
                
                break  # Process one brick collision per frame

        # Check if level cleared
        if not self.bricks: # No bricks left
            self.ball_speed = min(self.max_ball_speed, self.ball_speed + 0.5) # Slower speed increase
            self.create_bricks()
            self.ball_launched = False # Ball returns to paddle
            self.score += 100  # Level clear bonus (increased)
            if self.buzzer:
                 # Play a short win melody
                for freq in [600, 700, 800, 900, 1000]:
                    self.buzzer.play_tone(frequency=freq, duration=0.05)
                    time.sleep(0.03)

        return {"game_over": self.game_over, "score": self.score, "paused": self.paused}

    def render(self, screen):
        """
        Render the game screen.
        Args: screen: Pygame screen object.
        """
        screen.fill(self.BLACK)

        # Draw paddle
        paddle_rect_obj = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height)
        pygame.draw.rect(screen, self.BLUE, paddle_rect_obj, border_radius=3) # Rounded corners

        # Draw ball
        pygame.draw.circle(screen, self.WHITE, (int(self.ball_x), int(self.ball_y)), self.ball_radius)

        # Draw bricks
        for brick in self.bricks:
            if brick['active']:
                pygame.draw.rect(screen, brick['current_color_tuple'], brick['rect'])
                pygame.draw.rect(screen, self.BLACK, brick['rect'], 1) # Border for bricks


        # Render UI text (score, lives)
        if self.font: # Check if font was loaded
            score_surf = self.font.render(f"Score: {self.score}", True, self.WHITE)
            lives_surf = self.font.render(f"Lives: {self.lives}", True, self.WHITE)
            screen.blit(score_surf, (10, 10))
            screen.blit(lives_surf, (self.width - lives_surf.get_width() - 10, 10))

            # Launch ball hint
            if not self.ball_launched and not self.game_over:
                hint_surf = self.font.render("Press A to Launch Ball", True, self.YELLOW)
                screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, self.height - 70))
        else: # Fallback if font failed to load
            pygame.draw.rect(screen, self.RED, (10,10,100,20)) # Placeholder for score
            pygame.draw.rect(screen, self.RED, (self.width-110,10,100,20)) # Placeholder for lives


        # Game Over / Paused screen
        if self.game_over:
            self.draw_game_over_screen(screen)
        elif self.paused:
            self.draw_pause_screen(screen)

    def draw_game_over_screen(self, screen):
        """Draw the Game Over screen."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        if self.font:
            game_over_surf = self.font.render("Game Over!", True, self.RED)
            final_score_surf = self.font.render(f"Final Score: {self.score}", True, self.WHITE)
            restart_surf = self.font.render("Press Start to Restart", True, self.WHITE)

            screen.blit(game_over_surf, (self.width // 2 - game_over_surf.get_width() // 2, self.height // 2 - 60))
            screen.blit(final_score_surf, (self.width // 2 - final_score_surf.get_width() // 2, self.height // 2 - 10))
            screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 40))

    def draw_pause_screen(self, screen):
        """Draw the Pause screen."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0,0))
        if self.font:
            pause_surf = self.font.render("Paused", True, self.YELLOW)
            continue_surf = self.font.render("Press Start to Continue", True, self.WHITE)
            screen.blit(pause_surf, (self.width // 2 - pause_surf.get_width() // 2, self.height // 2 - 40))
            screen.blit(continue_surf, (self.width // 2 - continue_surf.get_width() // 2, self.height // 2 + 10))


    def cleanup(self):
        """Clean up game resources (if any)."""
        pass


# Test function - runs when the script is executed directly
if __name__ == "__main__":
    try:
        pygame.init()
        screen_width_main = 800
        screen_height_main = 600
        main_screen = pygame.display.set_mode((screen_width_main, screen_height_main))
        pygame.display.set_caption("Brick Breaker Game Test")

        game_instance = BrickBreakerGame(screen_width_main, screen_height_main)

        key_action_map = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_SPACE: "a_pressed", # Space for 'A' button
            pygame.K_RETURN: "start_pressed" # Enter for 'Start' button
        }

        game_running = True
        game_clock = pygame.time.Clock()

        while game_running:
            current_inputs = {action: False for action in key_action_map.values()}
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
            
            pressed_keys = pygame.key.get_pressed()
            for key_code, action_name in key_action_map.items():
                if pressed_keys[key_code]:
                    current_inputs[action_name] = True
            
            game_instance.update(current_inputs)
            game_instance.render(main_screen)
            pygame.display.flip()
            game_clock.tick(game_instance.fps) # Use fps from game instance

        game_instance.cleanup()
        pygame.quit()

    except Exception as e:
        print(f"Game execution error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()