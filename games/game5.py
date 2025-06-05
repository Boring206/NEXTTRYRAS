#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game5_enhanced.py - Memory Match Game Implementation (Enhanced)
import random
import pygame
import time
import math
from pygame.locals import *

class MemoryMatchGame:
    """Memory Match Game Class (Enhanced)"""

    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width
        self.height = height
        self.buzzer = buzzer
        self._internal_buzzer_active = False

        # Game States
        self.MENU = "MENU"
        self.SHOWING_CARDS = "SHOWING_CARDS"
        self.PLAYING = "PLAYING"
        self.PAUSED = "PAUSED"
        self.GAME_OVER = "GAME_OVER"
        self.game_state = self.MENU

        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (128, 0, 128)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.PINK = (255, 192, 203)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        self.LIGHT_BLUE = (173, 216, 230)
        self.LIME_GREEN = (50, 205, 50)
        self.GOLD = (255, 215, 0)

        # Game settings (default to easy)
        self.grid_cols = 4
        self.grid_rows = 4
        self.difficulty = "Easy (4x4)" # Default difficulty

        # Card colors (extended for more pairs)
        self.available_card_colors = [
            self.RED, self.GREEN, self.BLUE, self.YELLOW,
            self.PURPLE, self.CYAN, self.ORANGE, self.PINK,
            self.LIME_GREEN, self.GOLD, self.LIGHT_BLUE, (165, 42, 42) # Brown
        ]

        # Card size and margin (will be set in reset_game)
        self.card_width = 0
        self.card_height = 0
        self.card_margin = 5

        # Game state variables (initialized in reset_game)
        self.cards = []
        self.total_pairs = 0
        self.cursor_row = 0
        self.cursor_col = 0
        self.revealed_cards = []
        self.matches_found = 0
        self.moves = 0
        self.score = 0
        self.start_time = 0
        self.game_over_flag = False # Renamed from self.game_over to avoid conflict with state
        self.paused_flag = False    # Renamed from self.paused

        self.show_all_time_duration = 3.0  # Time to show all cards at start
        self.show_all_start_time = 0

        self.last_input_time = 0
        self.input_delay = 0.2 # Slightly reduced delay for responsiveness
        self.flip_animation_duration = 0.4 # Duration for card flip animation

        self.particles = []
        self.match_effect_timer = 0
        self.flip_back_timer_start = 0 # Renamed for clarity
        self.flip_back_active = False

        # Menu settings
        self.menu_options = ["Easy (4x4)", "Medium (6x4)", "Quit"]
        self.menu_selected_option = 0
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._init_fonts()

        self._init_sounds()
        # self.reset_game() # Don't reset yet, wait for menu selection

    def _init_fonts(self):
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

    def _init_sounds(self):
        if self.buzzer is None:
            try:
                pygame.mixer.init()
                self.sound_flip = self._load_sound("flip.wav")
                self.sound_match = self._load_sound("match.wav")
                self.sound_nomatch = self._load_sound("nomatch.wav")
                self.sound_win = self._load_sound("win.wav")
                self.sound_select = self._load_sound("select.wav") # For menu navigation
                self._internal_buzzer_active = True
                print("Internal Pygame mixer initialized for sounds.")
            except pygame.error as e:
                print(f"Pygame mixer could not be initialized or sound files not found: {e}")
                self._internal_buzzer_active = False
                # Initialize sound attributes as None when mixer fails
                self.sound_flip = None
                self.sound_match = None
                self.sound_nomatch = None
                self.sound_win = None
                self.sound_select = None
        else:
            print("External buzzer object provided.")
            # Initialize sound attributes as None when using external buzzer
            self.sound_flip = None
            self.sound_match = None
            self.sound_nomatch = None
            self.sound_win = None
            self.sound_select = None

    def _load_sound(self, filename):
        try:
            sound = pygame.mixer.Sound(filename)
            return sound
        except pygame.error as e:
            print(f"Could not load sound: {filename} - {e}")
            return None

    def _play_sound(self, sound_obj, frequency=None, duration=None): # frequency/duration for external buzzer compatibility
        if self.buzzer:
            if frequency and duration:
                 self.buzzer.play_tone(frequency=frequency, duration=duration)
            # Add more specific calls if external buzzer has named melodies
        elif self._internal_buzzer_active and sound_obj:
            sound_obj.play()

    def set_difficulty(self, difficulty_str):
        self.difficulty = difficulty_str
        if difficulty_str == "Easy (4x4)":
            self.grid_cols = 4
            self.grid_rows = 4
        elif difficulty_str == "Medium (6x4)":
            self.grid_cols = 6
            self.grid_rows = 4
        # Add more difficulties if needed
        self.reset_game()
        self.game_state = self.SHOWING_CARDS

    def reset_game(self):
        """Reset game state based on current difficulty"""
        self.total_pairs = (self.grid_cols * self.grid_rows) // 2

        # Card size calculation based on grid and screen dimensions
        # Adjust margins/paddings for better layout
        top_hud_height = 100
        bottom_hud_height = 100
        side_padding = 50

        available_width = self.width - (2 * side_padding) - (self.grid_cols - 1) * self.card_margin * 2
        available_height = self.height - top_hud_height - bottom_hud_height - (self.grid_rows - 1) * self.card_margin * 2
        
        self.card_width = available_width // self.grid_cols
        self.card_height = available_height // self.grid_rows

        # Create card pairs
        self.cards = []
        # Ensure enough colors, repeat if necessary
        num_colors_needed = self.total_pairs
        if num_colors_needed > len(self.available_card_colors):
            chosen_card_colors = (self.available_card_colors * (num_colors_needed // len(self.available_card_colors) + 1))[:num_colors_needed]
        else:
            chosen_card_colors = self.available_card_colors[:num_colors_needed]
        
        colors_for_cards = chosen_card_colors * 2  # Two of each color
        random.shuffle(colors_for_cards)

        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                index = row * self.grid_cols + col
                if index < len(colors_for_cards): # Check to prevent index out of bounds if logic is flawed
                    card = {
                        'row': row,
                        'col': col,
                        'color': colors_for_cards[index],
                        'revealed': False,
                        'matched': False,
                        'flipping': False,        # True during flip animation
                        'flip_progress': 0,     # 0 to 1 for animation
                        'flip_start_time': 0,   # Start time of the flip
                        'id': index             # Unique ID for easier handling
                    }
                    self.cards.append(card)
                else: # Should not happen with correct total_pairs and color list generation
                    print(f"Warning: Not enough colors for card at index {index}")

        self.cursor_row = 0
        self.cursor_col = 0
        self.revealed_cards = []
        self.matches_found = 0
        self.moves = 0
        self.score = 0
        self.start_time = time.time()

        self.game_over_flag = False
        self.paused_flag = False
        self.show_all_start_time = time.time()

        self.last_input_time = time.time() # Prevent immediate input processing after reset

        self.particles = []
        self.match_effect_timer = 0
        self.flip_back_active = False
        self.flip_back_timer_start = 0

        print(f"Game reset for {self.difficulty}. Grid: {self.grid_cols}x{self.grid_rows}, Pairs: {self.total_pairs}, Card Size: {self.card_width}x{self.card_height}")

    def get_card_at(self, row, col):
        """Get the card at the specified position"""
        index = row * self.grid_cols + col
        if 0 <= index < len(self.cards):
            # This assumes cards are ordered, which they are during creation.
            # A more robust way if order could change:
            for card in self.cards:
                if card['row'] == row and card['col'] == col:
                    return card
        return None

    def get_card_rect(self, card):
        """Get the rectangle for drawing the card"""
        # Calculate dynamic start X and Y to center the grid
        grid_total_width = self.grid_cols * (self.card_width + self.card_margin * 2) - self.card_margin*2
        grid_total_height = self.grid_rows * (self.card_height + self.card_margin * 2) - self.card_margin*2
        
        start_x = (self.width - grid_total_width) // 2
        start_y = 100 # Top HUD area
        
        x = start_x + card['col'] * (self.card_width + self.card_margin * 2)
        y = start_y + card['row'] * (self.card_height + self.card_margin * 2)
        return pygame.Rect(x, y, self.card_width, self.card_height)

    def handle_click(self, pos):
        if self.game_state == self.PLAYING:
            if len(self.revealed_cards) >= 2 or self.flip_back_active: # Don't allow clicks if 2 cards are revealed or during flip_back
                return

            for card in self.cards:
                rect = self.get_card_rect(card)
                if rect.collidepoint(pos):
                    if not card['revealed'] and not card['matched']:
                        self.cursor_row = card['row']
                        self.cursor_col = card['col']
                        self.attempt_flip_card(card['row'], card['col'])
                    break
        elif self.game_state == self.MENU:
            menu_item_height = 50
            base_y = self.height // 2 - (len(self.menu_options) * menu_item_height) // 2
            for i, option_text in enumerate(self.menu_options):
                text_render = self.font_medium.render(option_text, True, self.WHITE)
                text_rect = text_render.get_rect(center=(self.width // 2, base_y + i * menu_item_height))
                if text_rect.collidepoint(pos):
                    self.menu_selected_option = i
                    self._process_menu_selection()
                    break

    def attempt_flip_card(self, row, col):
        if len(self.revealed_cards) >= 2: # Already two cards selected
            return False

        card = self.get_card_at(row, col)
        if not card or card['revealed'] or card['matched'] or card['flipping']:
            return False

        # Immediately reveal the card instead of using animation
        card['revealed'] = True
        card['flipping'] = False
        card['flip_start_time'] = time.time()
        card['flip_progress'] = 1.0

        self.revealed_cards.append(card)

        self._play_sound(self.sound_flip, frequency=600, duration=0.1)
        self.moves += 1
        
        # Check for match immediately if we have 2 cards
        if len(self.revealed_cards) == 2:
            self.check_match()
        
        return True

    def check_match(self):
        if len(self.revealed_cards) == 2:
            card1, card2 = self.revealed_cards

            if card1['color'] == card2['color']: # Match
                card1['matched'] = True
                card2['matched'] = True
                self.matches_found += 1
                self.score += 100 - self.moves * 2 # Bonus points
                if self.score < 0: self.score = 0

                self.create_match_particles(card1)
                self.create_match_particles(card2)
                self.match_effect_timer = 1.0 # For visual feedback on matched cards

                self._play_sound(self.sound_match, frequency=800, duration=0.3)

                if self.matches_found == self.total_pairs:
                    self.game_over_flag = True
                    self.game_state = self.GAME_OVER
                    elapsed_time = time.time() - self.start_time
                    time_bonus = max(0, (self.total_pairs * 20) - int(elapsed_time)) # Adjusted time bonus
                    self.score += time_bonus
                    self._play_sound(self.sound_win) # Or self.buzzer.play_win_melody()
                
                self.revealed_cards = [] # Clear for next turn
            else: # No match
                self.flip_back_active = True
                self.flip_back_timer_start = time.time()
                self._play_sound(self.sound_nomatch, frequency=300, duration=0.2)
                # Don't clear revealed_cards yet, do it after flip_back_timer

    def create_match_particles(self, card):
        rect = self.get_card_rect(card)
        center_x, center_y = rect.centerx, rect.centery
        for _ in range(15): # More particles
            particle = {
                'x': center_x, 'y': center_y,
                'vx': random.uniform(-150, 150), 'vy': random.uniform(-200, -50), # More upward burst
                'life': random.uniform(0.5, 1.2), 'color': card['color'],
                'size': random.uniform(4, 10)
            }
            self.particles.append(particle)

    def update_particles(self, delta_time):
        for p in self.particles[:]:
            p['x'] += p['vx'] * delta_time
            p['y'] += p['vy'] * delta_time
            p['vy'] += 300 * delta_time  # Stronger gravity
            p['life'] -= delta_time
            if p['life'] <= 0:
                self.particles.remove(p)

    def _process_menu_selection(self):
        selected = self.menu_options[self.menu_selected_option]
        self._play_sound(self.sound_select, frequency=500, duration=0.1)
        if selected == "Quit":
            return {"action": "quit"} # Signal to main loop to quit
        else:
            self.set_difficulty(selected)
            # self.game_state will be set by set_difficulty
        return {"action": "start_game"}

    def update(self, controller_input=None, events=None):
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time

        # Update particles
        self.update_particles(delta_time)

        if events is None: events = []

        # Handle mouse clicks for menu and game
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.handle_click(event.pos)

        # --- Game State Logic ---
        if self.game_state == self.MENU:
            if controller_input and current_time - self.last_input_time >= self.input_delay:
                # Initialize left stick parameters if not exists
                if not hasattr(self, 'stick_threshold'):
                    self.stick_threshold = 0.7
                    self.last_stick_direction = None

                moved = False
                
                # Left stick input processing (single-trigger movement)
                stick_y = controller_input.get("left_stick_y", 0.0)
                stick_direction = None
                
                if abs(stick_y) > self.stick_threshold:
                    if stick_y > self.stick_threshold:
                        stick_direction = "down"
                    elif stick_y < -self.stick_threshold:
                        stick_direction = "up"
                
                # Apply stick movement (single-trigger with delay)
                if stick_direction and stick_direction != self.last_stick_direction:
                    if stick_direction == "up":
                        self.menu_selected_option = (self.menu_selected_option - 1) % len(self.menu_options)
                        moved = True
                    elif stick_direction == "down":
                        self.menu_selected_option = (self.menu_selected_option + 1) % len(self.menu_options)
                        moved = True
                    self.last_stick_direction = stick_direction
                elif not stick_direction:
                    self.last_stick_direction = None

                # D-pad input (preserve original logic, takes priority)
                if controller_input.get("up_pressed"):
                    self.menu_selected_option = (self.menu_selected_option - 1) % len(self.menu_options)
                    moved = True
                elif controller_input.get("down_pressed"):
                    self.menu_selected_option = (self.menu_selected_option + 1) % len(self.menu_options)
                    moved = True

                if controller_input.get("a_pressed"):
                    result = self._process_menu_selection()
                    if result == "quit":
                        return {"quit": True}
                    moved = True

                if moved:
                    self.last_input_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=400, duration=0.05)

        elif self.game_state == self.SHOWING_CARDS:
            if current_time - self.show_all_start_time >= self.show_all_time_duration:
                for card in self.cards:
                    card['revealed'] = False
                self.game_state = self.PLAYING

        elif self.game_state == self.PLAYING:
            if controller_input and current_time - self.last_input_time >= self.input_delay:
                # Initialize left stick parameters if not exists
                if not hasattr(self, 'stick_threshold'):
                    self.stick_threshold = 0.7
                    self.last_stick_direction = None

                moved_cursor = False
                
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
                    if stick_direction == "up" and self.cursor_row > 0:
                        self.cursor_row -= 1
                        moved_cursor = True
                    elif stick_direction == "down" and self.cursor_row < self.grid_rows - 1:
                        self.cursor_row += 1
                        moved_cursor = True
                    elif stick_direction == "left" and self.cursor_col > 0:
                        self.cursor_col -= 1
                        moved_cursor = True
                    elif stick_direction == "right" and self.cursor_col < self.grid_cols - 1:
                        self.cursor_col += 1
                        moved_cursor = True
                    self.last_stick_direction = stick_direction
                elif not stick_direction:
                    self.last_stick_direction = None

                # D-pad input (preserve original logic, takes priority)
                if controller_input.get("up_pressed") and self.cursor_row > 0:
                    self.cursor_row -= 1
                    moved_cursor = True
                elif controller_input.get("down_pressed") and self.cursor_row < self.grid_rows - 1:
                    self.cursor_row += 1
                    moved_cursor = True
                elif controller_input.get("left_pressed") and self.cursor_col > 0:
                    self.cursor_col -= 1
                    moved_cursor = True
                elif controller_input.get("right_pressed") and self.cursor_col < self.grid_cols - 1:
                    self.cursor_col += 1
                    moved_cursor = True
                elif controller_input.get("a_pressed"):
                    if len(self.revealed_cards) < 2 and not self.flip_back_active:
                        self.attempt_flip_card(self.cursor_row, self.cursor_col)
                    moved_cursor = True

                if moved_cursor:
                    self.last_input_time = current_time
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=250, duration=0.05)

            # Handle flip back timing for non-matching cards
            if self.flip_back_active and current_time - self.flip_back_timer_start >= 1.0:
                # Flip back the non-matching cards
                for card in self.revealed_cards:
                    card['revealed'] = False
                self.revealed_cards = []
                self.flip_back_active = False

        elif self.game_state == self.GAME_OVER:
            if controller_input and controller_input.get("a_pressed"):
                self.game_state = self.MENU

        return {"game_over": self.game_over_flag, "score": self.score}

    def render(self, screen):
        screen.fill(self.BLACK)

        if self.game_state == self.MENU:
            self.draw_menu(screen)
        elif self.game_state in [self.SHOWING_CARDS, self.PLAYING]:
            self.draw_hud(screen, self.game_state == self.SHOWING_CARDS, time.time())
            
            # Draw cards
            for card in self.cards:
                card_rect = self.get_card_rect(card)
                
                if card['matched']:
                    pygame.draw.rect(screen, self.DARK_GRAY, card_rect)
                elif card['revealed'] or self.game_state == self.SHOWING_CARDS:
                    pygame.draw.rect(screen, card['color'], card_rect)
                else:
                    pygame.draw.rect(screen, self.GRAY, card_rect)
                
                pygame.draw.rect(screen, self.WHITE, card_rect, 2)
            
            # Draw cursor
            if self.game_state == self.PLAYING:
                cursor_card = self.get_card_at(self.cursor_row, self.cursor_col)
                if cursor_card:
                    cursor_rect = self.get_card_rect(cursor_card)
                    pygame.draw.rect(screen, self.YELLOW, cursor_rect, 4)

            self.draw_particles(screen)

        elif self.game_state == self.GAME_OVER:
            self.draw_game_over_screen(screen)

    def draw_particles(self, screen):
        for particle in self.particles:
            if particle['life'] > 0:
                # 計算 alpha 值 (0-255)
                alpha = int(particle['life'] * 255)
                alpha = max(0, min(255, alpha))  # 確保在有效範圍內
                
                # 計算粒子大小
                size = max(2, int(6 * particle['life']))
                
                # 確保顏色是有效的 RGB 格式
                color = particle['color']
                if len(color) == 3:  # RGB 格式
                    r, g, b = color
                elif len(color) == 4:  # RGBA 格式，取前三個值
                    r, g, b = color[:3]
                else:
                    r, g, b = 255, 255, 255  # 預設白色
                
                # 創建帶有 alpha 的表面
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                
                # 使用 RGB 顏色繪製圓形
                pygame.draw.circle(particle_surf, (r, g, b), (size, size), size)
                
                # 設置整個表面的 alpha
                particle_surf.set_alpha(alpha)
                
                # 繪製到螢幕上
                screen.blit(particle_surf, (int(particle['x'] - size), int(particle['y'] - size)))

    def draw_hud(self, screen, is_showing_all, current_time):
        score_text = self.font_medium.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (10, 10))

        moves_text = self.font_medium.render(f"Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (10, 50))

        matches_text = self.font_medium.render(f"Matches: {self.matches_found}/{self.total_pairs}", True, self.WHITE)
        screen.blit(matches_text, (self.width - 200, 10))

        if is_showing_all:
            remaining_time = max(0, self.show_all_time_duration - (current_time - self.show_all_start_time))
            time_text = self.font_medium.render(f"Memorize: {remaining_time:.1f}s", True, self.YELLOW)
            screen.blit(time_text, (self.width // 2 - 100, 10))

    def draw_menu(self, screen):
        title_text = self.font_large.render("Memory Match", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))

        for i, option in enumerate(self.menu_options):
            color = self.YELLOW if i == self.menu_selected_option else self.WHITE
            option_text = self.font_medium.render(option, True, color)
            y_pos = 250 + i * 60
            screen.blit(option_text, (self.width // 2 - option_text.get_width() // 2, y_pos))

        instruction_text = self.font_small.render("Use arrow keys to navigate, A to select", True, self.GRAY)
        screen.blit(instruction_text, (self.width // 2 - instruction_text.get_width() // 2, self.height - 100))

    def draw_game_over_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title_text = self.font_large.render("Congratulations!", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 100))

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, self.height // 2 - 50))

        moves_text = self.font_medium.render(f"Total Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width // 2 - moves_text.get_width() // 2, self.height // 2))

        continue_text = self.font_small.render("Press A to return to menu", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 100))

    def draw_pause_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("Paused", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2))

    def cleanup(self):
        pass

# Test code
if __name__ == "__main__":
    try:
        pygame.init()
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Memory Match Game Test")

        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None):
                print(f"Buzzer: freq={frequency}, dur={duration}")

        game = MemoryMatchGame(screen_width, screen_height, buzzer=MockBuzzer())

        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }

        running = True
        clock = pygame.time.Clock()

        while running:
            controller_input = {key: False for key in key_mapping.values()}

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True

            result = game.update(controller_input)
            if result and result.get("quit"):
                running = False

            game.render(screen)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()