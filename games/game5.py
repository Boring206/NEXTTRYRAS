#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game5.py - Memory Match Game Implementation

import random
import pygame
import time
import math
from pygame.locals import *

class MemoryMatchGame:
    """Memory Match Game Class"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width
        self.height = height
        self.buzzer = buzzer
        
        # Color definitions
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (255, 0, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.PINK = (255, 192, 203)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        
        # Game settings
        self.grid_cols = 4
        self.grid_rows = 4
        self.total_pairs = (self.grid_cols * self.grid_rows) // 2
        
        # Card colors
        self.card_colors = [
            self.RED, self.GREEN, self.BLUE, self.YELLOW,
            self.PURPLE, self.CYAN, self.ORANGE, self.PINK
        ]
        
        # Card size
        self.card_width = (width - 100) // self.grid_cols - 10
        self.card_height = (height - 200) // self.grid_rows - 10
        self.card_margin = 5
        
        # Game state
        self.reset_game()
        
    def reset_game(self):
        """Reset game state"""
        # Create card pairs
        self.cards = []
        colors = self.card_colors[:self.total_pairs] * 2  # Two of each color
        random.shuffle(colors)
        
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                index = row * self.grid_cols + col
                card = {
                    'row': row,
                    'col': col,
                    'color': colors[index],
                    'revealed': False,
                    'matched': False,
                    'flipping': False,
                    'flip_start_time': 0
                }
                self.cards.append(card)
        
        # Cursor position
        self.cursor_row = 0
        self.cursor_col = 0
        
        # Game logic
        self.revealed_cards = []
        self.matches_found = 0
        self.moves = 0
        self.score = 0
        self.start_time = time.time()
        
        # State
        self.game_over = False
        self.paused = False
        self.show_all_time = 3.0  # Time to show all cards at start
        self.show_all_start = time.time()
        
        # Input control
        self.last_input_time = 0
        self.input_delay = 0.3
        self.flip_animation_duration = 0.5
        
        # Effects
        self.particles = []
        self.match_effect_timer = 0
        
    def get_card_at(self, row, col):
        """Get the card at the specified position"""
        for card in self.cards:
            if card['row'] == row and card['col'] == col:
                return card
        return None
    
    def get_card_rect(self, card):
        """Get the rectangle for drawing the card"""
        x = 50 + card['col'] * (self.card_width + self.card_margin * 2)
        y = 100 + card['row'] * (self.card_height + self.card_margin * 2)
        return pygame.Rect(x, y, self.card_width, self.card_height)
    
    def flip_card(self, row, col):
        """Flip the card"""
        if len(self.revealed_cards) >= 2:
            return False
            
        card = self.get_card_at(row, col)
        if not card or card['revealed'] or card['matched']:
            return False
        
        # Start flip animation
        card['flipping'] = True
        card['flip_start_time'] = time.time()
        card['revealed'] = True
        self.revealed_cards.append(card)
        
        # Sound effect
        if self.buzzer:
            self.buzzer.play_tone(frequency=600, duration=0.2)
        
        self.moves += 1
        return True
    
    def check_match(self):
        """Check for a match"""
        if len(self.revealed_cards) == 2:
            card1, card2 = self.revealed_cards
            
            if card1['color'] == card2['color']:
                # Successful match
                card1['matched'] = True
                card2['matched'] = True
                self.matches_found += 1
                self.score += 100 - self.moves * 2  # Bonus points
                
                # Create match effect
                self.create_match_particles(card1)
                self.create_match_particles(card2)
                self.match_effect_timer = 1.0
                
                # Sound effect
                if self.buzzer:
                    self.buzzer.play_tone(frequency=800, duration=0.3)
                
                # Check if game is complete
                if self.matches_found == self.total_pairs:
                    self.game_over = True
                    elapsed_time = time.time() - self.start_time
                    time_bonus = max(0, 300 - int(elapsed_time))
                    self.score += time_bonus
                    
                    if self.buzzer:
                        self.buzzer.play_win_melody()
            else:
                # Unsuccessful match, flip back after delay
                self.flip_back_timer = time.time()
                
                # Sound effect
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
            
            # Clear revealed cards list (successful matches stay revealed)
            self.revealed_cards = []
    
    def create_match_particles(self, card):
        """Create particle effect for successful match"""
        rect = self.get_card_rect(card)
        center_x = rect.centerx
        center_y = rect.centery
        
        for _ in range(10):
            particle = {
                'x': center_x,
                'y': center_y,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-100, 100),
                'life': 1.0,
                'color': card['color'],
                'size': random.uniform(3, 8)
            }
            self.particles.append(particle)
    
    def update_particles(self, delta_time):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time
            particle['vy'] += 200 * delta_time  # Gravity
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update(self, controller_input=None):
        """Update game state"""
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # Show all cards at start
        if current_time - self.show_all_start < self.show_all_time:
            return {"game_over": False}
        
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "score": self.score}
        
        # Update effects
        self.update_particles(delta_time)
        if self.match_effect_timer > 0:
            self.match_effect_timer -= delta_time
        
        # Handle flipping back cards
        if hasattr(self, 'flip_back_timer'):
            if current_time - self.flip_back_timer > 1.0:
                for card in self.cards:
                    if card['revealed'] and not card['matched']:
                        card['revealed'] = False
                        card['flipping'] = False
                delattr(self, 'flip_back_timer')
        
        # Handle input
        if controller_input and current_time - self.last_input_time >= self.input_delay:
            moved = False
            
            if controller_input.get("up_pressed") and self.cursor_row > 0:
                self.cursor_row -= 1
                moved = True
            elif controller_input.get("down_pressed") and self.cursor_row < self.grid_rows - 1:
                self.cursor_row += 1
                moved = True
            elif controller_input.get("left_pressed") and self.cursor_col > 0:
                self.cursor_col -= 1
                moved = True
            elif controller_input.get("right_pressed") and self.cursor_col < self.grid_cols - 1:
                self.cursor_col += 1
                moved = True
            elif controller_input.get("a_pressed"):
                if len(self.revealed_cards) < 2:
                    self.flip_card(self.cursor_row, self.cursor_col)
                    moved = True
            elif controller_input.get("start_pressed"):
                self.paused = True
                moved = True
            
            if moved:
                self.last_input_time = current_time
                if self.buzzer and not controller_input.get("a_pressed"):
                    self.buzzer.play_tone(frequency=300, duration=0.1)
        
        # Check for match
        if len(self.revealed_cards) == 2 and not hasattr(self, 'flip_back_timer'):
            self.check_match()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """Render game screen"""
        screen.fill(self.BLACK)
        
        current_time = time.time()
        show_all = current_time - self.show_all_start < self.show_all_time
        
        # Draw title
        font_large = pygame.font.Font(None, 48)
        title_text = font_large.render("Memory Match", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 20))
        
        # Draw cards
        for card in self.cards:
            rect = self.get_card_rect(card)
            
            # Determine whether to show card content
            show_content = (show_all or card['revealed'] or card['matched'])
            
            # Background
            if show_content:
                pygame.draw.rect(screen, card['color'], rect)
                pygame.draw.rect(screen, self.WHITE, rect, 3)
            else:
                pygame.draw.rect(screen, self.DARK_GRAY, rect)
                pygame.draw.rect(screen, self.GRAY, rect, 3)
            
            # Match success effect
            if card['matched'] and self.match_effect_timer > 0:
                alpha = int(self.match_effect_timer * 255)
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, alpha))
                screen.blit(overlay, rect.topleft)
            
            # Cursor
            if card['row'] == self.cursor_row and card['col'] == self.cursor_col:
                pygame.draw.rect(screen, self.YELLOW, rect, 5)
        
        # Draw particle effects
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                size = max(1, int(particle['size'] * particle['life']))
                color = (*particle['color'], alpha)
                
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color, (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))
        
        # Draw game info
        font_medium = pygame.font.Font(None, 36)
        
        # Score and statistics
        info_y = self.height - 80
        score_text = font_medium.render(f"Score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (50, info_y))
        
        moves_text = font_medium.render(f"Moves: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (250, info_y))
        
        pairs_text = font_medium.render(f"Pairs: {self.matches_found}/{self.total_pairs}", True, self.WHITE)
        screen.blit(pairs_text, (450, info_y))
        
        # Time
        if not self.game_over:
            elapsed = int(time.time() - self.start_time)
            time_text = font_medium.render(f"Time: {elapsed}s", True, self.WHITE)
            screen.blit(time_text, (650, info_y))
        
        # Start hint
        if show_all:
            countdown = int(self.show_all_time - (current_time - self.show_all_start))
            if countdown > 0:
                font_countdown = pygame.font.Font(None, 72)
                countdown_text = font_countdown.render(f"Remember positions: {countdown}", True, self.YELLOW)
                screen.blit(countdown_text, (self.width // 2 - countdown_text.get_width() // 2, self.height // 2 - 50))
        
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
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Title
        title_text = font_large.render("Congratulations!", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 100))
        
        # Statistics
        elapsed_time = int(time.time() - self.start_time)
        stats = [
            f"Final Score: {self.score}",
            f"Completion Time: {elapsed_time} seconds",
            f"Total Moves: {self.moves}",
            f"Average per Pair: {self.moves / self.total_pairs:.1f} moves"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = font_medium.render(stat, True, self.WHITE)
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2, 
                                  self.height // 2 - 30 + i * 40))
        
        # Restart hint
        restart_text = font_medium.render("Press Start to Restart", True, self.YELLOW)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                 self.height // 2 + 120))
    
    def draw_pause(self, screen):
        """Draw pause screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        pause_text = font_large.render("Paused", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))
        
        font_medium = pygame.font.Font(None, 36)
        continue_text = font_medium.render("Press Start to Continue", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 10))
    
    def cleanup(self):
        """Clean up game resources"""
        pass

# 測試代碼
if __name__ == "__main__":
    try:
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Memory Match Game Test")
        
        game = MemoryMatchGame(800, 600)
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
                "start_pressed": keys[pygame.K_RETURN]
            }
            
            game.update(controller_input)
            game.render(screen)
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()
