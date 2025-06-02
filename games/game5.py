#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game5.py - 記憶翻牌遊戲實現

import random
import pygame
import time
import math
from pygame.locals import *

class MemoryMatchGame:
    """記憶翻牌遊戲類"""
    
    def __init__(self, width=800, height=600, buzzer=None):
        self.width = width
        self.height = height
        self.buzzer = buzzer
        
        # 顏色定義
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
        
        # 遊戲設定
        self.grid_cols = 4
        self.grid_rows = 4
        self.total_pairs = (self.grid_cols * self.grid_rows) // 2
        
        # 卡片顏色
        self.card_colors = [
            self.RED, self.GREEN, self.BLUE, self.YELLOW,
            self.PURPLE, self.CYAN, self.ORANGE, self.PINK
        ]
        
        # 卡片尺寸
        self.card_width = (width - 100) // self.grid_cols - 10
        self.card_height = (height - 200) // self.grid_rows - 10
        self.card_margin = 5
        
        # 遊戲狀態
        self.reset_game()
        
    def reset_game(self):
        """重置遊戲狀態"""
        # 創建卡片配對
        self.cards = []
        colors = self.card_colors[:self.total_pairs] * 2  # 每種顏色兩張
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
        
        # 游標位置
        self.cursor_row = 0
        self.cursor_col = 0
        
        # 遊戲邏輯
        self.revealed_cards = []
        self.matches_found = 0
        self.moves = 0
        self.score = 0
        self.start_time = time.time()
        
        # 狀態
        self.game_over = False
        self.paused = False
        self.show_all_time = 3.0  # 開始時顯示所有卡片的時間
        self.show_all_start = time.time()
        
        # 輸入控制
        self.last_input_time = 0
        self.input_delay = 0.3
        self.flip_animation_duration = 0.5
        
        # 特效
        self.particles = []
        self.match_effect_timer = 0
        
    def get_card_at(self, row, col):
        """獲取指定位置的卡片"""
        for card in self.cards:
            if card['row'] == row and card['col'] == col:
                return card
        return None
    
    def get_card_rect(self, card):
        """獲取卡片的繪製矩形"""
        x = 50 + card['col'] * (self.card_width + self.card_margin * 2)
        y = 100 + card['row'] * (self.card_height + self.card_margin * 2)
        return pygame.Rect(x, y, self.card_width, self.card_height)
    
    def flip_card(self, row, col):
        """翻轉卡片"""
        if len(self.revealed_cards) >= 2:
            return False
            
        card = self.get_card_at(row, col)
        if not card or card['revealed'] or card['matched']:
            return False
        
        # 開始翻轉動畫
        card['flipping'] = True
        card['flip_start_time'] = time.time()
        card['revealed'] = True
        self.revealed_cards.append(card)
        
        # 音效
        if self.buzzer:
            self.buzzer.play_tone(frequency=600, duration=0.2)
        
        self.moves += 1
        return True
    
    def check_match(self):
        """檢查配對"""
        if len(self.revealed_cards) == 2:
            card1, card2 = self.revealed_cards
            
            if card1['color'] == card2['color']:
                # 配對成功
                card1['matched'] = True
                card2['matched'] = True
                self.matches_found += 1
                self.score += 100 - self.moves * 2  # 獎勵分數
                
                # 創建配對特效
                self.create_match_particles(card1)
                self.create_match_particles(card2)
                self.match_effect_timer = 1.0
                
                # 音效
                if self.buzzer:
                    self.buzzer.play_tone(frequency=800, duration=0.3)
                
                # 檢查遊戲是否完成
                if self.matches_found == self.total_pairs:
                    self.game_over = True
                    elapsed_time = time.time() - self.start_time
                    time_bonus = max(0, 300 - int(elapsed_time))
                    self.score += time_bonus
                    
                    if self.buzzer:
                        self.buzzer.play_win_melody()
            else:
                # 配對失敗，延遲後翻回去
                self.flip_back_timer = time.time()
                
                # 音效
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
            
            # 清空已翻開的卡片列表（成功配對的會保持翻開狀態)
            self.revealed_cards = []
    
    def create_match_particles(self, card):
        """創建配對成功的粒子特效"""
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
        """更新粒子效果"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time
            particle['vy'] += 200 * delta_time  # 重力
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update(self, controller_input=None):
        """更新遊戲狀態"""
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # 開始時顯示所有卡片
        if current_time - self.show_all_start < self.show_all_time:
            return {"game_over": False}
        
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "score": self.score}
        
        # 更新特效
        self.update_particles(delta_time)
        if self.match_effect_timer > 0:
            self.match_effect_timer -= delta_time
        
        # 處理翻回卡片
        if hasattr(self, 'flip_back_timer'):
            if current_time - self.flip_back_timer > 1.0:
                for card in self.cards:
                    if card['revealed'] and not card['matched']:
                        card['revealed'] = False
                        card['flipping'] = False
                delattr(self, 'flip_back_timer')
        
        # 處理輸入
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
        
        # 檢查配對
        if len(self.revealed_cards) == 2 and not hasattr(self, 'flip_back_timer'):
            self.check_match()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """渲染遊戲畫面"""
        screen.fill(self.BLACK)
        
        current_time = time.time()
        show_all = current_time - self.show_all_start < self.show_all_time
        
        # 繪製標題
        font_large = pygame.font.Font(None, 48)
        title_text = font_large.render("記憶翻牌", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 20))
        
        # 繪製卡片
        for card in self.cards:
            rect = self.get_card_rect(card)
            
            # 決定是否顯示卡片內容
            show_content = (show_all or card['revealed'] or card['matched'])
            
            # 背景
            if show_content:
                pygame.draw.rect(screen, card['color'], rect)
                pygame.draw.rect(screen, self.WHITE, rect, 3)
            else:
                pygame.draw.rect(screen, self.DARK_GRAY, rect)
                pygame.draw.rect(screen, self.GRAY, rect, 3)
            
            # 配對成功的特效
            if card['matched'] and self.match_effect_timer > 0:
                alpha = int(self.match_effect_timer * 255)
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, alpha))
                screen.blit(overlay, rect.topleft)
            
            # 游標
            if card['row'] == self.cursor_row and card['col'] == self.cursor_col:
                pygame.draw.rect(screen, self.YELLOW, rect, 5)
        
        # 繪製粒子效果
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                size = max(1, int(particle['size'] * particle['life']))
                color = (*particle['color'], alpha)
                
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color, (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))
        
        # 繪製遊戲資訊
        font_medium = pygame.font.Font(None, 36)
        
        # 分數和統計
        info_y = self.height - 80
        score_text = font_medium.render(f"分數: {self.score}", True, self.WHITE)
        screen.blit(score_text, (50, info_y))
        
        moves_text = font_medium.render(f"移動: {self.moves}", True, self.WHITE)
        screen.blit(moves_text, (250, info_y))
        
        pairs_text = font_medium.render(f"配對: {self.matches_found}/{self.total_pairs}", True, self.WHITE)
        screen.blit(pairs_text, (450, info_y))
        
        # 時間
        if not self.game_over:
            elapsed = int(time.time() - self.start_time)
            time_text = font_medium.render(f"時間: {elapsed}s", True, self.WHITE)
            screen.blit(time_text, (650, info_y))
        
        # 開始提示
        if show_all:
            countdown = int(self.show_all_time - (current_time - self.show_all_start))
            if countdown > 0:
                font_countdown = pygame.font.Font(None, 72)
                countdown_text = font_countdown.render(f"記住位置: {countdown}", True, self.YELLOW)
                screen.blit(countdown_text, (self.width // 2 - countdown_text.get_width() // 2, self.height // 2 - 50))
        
        # 遊戲結束畫面
        if self.game_over:
            self.draw_game_over(screen)
        elif self.paused:
            self.draw_pause(screen)
    
    def draw_game_over(self, screen):
        """繪製遊戲結束畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # 標題
        title_text = font_large.render("恭喜完成！", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 100))
        
        # 統計
        elapsed_time = int(time.time() - self.start_time)
        stats = [
            f"最終分數: {self.score}",
            f"完成時間: {elapsed_time} 秒",
            f"總移動數: {self.moves}",
            f"平均每對: {self.moves / self.total_pairs:.1f} 步"
        ]
        
        for i, stat in enumerate(stats):
            stat_text = font_medium.render(stat, True, self.WHITE)
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2, 
                                  self.height // 2 - 30 + i * 40))
        
        # 重新開始提示
        restart_text = font_medium.render("按 Start 重新開始", True, self.YELLOW)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                 self.height // 2 + 120))
    
    def draw_pause(self, screen):
        """繪製暫停畫面"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        pause_text = font_large.render("暫停", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))
        
        font_medium = pygame.font.Font(None, 36)
        continue_text = font_medium.render("按 Start 繼續", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 10))
    
    def cleanup(self):
        """清理遊戲資源"""
        pass

# 測試代碼
if __name__ == "__main__":
    try:
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("記憶翻牌遊戲測試")
        
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
        print(f"遊戲執行錯誤: {e}")
        pygame.quit()
