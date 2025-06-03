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
        self.PURPLE = (128, 0, 128) # Adjusted Purple for better visibility
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
        else:
            print("External buzzer object provided.")

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

        available_width = self.width - (2 * side_padding) - (self.grid_cols -1) * self.card_margin * 2
        available_height = self.height - top_hud_height - bottom_hud_height - (self.grid_rows -1) * self.card_margin * 2
        
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

        card['flipping'] = True
        card['flip_start_time'] = time.time()
        card['flip_progress'] = 0 # Reset progress

        # revealed will be set to True mid-animation or after
        self.revealed_cards.append(card)

        self._play_sound(self.sound_flip, frequency=600, duration=0.1)
        self.moves += 1
        return True

    def check_match(self):
        if len(self.revealed_cards) == 2:
            card1, card2 = self.revealed_cards

            # Ensure flipping animation is complete for both before checking
            if card1['flipping'] or card2['flipping']:
                return

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
            # Don't clear revealed_cards immediately for no-match, do it after flip_back_timer

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

        if events is None: events = []

        # Handle mouse clicks for menu and game
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.handle_click(event.pos)


        # --- Game State Logic ---
        if self.game_state == self.MENU:
            if controller_input and current_time - self.last_input_time >= self.input_delay:
                moved = False
                if controller_input.get("up_pressed"):
                    self.menu_selected_option = (self.menu_selected_option - 1) % len(self.menu_options)
                    self._play_sound(self.sound_select, frequency=400, duration=0.05)
                    moved = True
                elif controller_input.get("down_pressed"):
                    self.menu_selected_option = (self.menu_selected_option + 1) % len(self.menu_options)
                    self._play_sound(self.sound_select, frequency=400, duration=0.05)
                    moved = True
                elif controller_input.get("a_pressed") or controller_input.get("start_pressed"): # 'a' or 'enter'
                    action_result = self._process_menu_selection()
                    if action_result.get("action") == "quit":
                        return {"game_over": True, "quit_game": True} # Special signal
                    moved = True
                if moved:
                    self.last_input_time = current_time
            return {"game_over": False}


        elif self.game_state == self.SHOWING_CARDS:
            if current_time - self.show_all_start_time >= self.show_all_time_duration:
                self.game_state = self.PLAYING
                self.start_time = time.time() # Actual game start time
            return {"game_over": False}


        elif self.game_state == self.GAME_OVER:
            if controller_input and controller_input.get("start_pressed") and \
               current_time - self.last_input_time >= self.input_delay:
                self.game_state = self.MENU # Go back to menu
                self.last_input_time = current_time
            return {"game_over": True, "score": self.score} # game_over_flag is true

        elif self.game_state == self.PAUSED:
            if controller_input and controller_input.get("start_pressed") and \
               current_time - self.last_input_time >= self.input_delay:
                self.paused_flag = False
                self.game_state = self.PLAYING
                self.last_input_time = current_time
                # Adjust start_time if pausing should stop the timer
                self.start_time += (time.time() - self._pause_time_start) # Add paused duration back
            return {"game_over": self.game_over_flag}


        elif self.game_state == self.PLAYING:
            # Update card flip animations
            for card in self.cards:
                if card['flipping']:
                    progress = (current_time - card['flip_start_time']) / self.flip_animation_duration
                    card['flip_progress'] = min(1, progress)
                    if progress >= 0.5 and not card['revealed']: # Mid-point of animation
                        card['revealed'] = True # Now show the color
                    if progress >= 1:
                        card['flipping'] = False
                        card['flip_progress'] = 1 # Ensure it's fully revealed graphically

            self.update_particles(delta_time)
            if self.match_effect_timer > 0:
                self.match_effect_timer -= delta_time

            # Handle flipping back non-matched cards
            if self.flip_back_active:
                if current_time - self.flip_back_timer_start > 0.8: # Slightly shorter delay
                    for card_to_hide in self.revealed_cards: # revealed_cards still holds the two non-matching cards
                        if not card_to_hide['matched']: # Should always be true here
                            card_to_hide['revealed'] = False
                            card_to_hide['flipping'] = True # Start flip back animation
                            card_to_hide['flip_start_time'] = time.time()
                            card_to_hide['flip_progress'] = 0
                    self.revealed_cards = [] # Now clear them
                    self.flip_back_active = False
            
            # Process keyboard input for game play
            if controller_input and current_time - self.last_input_time >= self.input_delay:
                moved = False
                prev_cursor_row, prev_cursor_col = self.cursor_row, self.cursor_col

                if controller_input.get("up_pressed"):
                    self.cursor_row = max(0, self.cursor_row - 1)
                    moved = True
                elif controller_input.get("down_pressed"):
                    self.cursor_row = min(self.grid_rows - 1, self.cursor_row + 1)
                    moved = True
                elif controller_input.get("left_pressed"):
                    self.cursor_col = max(0, self.cursor_col - 1)
                    moved = True
                elif controller_input.get("right_pressed"):
                    self.cursor_col = min(self.grid_cols - 1, self.cursor_col + 1)
                    moved = True
                elif controller_input.get("a_pressed"):
                    if not self.flip_back_active: # Don't allow flip if cards are about to flip back
                         self.attempt_flip_card(self.cursor_row, self.cursor_col)
                    moved = True # Counts as an action
                elif controller_input.get("start_pressed"):
                    self.paused_flag = True
                    self.game_state = self.PAUSED
                    self._pause_time_start = time.time() # Record when pause starts
                    moved = True

                if moved:
                    self.last_input_time = current_time
                    if (self.cursor_row != prev_cursor_row or self.cursor_col != prev_cursor_col) and \
                       not controller_input.get("a_pressed"): # Play sound only for cursor move
                        self._play_sound(self.sound_select, frequency=300, duration=0.05)


            # Check for match if two cards are revealed and not flipping back
            if len(self.revealed_cards) == 2 and not self.flip_back_active:
                # Ensure both cards have finished their primary flip animation
                card1, card2 = self.revealed_cards
                if not card1['flipping'] and not card2['flipping']:
                    self.check_match()
            
            return {"game_over": self.game_over_flag, "score": self.score}

        return {"game_over": self.game_over_flag}


    def render(self, screen):
        screen.fill(self.BLACK)
        current_time = time.time()

        if self.game_state == self.MENU:
            self.draw_menu(screen)
            return

        # Draw title
        title_text = self.font_large.render("Memory Match", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 20))

        # Draw cards
        is_showing_all = (self.game_state == self.SHOWING_CARDS)

        for card in self.cards:
            rect = self.get_card_rect(card)
            card_center_x, card_center_y = rect.centerx, rect.centery

            # Card flipping animation
            if card['flipping']:
                progress = card['flip_progress'] # Already calculated in update
                # Phase 1: Shrinking (0 to 0.5 progress) -> show back
                # Phase 2: Expanding (0.5 to 1 progress) -> show front (color)
                
                if progress < 0.5: # Shrinking, show back
                    current_width = self.card_width * (1 - (progress * 2))
                    display_color = self.DARK_GRAY
                    border_color = self.GRAY
                else: # Expanding, show front (color)
                    current_width = self.card_width * ((progress - 0.5) * 2)
                    display_color = card['color']
                    border_color = self.WHITE
                
                current_height = self.card_height # Height doesn't change in this simple animation
                
                animated_rect = pygame.Rect(
                    card_center_x - current_width / 2,
                    rect.y,
                    current_width,
                    current_height
                )
                pygame.draw.rect(screen, display_color, animated_rect)
                pygame.draw.rect(screen, border_color, animated_rect, 3)

            else: # Not flipping, normal draw
                show_content = (is_showing_all or card['revealed'] or card['matched'])
                if show_content:
                    pygame.draw.rect(screen, card['color'], rect)
                    pygame.draw.rect(screen, self.WHITE, rect, 3)
                else:
                    pygame.draw.rect(screen, self.DARK_GRAY, rect)
                    pygame.draw.rect(screen, self.GRAY, rect, 3)

            # Match success visual effect (glow)
            if card['matched'] and self.match_effect_timer > 0:
                alpha = int(max(0, min(1, self.match_effect_timer / 1.0)) * 100) # Fades out
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((255, 255, 100, alpha)) # Yellowish glow
                screen.blit(overlay, rect.topleft)

            # Cursor
            if self.game_state == self.PLAYING and \
               not is_showing_all and \
               card['row'] == self.cursor_row and card['col'] == self.cursor_col:
                pygame.draw.rect(screen, self.YELLOW, rect, 5) # Thicker cursor

        # Draw particle effects
        self.draw_particles(screen)

        # Draw game info HUD
        self.draw_hud(screen, is_showing_all, current_time)

        # Overlays for Pause/Game Over
        if self.game_state == self.GAME_OVER: # Uses game_over_flag
            self.draw_game_over_screen(screen)
        elif self.game_state == self.PAUSED: # Uses paused_flag
            self.draw_pause_screen(screen)


    def draw_particles(self, screen):
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                size = max(1, int(particle['size'] * (particle['life']**0.5))) # Size shrinks less linearly
                
                # Create a surface for each particle to handle per-pixel alpha correctly
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, (*particle['color'], alpha), (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))

    def draw_hud(self, screen, is_showing_all, current_time):
        info_y = self.height - 60 # Adjusted Y for HUD
        
        score_text = self.font_small.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (50, info_y))

        moves_text = self.font_small.render(f"Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (self.width // 2 - moves_text.get_width()//2 - 100, info_y))

        pairs_text = self.font_small.render(f"Pairs: {self.matches_found}/{self.total_pairs}", True, self.WHITE)
        screen.blit(pairs_text, (self.width // 2 + 50, info_y))

        if self.game_state != self.GAME_OVER and self.game_state != self.SHOWING_CARDS and self.game_state != self.MENU:
            elapsed = int(current_time - self.start_time) if self.start_time > 0 else 0
            time_text_val = self.font_small.render(f"Time: {elapsed}s", True, self.WHITE)
            screen.blit(time_text_val, (self.width - time_text_val.get_width() - 50, info_y))

        if is_showing_all:
            countdown = int(self.show_all_time_duration - (current_time - self.show_all_start_time))
            if countdown > 0:
                countdown_text_render = self.font_large.render(f"Remember: {countdown}", True, self.YELLOW)
                screen.blit(countdown_text_render, (self.width // 2 - countdown_text_render.get_width() // 2, self.height // 2 - 50))

    def draw_menu(self, screen):
        screen.fill(self.DARK_GRAY) # Menu background
        title_text = self.font_large.render("Memory Match", True, self.GOLD)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 4))

        menu_item_height = 60
        base_y = self.height // 2 - (len(self.menu_options) * menu_item_height) // 2 + 50

        for i, option_text in enumerate(self.menu_options):
            color = self.YELLOW if i == self.menu_selected_option else self.WHITE
            text_render = self.font_medium.render(option_text, True, color)
            text_rect = text_render.get_rect(center=(self.width // 2, base_y + i * menu_item_height))
            screen.blit(text_render, text_rect)
        
        instructions_font = pygame.font.Font(None, 28)
        inst1 = instructions_font.render("Use UP/DOWN keys to navigate, ENTER or A to select.", True, self.GRAY)
        inst2 = instructions_font.render("Or click to select.", True, self.GRAY)
        screen.blit(inst1, (self.width//2 - inst1.get_width()//2, base_y + len(self.menu_options) * menu_item_height + 20))
        screen.blit(inst2, (self.width//2 - inst2.get_width()//2, base_y + len(self.menu_options) * menu_item_height + 20 + inst1.get_height() + 5))


    def draw_game_over_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Darker overlay
        screen.blit(overlay, (0, 0))

        title_text = self.font_large.render("Congratulations!", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 150))

        elapsed_time = int(time.time() - self.start_time) if self.start_time > 0 else 0
        avg_moves = f"{self.moves / self.total_pairs:.1f}" if self.total_pairs > 0 else "N/A"
        stats = [
            f"Final Score: {self.score}",
            f"Time: {elapsed_time} seconds",
            f"Moves: {self.moves}",
            f"Avg Moves/Pair: {avg_moves}"
        ]

        for i, stat in enumerate(stats):
            stat_text = self.font_small.render(stat, True, self.WHITE) # Smaller font for stats
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2,
                                     self.height // 2 - 60 + i * 35))

        restart_text = self.font_medium.render("Press Start to Return to Menu", True, self.YELLOW)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2,
                                     self.height // 2 + 80))

    def draw_pause_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pause_text = self.font_large.render("Paused", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))

        continue_text = self.font_medium.render("Press Start to Continue", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 20))

    def cleanup(self):
        if self._internal_buzzer_active:
            pygame.mixer.quit()
        print("Game cleanup called.")


# Test code
if __name__ == "__main__":
    try:
        pygame.init()
        pygame.font.init() # Ensure font module is initialized

        SCREEN_WIDTH = 800
        SCREEN_HEIGHT = 600
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Memory Match Game Enhanced")

        game = MemoryMatchGame(SCREEN_WIDTH, SCREEN_HEIGHT)
        clock = pygame.time.Clock()

        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            keys = pygame.key.get_pressed()
            controller_input = {
                "up_pressed": keys[pygame.K_UP],
                "down_pressed": keys[pygame.K_DOWN],
                "left_pressed": keys[pygame.K_LEFT],
                "right_pressed": keys[pygame.K_RIGHT],
                "a_pressed": keys[pygame.K_a] or keys[pygame.K_SPACE], # A or Space to select/flip
                "start_pressed": keys[pygame.K_RETURN] # Enter key
            }

            game_status = game.update(controller_input, events) # Pass events for mouse clicks

            if game_status.get("quit_game"): # Check for quit signal from menu
                running = False

            game.render(screen)
            pygame.display.flip()
            clock.tick(60) # Target 60 FPS

        game.cleanup()
        pygame.quit()

    except Exception as e:
        print(f"Game execution error: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()