#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game1.py - Enhanced Snake Game Implementation

import random
import pygame
import time
import math
from pygame.locals import *

class EnhancedSnakeGame:
    """Enhanced Snake Game Class"""

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width
        self.height = height
        self.buzzer = buzzer

        # Game element sizes
        self.block_size = 20
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
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)

        # Special food colors
        self.GOLDEN_FOOD = (255, 215, 0)
        self.SPEED_FOOD = (255, 100, 100)
        self.MULTI_FOOD = (100, 255, 100)
        self.BONUS_FOOD = (255, 20, 147) # Deep Pink

        # Game speed related
        self.clock = pygame.time.Clock()
        self.base_speed = 8.0 # Use float for more precise speed adjustments
        self.speed_boost_value = 15.0 # Renamed from speed_boost to avoid conflict with powerup key
        self.current_speed = self.base_speed

        # Power-up system
        self.powerups = {
            'invincible': {'active': False, 'timer': 0, 'duration': 5.0},
            'speed_boost': {'active': False, 'timer': 0, 'duration': 3.0},
            'score_multiplier': {'active': False, 'timer': 0, 'duration': 10.0},
            'wall_phase': {'active': False, 'timer': 0, 'duration': 8.0}
        }

        # Particle effect system
        self.particles = []

        # Sound enhancement / Combo system
        self.combo_count = 0
        self.max_combo_achieved = 0 # Added to track max combo
        self.last_eat_time = 0
        self.combo_window = 2.0  # Combo window time

        # Initialize game state
        self.reset_game()

    def reset_game(self):
        """Reset game state"""
        # Snake's initial position
        self.snake = [(self.grid_width // 2, self.grid_height // 2)]
        self.direction = (1, 0) # Moving right initially

        # Food system
        self.foods = []
        self.generate_food() # Generate initial normal food

        # Special food timer
        self.special_food_timer = time.time() # Initialize timer correctly
        self.special_food_interval = 10.0  # 10 seconds to generate a special food

        # Game state
        self.score = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.boosting = False # Manual speed boost

        # Enhanced features
        self.score_multiplier_value = 1 # Renamed from score_multiplier to avoid conflict with powerup key
        self.total_eaten = 0
        self.combo_count = 0
        self.max_combo_achieved = 0 # Reset max combo

        # Reset power-ups
        for powerup_data in self.powerups.values(): # Use a different variable name
            powerup_data['active'] = False
            powerup_data['timer'] = 0
        
        self.current_speed = self.base_speed # Reset speed

        # Clear particles
        self.particles.clear()

        # Movement control
        self.last_move_time = time.time()
        self.move_interval = 1.0 / self.base_speed
        self._last_update_time = time.time() # Initialize for delta_time calculation

    def generate_food(self, food_type='normal'):
        """Generate food"""
        while True:
            pos = (random.randint(0, self.grid_width - 1),
                   random.randint(0, self.grid_height - 1))

            # Ensure not on snake body or other food
            if pos not in self.snake and not any(food_item['pos'] == pos for food_item in self.foods):
                food = {
                    'pos': pos,
                    'type': food_type,
                    'spawn_time': time.time(),
                    'lifetime': 15.0 if food_type != 'normal' else float('inf')
                }

                # Special food attributes
                if food_type == 'golden':
                    food['points'] = 5
                    food['growth'] = 2
                elif food_type == 'speed': # This activates 'speed_boost' powerup
                    food['points'] = 3
                    food['powerup'] = 'speed_boost'
                elif food_type == 'multi': # This activates 'score_multiplier' powerup
                    food['points'] = 2
                    food['powerup'] = 'score_multiplier'
                elif food_type == 'bonus': # This activates 'invincible' powerup
                    food['points'] = 10
                    food['powerup'] = 'invincible'
                elif food_type == 'phase': # This activates 'wall_phase' powerup
                    food['points'] = 4
                    food['powerup'] = 'wall_phase'
                else:  # normal
                    food['points'] = 1
                    food['growth'] = 1

                self.foods.append(food)
                break

    def update_special_foods(self):
        """Update special food generation"""
        current_time = time.time()

        # Generate special food
        if current_time - self.special_food_timer >= self.special_food_interval:
            special_types = ['golden', 'speed', 'multi', 'bonus', 'phase']
            # Adjust spawn probability based on level (example weights)
            weights = [3, 2, 2, 1, 1]  # Golden food has higher chance
            if self.level > 5: # Example: higher chance for rarer items at higher levels
                weights = [2, 2, 2, 2, 2] 
            
            # Ensure there's a limited number of special foods on screen
            if sum(1 for f in self.foods if f['type'] != 'normal') < 3: # Max 3 special foods
                special_type = random.choices(special_types, weights=weights, k=1)[0]
                self.generate_food(special_type)
            self.special_food_timer = current_time

            # Shorten special food spawn interval as level increases
            self.special_food_interval = max(5.0, 10.0 - self.level * 0.5)

        # Remove expired special foods
        self.foods = [food for food in self.foods
                      if food['type'] == 'normal' or
                      (current_time - food['spawn_time']) < food['lifetime']]

    def update_powerups(self, delta_time):
        """Update power-up effects"""
        for name, powerup_data in self.powerups.items():
            if powerup_data['active']:
                powerup_data['timer'] -= delta_time
                if powerup_data['timer'] <= 0:
                    powerup_data['active'] = False
                    # Power-up end effects
                    if name == 'score_multiplier':
                        self.score_multiplier_value = 1
                    elif name == 'speed_boost':
                        # Only reset to base_speed if not manually boosting
                        if not self.boosting:
                             self.current_speed = self.base_speed
                        # If boosting, update() will set to self.speed_boost_value
                    elif name == 'invincible':
                        pass # No specific end effect needed beyond timer
                    elif name == 'wall_phase':
                        pass # No specific end effect needed
                    
                    # Optional: Sound for power-up expiring
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=300, duration=0.2)


    def activate_powerup(self, powerup_type):
        """Activate power-up effect"""
        if powerup_type in self.powerups:
            powerup_data = self.powerups[powerup_type]
            powerup_data['active'] = True
            powerup_data['timer'] = powerup_data['duration']

            # Immediate effects
            if powerup_type == 'score_multiplier':
                self.score_multiplier_value = 3
            elif powerup_type == 'speed_boost':
                # If already boosting manually, power-up might give an extra kick or just refresh timer
                self.current_speed = self.base_speed * 1.5 
            elif powerup_type == 'invincible':
                pass # Effect handled in collision checks
            elif powerup_type == 'wall_phase':
                pass # Effect handled in boundary checks

            # Play power-up sound
            if self.buzzer:
                self.buzzer.play_tone(frequency=800, duration=0.3)

    def create_particles(self, pos, color, count=5, effect_type='eat'):
        """Create particle effects"""
        for _ in range(count):
            if effect_type == 'eat':
                vx_range = (-50, 50)
                vy_range = (-50, 50)
                life_mult = 1.0
                gravity = 100
            elif effect_type == 'boost': # Example for a different particle effect
                vx_range = (-20, 20)
                vy_range = (-100, -50) # Upwards
                life_mult = 0.5
                gravity = 50
                
            particle = {
                'x': pos[0] * self.block_size + self.block_size // 2,
                'y': pos[1] * self.block_size + self.block_size // 2,
                'vx': random.uniform(*vx_range),
                'vy': random.uniform(*vy_range),
                'life': 1.0 * life_mult,
                'color': color,
                'size': random.uniform(2, 6)
            }
            self.particles.append(particle)

    def update_particles(self, delta_time):
        """Update particle effects"""
        active_particles = []
        for particle in self.particles:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time * 2 # Life drains twice as fast
            particle['vy'] += 100 * delta_time  # Gravity effect

            if particle['life'] > 0:
                active_particles.append(particle)
        self.particles = active_particles


    def update(self, controller_input=None):
        """Update game state"""
        current_time = time.time()
        delta_time = current_time - self._last_update_time
        self._last_update_time = current_time

        # Handle pause/game over input first
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                # Debounce start press for restart/resume
                if not hasattr(self, 'start_handled_time') or current_time - self.start_handled_time > 0.5:
                    if self.game_over:
                        self.reset_game()
                    else: # Paused
                        self.paused = False
                    self.start_handled_time = current_time # Mark as handled
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused}

        # Update systems that run every frame regardless of movement
        self.update_powerups(delta_time)
        self.update_particles(delta_time)
        self.update_special_foods() # This also uses time, so frequent updates are good

        # Handle input
        if controller_input:
            # Initialize input delay for left stick if not exists
            if not hasattr(self, 'stick_input_delay'):
                self.stick_input_delay = 0.2  # Stick input delay similar to D-pad
                self.last_stick_input_time = 0
                self.stick_threshold = 0.6  # Threshold for stick activation
                self.last_stick_direction = None
            
            # Left stick input processing (single-trigger movement)
            stick_x = controller_input.get("left_stick_x", 0.0)
            stick_y = controller_input.get("left_stick_y", 0.0)
            stick_direction_request = None
            
            # Determine stick direction with dead zone
            if abs(stick_x) > self.stick_threshold or abs(stick_y) > self.stick_threshold:
                if abs(stick_x) > abs(stick_y):  # Horizontal movement dominant
                    if stick_x > self.stick_threshold and self.direction != (-1, 0):
                        stick_direction_request = (1, 0)  # Right
                    elif stick_x < -self.stick_threshold and self.direction != (1, 0):
                        stick_direction_request = (-1, 0)  # Left
                else:  # Vertical movement dominant
                    if stick_y > self.stick_threshold and self.direction != (0, -1):
                        stick_direction_request = (0, 1)  # Down
                    elif stick_y < -self.stick_threshold and self.direction != (0, 1):
                        stick_direction_request = (0, -1)  # Up
            
            # Apply stick input with delay (single-trigger)
            if (stick_direction_request and 
                stick_direction_request != self.last_stick_direction and
                current_time - self.last_stick_input_time >= self.stick_input_delay):
                self.direction = stick_direction_request
                self.last_stick_input_time = current_time
                self.last_stick_direction = stick_direction_request
            elif not stick_direction_request:
                self.last_stick_direction = None  # Reset when stick returns to center
            
            # D-pad directional control (preserve original logic)
            d_pad_direction_request = None
            if controller_input.get("up_pressed") and self.direction != (0, 1):
                d_pad_direction_request = (0, -1)
            elif controller_input.get("down_pressed") and self.direction != (0, -1):
                d_pad_direction_request = (0, 1)
            elif controller_input.get("left_pressed") and self.direction != (1, 0):
                d_pad_direction_request = (-1, 0)
            elif controller_input.get("right_pressed") and self.direction != (-1, 0):
                d_pad_direction_request = (1, 0)
            
            # D-pad takes priority over stick for precise control
            if d_pad_direction_request:
                self.direction = d_pad_direction_request

            # Boost control (manual speed up)
            self.boosting = controller_input.get("a_pressed", False)

            # Pause control
            if controller_input.get("start_pressed"):
                 if not hasattr(self, 'start_handled_time') or current_time - self.start_handled_time > 0.5:
                    self.paused = not self.paused
                    self.start_handled_time = current_time
                    if self.buzzer: self.buzzer.play_tone(frequency=500, duration=0.1)
                    # Return immediately after pausing to prevent further game logic this frame
                    return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # Update movement speed based on powerups and manual boost
        if self.powerups['speed_boost']['active']:
            # Speed boost powerup overrides manual boosting if it's faster or has a different effect
             move_speed = self.base_speed * 1.5 # Assuming powerup speed is fixed multiplier
        elif self.boosting:
            move_speed = self.speed_boost_value
        else:
            move_speed = self.current_speed # current_speed is base_speed or level-adjusted speed
        
        self.move_interval = 1.0 / max(move_speed, 1.0) # Ensure speed is at least 1

        # Check if it's time to move
        if current_time - self.last_move_time < self.move_interval:
            return {"game_over": self.game_over, "score": self.score, "paused": self.paused} # Added paused state

        self.last_move_time = current_time

        # Move snake
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        # Boundary handling
        if self.powerups['wall_phase']['active']:
            # Wall phasing mode
            new_head = (new_head[0] % self.grid_width, new_head[1] % self.grid_height)
        else:
            # Normal boundary check
            if (new_head[0] < 0 or new_head[0] >= self.grid_width or
                    new_head[1] < 0 or new_head[1] >= self.grid_height):
                self.game_over = True
                if self.buzzer:
                    self.buzzer.play_tone(frequency=200, duration=1.0) # Game over sound
                return {"game_over": True, "score": self.score, "paused": self.paused}

        # Check collision with self
        # Invincible powerup allows passing through self
        if not self.powerups['invincible']['active'] and new_head in self.snake[1:]: # Don't check head against itself
            self.game_over = True
            if self.buzzer:
                self.buzzer.play_tone(frequency=200, duration=1.0) # Game over sound
            return {"game_over": True, "score": self.score, "paused": self.paused}

        # Add new head
        self.snake.insert(0, new_head)

        # Check if food is eaten
        eaten_food_item = None
        for food_item in self.foods[:]: # Iterate over a copy for safe removal
            if new_head == food_item['pos']:
                eaten_food_item = food_item
                self.foods.remove(food_item)
                break
        
        if eaten_food_item:
            # Handle combo
            if current_time - self.last_eat_time < self.combo_window:
                self.combo_count += 1
            else:
                self.combo_count = 1 # Reset combo if window passed
            self.last_eat_time = current_time
            self.max_combo_achieved = max(self.max_combo_achieved, self.combo_count)

            # Calculate score
            base_points = eaten_food_item['points']
            combo_bonus_multiplier = 1 + (self.combo_count -1) * 0.1 # e.g. 10% bonus per combo hit after first
            total_points = int(base_points * combo_bonus_multiplier * self.score_multiplier_value)
            self.score += total_points

            # Snake growth
            growth_amount = eaten_food_item.get('growth', 1)
            # No need to subtract 1 from growth_amount because the head is added, and tail is popped if no food
            # So, for growth N, we need to add N-1 segments if tail isn't popped.
            # Since tail will be popped if no food, and NOT popped if food is eaten,
            # simply adding growth_amount -1 tail copies is correct IF we don't pop.
            # The current logic: add head, then if no food, pop tail. If food, don't pop tail.
            # So, if growth is 1, effectively snake grows by 1. If growth is 2, snake should grow by 2.
            # This means if growth is X, we need to add X-1 dummy segments to the tail before the pop logic.
            # However, the current code adds X-1 segments AND doesn't pop. This is correct.

            for _ in range(growth_amount -1): # Already grew by 1 (head added, tail not popped)
                 if self.snake: # Should always be true
                    self.snake.append(self.snake[-1]) # Append a copy of the last segment


            # Activate power-up if any
            if 'powerup' in eaten_food_item:
                self.activate_powerup(eaten_food_item['powerup'])

            # Create particle effects
            food_color_map = {
                'normal': self.RED, 'golden': self.GOLDEN_FOOD, 'speed': self.SPEED_FOOD,
                'multi': self.MULTI_FOOD, 'bonus': self.BONUS_FOOD, 'phase': self.PURPLE
            }
            self.create_particles(eaten_food_item['pos'],
                                  food_color_map.get(eaten_food_item['type'], self.RED),
                                  count=10 if eaten_food_item['type'] != 'normal' else 5)

            # Play sound effect
            if self.buzzer:
                if eaten_food_item['type'] == 'normal':
                    freq = min(600 + self.combo_count * 50, 1500) # Adjusted frequency
                    self.buzzer.play_tone(frequency=freq, duration=0.15)
                else:
                    # Special food sound
                    self.buzzer.play_tone(frequency=1000, duration=0.1)
                    pygame.time.wait(50) # Short pause for distinct sound
                    self.buzzer.play_tone(frequency=1200, duration=0.1)
            
            # Generate new normal food if a normal food was eaten or if no normal food exists
            if eaten_food_item['type'] == 'normal' or not any(f['type'] == 'normal' for f in self.foods):
                self.generate_food()

            # Level up check
            self.total_eaten += 1
            if self.total_eaten % 10 == 0: # Level up every 10 foods
                self.level += 1
                self.base_speed += 0.5 # Slower speed increase
                if not self.powerups['speed_boost']['active'] and not self.boosting:
                    self.current_speed = self.base_speed
                if self.buzzer:
                    self.buzzer.play_tone(frequency=1500, duration=0.5) # Level up sound
        else:
            # No food eaten, remove tail segment
            if self.snake: self.snake.pop()

        # Ensure at least one normal food on the map if others were special and expired
        if not any(f['type'] == 'normal' for f in self.foods):
            self.generate_food()
            
        return {"game_over": self.game_over, "score": self.score, "paused": self.paused}

    def render(self, screen):
        """Render the game screen"""
        # Clear screen
        screen.fill(self.BLACK)

        # Draw food
        for food_item in self.foods:
            food_color_map = {
                'normal': self.RED, 'golden': self.GOLDEN_FOOD, 'speed': self.SPEED_FOOD,
                'multi': self.MULTI_FOOD, 'bonus': self.BONUS_FOOD, 'phase': self.PURPLE
            }
            color = food_color_map.get(food_item['type'], self.RED)

            food_rect = pygame.Rect(
                food_item['pos'][0] * self.block_size,
                food_item['pos'][1] * self.block_size,
                self.block_size,
                self.block_size
            )

            # Special food flashing effect
            if food_item['type'] != 'normal':
                current_time = time.time()
                remaining_time = food_item['lifetime'] - (current_time - food_item['spawn_time'])
                if remaining_time < 3.0:  # Flash in the last 3 seconds
                    if int(current_time * 6) % 2:  # 3Hz flash (6 changes per sec)
                        # Make color brighter for flash
                        color = tuple(min(255, c + 60) for c in color)
            
            pygame.draw.rect(screen, color, food_rect)
            # Special food marker (e.g., a small white circle)
            if food_item['type'] != 'normal':
                pygame.draw.circle(screen, self.WHITE, food_rect.center, self.block_size // 6)


        # Draw snake
        for i, segment in enumerate(self.snake):
            # Base color: blue for head, green for body
            seg_color = self.BLUE if i == 0 else self.GREEN 
            
            # Invincible power-up flash effect
            if self.powerups['invincible']['active']:
                if int(time.time() * 10) % 2: # Faster flash for invincibility
                     seg_color = self.YELLOW # Flash to yellow, for example
            
            # Wall phase power-up visual (e.g., semi-transparent or different color)
            if self.powerups['wall_phase']['active'] and i == 0: # Only head maybe
                # Example: make head slightly transparent or a different hue
                 # For simplicity, let's make it lighter
                seg_color = tuple(min(255, c + 50) for c in seg_color)


            segment_rect = pygame.Rect(
                segment[0] * self.block_size,
                segment[1] * self.block_size,
                self.block_size,
                self.block_size
            )
            pygame.draw.rect(screen, seg_color, segment_rect)
            
            # Snake head decoration (e.g., eyes)
            if i == 0:
                eye_radius = self.block_size // 8
                offset_x1, offset_y1 = 0,0
                offset_x2, offset_y2 = 0,0

                if self.direction == (1,0): # Right
                    offset_x1, offset_y1 = self.block_size // 2, -self.block_size // 4
                    offset_x2, offset_y2 = self.block_size // 2, self.block_size // 4
                elif self.direction == (-1,0): # Left
                    offset_x1, offset_y1 = -self.block_size // 2, -self.block_size // 4
                    offset_x2, offset_y2 = -self.block_size // 2, self.block_size // 4
                elif self.direction == (0,1): # Down
                    offset_x1, offset_y1 = -self.block_size // 4, self.block_size // 2
                    offset_x2, offset_y2 = self.block_size // 4, self.block_size // 2
                elif self.direction == (0,-1): # Up
                    offset_x1, offset_y1 = -self.block_size // 4, -self.block_size // 2
                    offset_x2, offset_y2 = self.block_size // 4, -self.block_size // 2
                
                eye1_pos = (segment_rect.centerx + offset_x1, segment_rect.centery + offset_y1)
                eye2_pos = (segment_rect.centerx + offset_x2, segment_rect.centery + offset_y2)
                pygame.draw.circle(screen, self.WHITE, eye1_pos, eye_radius)
                pygame.draw.circle(screen, self.WHITE, eye2_pos, eye_radius)


        # Draw particles
        for particle in self.particles:
            # Particle life affects alpha and size
            alpha = max(0, min(255, int(particle['life'] * 255)))
            size = max(1, int(particle['size'] * particle['life'])) # Size shrinks with life
            
            if alpha > 0 and size > 0:
                # Create a surface for each particle to handle alpha correctly
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                # Draw circle on this temp surface
                pygame.draw.circle(particle_surf, (*particle['color'][:3], alpha), (size, size), size)
                # Blit the temp surface onto the main screen
                screen.blit(particle_surf, (int(particle['x'] - size), int(particle['y'] - size)))


        # Draw UI
        font = pygame.font.Font(None, 36) # Default font, size 36

        # Basic info
        score_text_surf = font.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text_surf, (10, 10))

        level_text_surf = font.render(f"Level: {self.level}", True, self.WHITE)
        screen.blit(level_text_surf, (10, 50))

        current_speed_display = self.current_speed
        if self.powerups['speed_boost']['active']:
            current_speed_display = self.base_speed * 1.5
        elif self.boosting:
            current_speed_display = self.speed_boost_value

        speed_text_surf = font.render(f"Speed: {current_speed_display:.1f}", True, self.WHITE)
        screen.blit(speed_text_surf, (10, 90))

        # Combo display
        if self.combo_count > 1:
            combo_text_surf = font.render(f"Combo x{self.combo_count}!", True, self.YELLOW)
            # Position combo text dynamically or at a fixed nice spot
            screen.blit(combo_text_surf, (self.width - combo_text_surf.get_width() - 10, 10))

        # Power-up status display
        y_offset = 130
        font_small = pygame.font.Font(None, 28) # Slightly smaller font for status
        
        powerup_display_names = {
            'invincible': 'Invincible',
            'speed_boost': 'Speed Boost',
            'score_multiplier': 'Score x3',
            'wall_phase': 'Wall Phase'
        }

        active_powerup_count = 0
        for name, powerup_data in self.powerups.items():
            if powerup_data['active']:
                active_powerup_count +=1
                remaining_time = powerup_data['timer']
                text_surf = font_small.render(f"{powerup_display_names[name]}: {remaining_time:.1f}s", True, self.CYAN)
                screen.blit(text_surf, (10, y_offset))
                y_offset += 30
        
        if active_powerup_count == 0 and self.level > 1: # Show a tip if no powerups active after level 1
            tip_text = font_small.render("Eat special food for power-ups!", True, self.GRAY)
            screen.blit(tip_text, (10, y_offset))


        # Game Over / Paused screen
        if self.game_over:
            self.draw_game_over_screen(screen) # Renamed for clarity
        elif self.paused:
            self.draw_pause_screen(screen) # Renamed for clarity

    def draw_game_over_screen(self, screen): # Renamed
        """Draw the Game Over screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA) # For transparency
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(overlay, (0, 0))

        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)

        # Title
        title_surf = font_large.render("Game Over", True, self.RED)
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, self.height // 2 - 150))

        # Statistics
        stats_info = [
            f"Final Score: {self.score}",
            f"Reached Level: {self.level}",
            f"Total Food Eaten: {self.total_eaten}",
            f"Max Combo: {self.max_combo_achieved}" # Using the new variable
        ]

        for i, stat_str in enumerate(stats_info):
            stat_surf = font_small.render(stat_str, True, self.WHITE)
            screen.blit(stat_surf, (self.width // 2 - stat_surf.get_width() // 2,
                                   self.height // 2 - 60 + i * 40)) # Adjusted y_pos

        restart_surf = font_medium.render("Press Start to Restart", True, self.WHITE)
        screen.blit(restart_surf, (self.width // 2 - restart_surf.get_width() // 2,
                                 self.height // 2 + 100)) # Adjusted y_pos

    def draw_pause_screen(self, screen): # Renamed
        """Draw the Pause screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        font_large = pygame.font.Font(None, 80) # Larger "Paused" text
        pause_surf = font_large.render("Paused", True, self.YELLOW)
        screen.blit(pause_surf, (self.width // 2 - pause_surf.get_width() // 2, self.height // 2 - 60))

        font_medium = pygame.font.Font(None, 40)
        continue_surf = font_medium.render("Press Start to Continue", True, self.WHITE)
        screen.blit(continue_surf, (self.width // 2 - continue_surf.get_width() // 2,
                                   self.height // 2 + 20))

    def cleanup(self):
        """Clean up game resources (if any)"""
        # For Pygame, this is usually handled by pygame.quit()
        pass

# For backward compatibility if other scripts import SnakeGame
SnakeGame = EnhancedSnakeGame

# If this script is run directly, for testing
if __name__ == "__main__":
    try:
        # Initialize Pygame
        pygame.init()

        # Set up window
        screen_width_main = 800
        screen_height_main = 600
        main_screen = pygame.display.set_mode((screen_width_main, screen_height_main))
        pygame.display.set_caption("Enhanced Snake Game Test")

        # Create game instance
        game_instance = SnakeGame(screen_width_main, screen_height_main)

        # Map keyboard keys to simulated controller inputs
        key_action_map = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_SPACE: "a_pressed",  # Use Space for 'A' button (boost)
            pygame.K_RETURN: "start_pressed" # Enter for 'Start' button (pause/restart)
        }
        
        game_running = True
        game_clock = pygame.time.Clock() # Use a local clock for the main loop

        while game_running:
            # Event handling
            current_inputs = {action: False for action in key_action_map.values()}

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_running = False
                # Handle single press for start/pause directly if needed,
                # but game.update already has debounce for start.
                # For continuous presses (like movement), get_pressed is better.

            # Get currently pressed keys for continuous actions
            pressed_keys = pygame.key.get_pressed()
            for key_code, action_name in key_action_map.items():
                if pressed_keys[key_code]:
                    current_inputs[action_name] = True
            
            # Update game
            game_instance.update(current_inputs)

            # Render game
            game_instance.render(main_screen)
            pygame.display.flip() # Update the full display

            # Control frame rate
            game_clock.tick(60) # Target 60 FPS

        # Quit Pygame
        game_instance.cleanup()
        pygame.quit()

    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()