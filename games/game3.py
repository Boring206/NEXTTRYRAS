#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game3.py - Space Invaders Game Implementation

import random
import pygame
import time
from pygame.locals import *

class SpaceInvadersGame:
    """Space Invaders Game Class"""
    
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
        
        # Game element sizes
        self.player_width = 50
        self.player_height = 30
        self.enemy_width = 40
        self.enemy_height = 30
        self.bullet_width = 5
        self.bullet_height = 15
        self.enemy_bullet_width = 3
        self.enemy_bullet_height = 12
        
        # Game speed settings
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.player_speed = 5
        self.bullet_speed = 7
        self.enemy_speed_x = 2
        self.enemy_speed_y = 20
        self.enemy_bullet_speed = 4
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Player ship initial position
        self.player_x = (self.width - self.player_width) // 2
        self.player_y = self.height - 50
        
        # Bullet lists
        self.bullets = []
        self.enemy_bullets = []
        
        # Enemy ship lists
        self.enemies = []
        self.create_enemies()
        
        # Direction, controls enemy movement
        self.enemy_direction = 1
        
        # Shooting timer (limits shooting frequency)
        self.last_shot_time = 0
        self.shot_delay = 0.5  # Seconds between shots
        
        # Enemy shooting timer
        self.enemy_shot_timer = 0
        self.enemy_shot_interval = 60  # Frames
        
        # Current wave and score
        self.wave = 1
        self.score = 0
        self.lives = 3
        
        # Game state
        self.game_over = False
        self.paused = False
    
    def create_enemies(self):
        """Create enemy ship array"""
        rows = 5
        cols = 8
        
        for row in range(rows):
            for col in range(cols):
                x = col * (self.enemy_width + 10) + 50
                y = row * (self.enemy_height + 10) + 50
                
                # Enemy ship type/color based on row number
                enemy_type = min(row, 2)  # 0=simple, 1=medium, 2=hard
                
                self.enemies.append({
                    'x': x,
                    'y': y,
                    'type': enemy_type,
                    'health': enemy_type + 1  # Health: simple=1, medium=2, hard=3
                })
    
    def move_player(self, direction):
        """Move player ship"""
        if direction == "left":
            self.player_x = max(0, self.player_x - self.player_speed)
        elif direction == "right":
            self.player_x = min(self.width - self.player_width, self.player_x + self.player_speed)
    
    def shoot(self):
        """Player shooting"""
        current_time = time.time()
        if current_time - self.last_shot_time >= self.shot_delay:
            # Shoot bullet from the center of the ship
            bullet_x = self.player_x + (self.player_width // 2) - (self.bullet_width // 2)
            bullet_y = self.player_y
            
            self.bullets.append({
                'x': bullet_x,
                'y': bullet_y
            })
            
            self.last_shot_time = current_time
            
            # Play shooting sound effect
            if self.buzzer:
                self.buzzer.play_tone("select")
    
    def enemy_shoot(self):
        """Enemy shooting"""
        self.enemy_shot_timer += 1
        
        if self.enemy_shot_timer >= self.enemy_shot_interval:
            self.enemy_shot_timer = 0
            
            # Randomly select an enemy to shoot
            if self.enemies:
                shooter = random.choice(self.enemies)
                
                bullet_x = shooter['x'] + (self.enemy_width // 2) - (self.enemy_bullet_width // 2)
                bullet_y = shooter['y'] + self.enemy_height
                
                self.enemy_bullets.append({
                    'x': bullet_x,
                    'y': bullet_y
                })
    
    def move_bullets(self):
        """Move all bullets"""
        # Move player bullets (upward)
        for bullet in self.bullets[:]:
            bullet['y'] -= self.bullet_speed
            
            # Remove bullets that move off-screen
            if bullet['y'] < 0:
                self.bullets.remove(bullet)
        
        # Move enemy bullets (downward)
        for bullet in self.enemy_bullets[:]:
            bullet['y'] += self.enemy_bullet_speed
            
            # Remove bullets that move off-screen
            if bullet['y'] > self.height:
                self.enemy_bullets.remove(bullet)
    
    def move_enemies(self):
        """Move enemies"""
        change_direction = False
        
        # Check if any enemy has reached the edge
        for enemy in self.enemies:
            if (enemy['x'] + self.enemy_width >= self.width and self.enemy_direction > 0) or \
               (enemy['x'] <= 0 and self.enemy_direction < 0):
                change_direction = True
                break
        
        # Change direction and move down
        if change_direction:
            self.enemy_direction = -self.enemy_direction
            for enemy in self.enemies:
                enemy['y'] += self.enemy_speed_y
        else:
            # Normal left-right movement
            for enemy in self.enemies:
                enemy['x'] += self.enemy_speed_x * self.enemy_direction
        
        # Check if any enemy has reached the bottom (game over)
        for enemy in self.enemies:
            if enemy['y'] + self.enemy_height >= self.player_y:
                self.game_over = True
                if self.buzzer:
                    self.buzzer.play_game_over_melody()
                break
    
    def check_collisions(self):
        """Check collisions"""
        # Check player bullets vs enemies
        for bullet in self.bullets[:]:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.bullet_width, self.bullet_height)
            
            for enemy in self.enemies[:]:
                enemy_rect = pygame.Rect(enemy['x'], enemy['y'], self.enemy_width, self.enemy_height)
                
                if bullet_rect.colliderect(enemy_rect):
                    # Enemy hit
                    enemy['health'] -= 1
                    
                    # Remove hit bullet
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    
                    # Enemy defeated
                    if enemy['health'] <= 0:
                        self.enemies.remove(enemy)
                        self.score += (enemy['type'] + 1) * 10
                        
                        if self.buzzer:
                            self.buzzer.play_tone("score")
                    
                    break
        
        # Check enemy bullets vs player
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
        
        for bullet in self.enemy_bullets[:]:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.enemy_bullet_width, self.enemy_bullet_height)
            
            if bullet_rect.colliderect(player_rect):
                # Player hit
                self.lives -= 1
                self.enemy_bullets.remove(bullet)
                
                if self.buzzer:
                    self.buzzer.play_tone("error")
                
                if self.lives <= 0:
                    self.game_over = True
                    if self.buzzer:
                        self.buzzer.play_game_over_melody()
    
    def check_wave_complete(self):
        """Check if current wave is complete"""
        if not self.enemies:
            self.wave += 1
            self.create_enemies()
            
            # Increase enemy speed
            self.enemy_speed_x += 0.5
            
            # Decrease enemy shooting interval
            self.enemy_shot_interval = max(20, self.enemy_shot_interval - 5)
            
            if self.buzzer:
                self.buzzer.play_win_melody()
    
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
        
        current_time = time.time()
        
        # Handle input
        if controller_input:
            # Movement control (enhanced responsiveness)
            if controller_input.get("left_pressed"):
                self.move_player("left")
                if self.buzzer and current_time - getattr(self, 'last_move_sound', 0) > 0.1:
                    self.buzzer.play_tone(frequency=300, duration=0.05)
                    self.last_move_sound = current_time
                    
            if controller_input.get("right_pressed"):
                self.move_player("right")
                if self.buzzer and current_time - getattr(self, 'last_move_sound', 0) > 0.1:
                    self.buzzer.play_tone(frequency=300, duration=0.05)
                    self.last_move_sound = current_time
            
            # Shooting control (prevent too frequent shots)
            if controller_input.get("a_pressed"):
                if current_time - self.last_shot_time >= self.shot_cooldown:
                    self.shoot()
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=800, duration=0.1)
            
            # Pause control
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "score": self.score, "paused": self.paused}
        
        # Update game logic
        self.update_bullets()
        self.update_aliens()
        self.update_alien_bullets()
        self.check_collisions()
        
        # Check victory conditions
        if not self.aliens:
            self.spawn_new_wave()
            if self.buzzer:
                self.buzzer.play_victory_fanfare()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """
        Render game screen
        
        Parameters:
            screen: pygame screen object
        """
        # Clear screen
        screen.fill(self.BLACK)
        
        # Draw starry background
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            pygame.draw.circle(screen, self.WHITE, (x, y), 1)
        
        # Draw player ship
        player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
        pygame.draw.rect(screen, self.GREEN, player_rect)
        
        # Draw triangular ship shape
        pygame.draw.polygon(screen, self.GREEN, [
            (self.player_x, self.player_y + self.player_height),
            (self.player_x + self.player_width // 2, self.player_y),
            (self.player_x + self.player_width, self.player_y + self.player_height)
        ])
        
        # Draw player bullets
        for bullet in self.bullets:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.bullet_width, self.bullet_height)
            pygame.draw.rect(screen, self.BLUE, bullet_rect)
        
        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            bullet_rect = pygame.Rect(bullet['x'], bullet['y'], self.enemy_bullet_width, self.enemy_bullet_height)
            pygame.draw.rect(screen, self.RED, bullet_rect)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy_rect = pygame.Rect(enemy['x'], enemy['y'], self.enemy_width, self.enemy_height)
            
            # Set color based on enemy type
            if enemy['type'] == 0:
                color = self.GREEN
            elif enemy['type'] == 1:
                color = self.YELLOW
            else:
                color = self.RED
            
            pygame.draw.rect(screen, color, enemy_rect)
        
        # Draw score, wave and lives
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, self.WHITE)
        wave_text = font.render(f"Wave: {self.wave}", True, self.WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, self.WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(wave_text, (10, 50))
        screen.blit(lives_text, (self.width - 150, 10))
        
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
        
        restart_text = font.render("Press Start to Restart", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height // 2 + 50))
    
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
        """清理遊戲資源"""
        # 目前無需特殊清理，但保留此方法以便未來擴充
        pass

# 若獨立執行此腳本，用於測試
if __name__ == "__main__":
    try:
        # 初始化 pygame
        pygame.init()
        
        # 設置視窗
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Space Invaders Game Test")
        
        # 建立遊戲實例
        game = SpaceInvadersGame(screen_width, screen_height)
        
        # 模擬控制器輸入的鍵盤映射
        key_mapping = {
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_RETURN: "start_pressed"
        }
        
        # 遊戲主迴圈
        running = True
        while running:
            # 處理事件
            controller_input = {key: False for key in key_mapping.values()}
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # 獲取當前按下的按鍵狀態
            keys = pygame.key.get_pressed()
            for key, input_name in key_mapping.items():
                if keys[key]:
                    controller_input[input_name] = True
            
            # 更新遊戲
            game.update(controller_input)
            
            # 渲染
            game.render(screen)
            pygame.display.flip()
            
            # 控制幀率
            pygame.time.Clock().tick(60)
        
        # 退出 pygame
        pygame.quit()
    
    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()
