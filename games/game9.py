#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game9.py - Enhanced Reaction Test Game Implementation

import random
import pygame
import time
import math
from pygame.locals import *

class ReactionTestGame:
    """Enhanced Reaction Test Game Class"""
    
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
        self.PURPLE = (255, 0, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.DARK_GREEN = (0, 128, 0)
        self.GRAY = (128, 128, 128)
        
        # Game parameters
        self.trials = 10           # Number of trials
        self.min_wait_time = 1.0   # Minimum wait time
        self.max_wait_time = 5.0   # Maximum wait time
        self.signal_duration = 2.0 # Signal display time
        
        # Test modes
        self.test_modes = [
            {
                'name': 'Visual Reaction',
                'description': 'Press A when you see green signal',
                'type': 'visual',
                'signal_color': self.GREEN,
                'background_color': self.BLACK
            },
            {
                'name': 'Color Recognition',
                'description': 'React only to green signals',
                'type': 'color_recognition',
                'signal_color': self.GREEN,
                'distractor_colors': [self.RED, self.BLUE, self.YELLOW],
                'background_color': self.BLACK
            },
            {
                'name': 'Position Reaction',
                'description': 'Signal appears in different positions',
                'type': 'position',
                'signal_color': self.GREEN,
                'background_color': self.BLACK
            },
            {
                'name': 'Audio-Visual Reaction',
                'description': 'Both sound and visual signal',
                'type': 'audio_visual',
                'signal_color': self.CYAN,
                'background_color': self.BLACK
            },
            {
                'name': 'Continuous Reaction',
                'description': 'Rapid consecutive signal test',
                'type': 'continuous',
                'signal_color': self.YELLOW,
                'background_color': self.BLACK
            }
        ]
        
        # Initialize game state
        self.reset_game()
    
    def reset_game(self):
        """Reset game state"""
        # Game status
        self.game_over = False
        self.paused = False
        self.current_mode_index = 0
        self.current_trial = 0
        
        # Test data
        self.reaction_times = []
        self.false_starts = 0     # False start count
        self.missed_signals = 0   # Missed signals count
        self.correct_responses = 0 # Correct response count
        
        # State control
        self.state = 'menu'  # menu, instructions, waiting, signal, result, game_over
        self.signal_start_time = 0
        self.wait_start_time = 0
        self.signal_position = (self.width // 2, self.height // 2)
        self.current_signal_color = self.GREEN
        self.is_distractor = False
        
        # Continuous mode special variables
        self.continuous_signals = []
        self.continuous_responses = []
        
        # Animation effects
        self.signal_pulse = 0
        self.background_flash = 0
        self.particles = []
        
        # Statistical analysis
        self.session_start_time = time.time()
    
    def get_current_mode(self):
        """Get current test mode"""
        return self.test_modes[self.current_mode_index]
    
    def start_test(self):
        """Start test"""
        self.state = 'instructions'
        if self.buzzer:
            self.buzzer.play_tone(frequency=800, duration=0.3)
    
    def next_trial(self):
        """Enter next trial"""
        if self.current_trial >= self.trials:
            self.finish_mode()
            return
        
        self.state = 'waiting'
        self.wait_start_time = time.time()
        
        # Set wait time based on mode
        mode = self.get_current_mode()
        if mode['type'] == 'continuous':
            self.wait_time = random.uniform(0.5, 1.5)
        else:
            self.wait_time = random.uniform(self.min_wait_time, self.max_wait_time)
        
        # Set signal position (position reaction mode)
        if mode['type'] == 'position':
            margin = 100
            self.signal_position = (
                random.randint(margin, self.width - margin),
                random.randint(margin, self.height - margin)
            )
        else:
            self.signal_position = (self.width // 2, self.height // 2)
        
        # Set signal color (color recognition mode)
        if mode['type'] == 'color_recognition':
            if random.random() < 0.7:
                self.current_signal_color = mode['signal_color']
                self.is_distractor = False
            else:
                self.current_signal_color = random.choice(mode['distractor_colors'])
                self.is_distractor = True
        else:
            self.current_signal_color = mode['signal_color']
            self.is_distractor = False
    
    def show_signal(self):
        """Display signal"""
        self.state = 'signal'
        self.signal_start_time = time.time()
        self.signal_pulse = 0
        
        # Play audio (audio-visual reaction mode)
        mode = self.get_current_mode()
        if mode['type'] == 'audio_visual' and self.buzzer:
            self.buzzer.play_tone(frequency=800, duration=0.5)
        
        # Create visual effects
        self.create_signal_particles()
    
    def create_signal_particles(self):
        """Create signal particle effects"""
        for _ in range(8):
            particle = {
                'x': self.signal_position[0],
                'y': self.signal_position[1],
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-100, 100),
                'life': 1.0,
                'color': self.current_signal_color,
                'size': random.uniform(3, 8)
            }
            self.particles.append(particle)
    
    def handle_response(self):
        """Handle player response"""
        current_time = time.time()
        
        if self.state == 'waiting':
            # False start
            self.false_starts += 1
            self.background_flash = 10
            if self.buzzer:
                self.buzzer.play_tone(frequency=300, duration=0.5)
            self.next_trial()
            
        elif self.state == 'signal':
            # Correct timing response
            mode = self.get_current_mode()
            
            if mode['type'] == 'color_recognition' and self.is_distractor:
                # Wrong response to distractor signal
                self.false_starts += 1
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
            else:
                # Correct response
                reaction_time = (current_time - self.signal_start_time) * 1000  # Convert to milliseconds
                self.reaction_times.append(reaction_time)
                self.correct_responses += 1
                
                # Visual feedback
                self.create_success_particles()
                
                # Audio feedback
                if self.buzzer:
                    # Play different tones based on reaction time
                    if reaction_time < 200:
                        self.buzzer.play_tone(frequency=1000, duration=0.2)  # Excellent
                    elif reaction_time < 350:
                        self.buzzer.play_tone(frequency=800, duration=0.2)   # Good
                    else:
                        self.buzzer.play_tone(frequency=600, duration=0.2)   # Average
            
            self.current_trial += 1
            self.next_trial()
    
    def create_success_particles(self):
        """Create success reaction particle effects"""
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            particle = {
                'x': self.signal_position[0],
                'y': self.signal_position[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 1.5,
                'color': self.YELLOW,
                'size': random.uniform(2, 6)
            }
            self.particles.append(particle)
    
    def finish_mode(self):
        """Complete current mode"""
        self.state = 'result'
        if self.buzzer:
            self.buzzer.play_tone(frequency=1200, duration=0.5)
    
    def next_mode(self):
        """Enter next mode"""
        self.current_mode_index += 1
        if self.current_mode_index >= len(self.test_modes):
            self.game_over = True
            self.state = 'game_over'
        else:
            self.current_trial = 0
            self.state = 'menu'
    
    def calculate_statistics(self):
        """Calculate statistics"""
        if not self.reaction_times:
            return {}
        
        times = self.reaction_times
        return {
            'count': len(times),
            'average': sum(times) / len(times),
            'fastest': min(times),
            'slowest': max(times),
            'median': sorted(times)[len(times) // 2],
            'consistency': max(times) - min(times) if len(times) > 1 else 0
        }
    
    def get_performance_rating(self, avg_time):
        """Rate performance based on average reaction time"""
        if avg_time < 200:
            return "Amazing", self.GREEN
        elif avg_time < 250:
            return "Excellent", self.CYAN
        elif avg_time < 300:
            return "Good", self.YELLOW
        elif avg_time < 400:
            return "Average", self.ORANGE
        else:
            return "Needs Improvement", self.RED
    
    def update_particles(self, delta_time):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['life'] -= delta_time
            particle['vy'] += 200 * delta_time  # Gravity effect
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def update(self, controller_input=None):
        """Update game state"""
        if self.game_over or self.paused:
            if controller_input and controller_input.get("start_pressed"):
                if self.game_over:
                    self.reset_game()
                else:
                    self.paused = False
            return {"game_over": self.game_over, "paused": self.paused}
        
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # Update animation effects
        self.signal_pulse += delta_time * 8
        if self.background_flash > 0:
            self.background_flash -= delta_time * 30
        
        # Update particles
        self.update_particles(delta_time)
        
        # Handle input
        if controller_input:
            # A button - Reaction button
            if controller_input.get("a_pressed"):
                if self.state in ['waiting', 'signal']:
                    self.handle_response()
                elif self.state == 'menu':
                    self.start_test()
                elif self.state == 'instructions':
                    self.next_trial()
                elif self.state == 'result':
                    self.next_mode()
            
            # B button - Back or skip
            if controller_input.get("b_pressed"):
                if self.state == 'menu':
                    self.game_over = True
                elif self.state in ['instructions', 'result']:
                    self.state = 'menu'
            
            # Arrow keys - Select mode
            if self.state == 'menu':
                if controller_input.get("up_pressed"):
                    self.current_mode_index = (self.current_mode_index - 1) % len(self.test_modes)
                elif controller_input.get("down_pressed"):
                    self.current_mode_index = (self.current_mode_index + 1) % len(self.test_modes)
            
            # Pause control
            if controller_input.get("start_pressed"):
                self.paused = not self.paused
                return {"game_over": self.game_over, "paused": self.paused}
        
        # State machine logic
        if self.state == 'waiting':
            if current_time - self.wait_start_time >= self.wait_time:
                self.show_signal()
        
        elif self.state == 'signal':
            if current_time - self.signal_start_time >= self.signal_duration:
                # Timeout, count as missed
                self.missed_signals += 1
                self.current_trial += 1
                if self.buzzer:
                    self.buzzer.play_tone(frequency=300, duration=0.5)
                self.next_trial()
        
        return {"game_over": self.game_over}
    
    def render(self, screen):
        """Render game screen"""
        # Background
        mode = self.get_current_mode()
        bg_color = mode.get('background_color', self.BLACK)
        
        # Flashing effect
        if self.background_flash > 0:
            flash_intensity = min(self.background_flash / 10, 1.0)
            bg_color = tuple(min(255, int(c + (255 - c) * flash_intensity)) for c in bg_color)
        
        screen.fill(bg_color)
        
        # Render different content based on state
        if self.state == 'menu':
            self.render_menu(screen)
        elif self.state == 'instructions':
            self.render_instructions(screen)
        elif self.state == 'waiting':
            self.render_waiting(screen)
        elif self.state == 'signal':
            self.render_signal(screen)
        elif self.state == 'result':
            self.render_result(screen)
        elif self.game_over:
            self.render_game_over(screen)
        
        # Render particle effects
        self.render_particles(screen)
        
        # Pause screen
        if self.paused:
            self.render_pause_overlay(screen)
    
    def render_menu(self, screen):
        """Render menu"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Title
        title_text = font_large.render("Reaction Test", True, self.WHITE)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))
        
        # Mode selection
        y_start = 150
        for i, mode in enumerate(self.test_modes):
            color = self.YELLOW if i == self.current_mode_index else self.WHITE
            prefix = "▶ " if i == self.current_mode_index else "  "
            
            mode_text = font_medium.render(f"{prefix}{mode['name']}", True, color)
            screen.blit(mode_text, (100, y_start + i * 60))
            
            # Mode description
            if i == self.current_mode_index:
                desc_text = font_small.render(mode['description'], True, self.GRAY)
                screen.blit(desc_text, (120, y_start + i * 60 + 35))
        
        # Control hints
        hint_text = font_small.render("Use arrow keys to select mode, A to start, B to exit", True, self.WHITE)
        screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 80))
    
    def render_instructions(self, screen):
        """Render instructions"""
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        mode = self.get_current_mode()
        
        # Mode name
        title_text = font_large.render(mode['name'], True, self.CYAN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        # Instructions
        instructions = [
            mode['description'],
            "",
            "Press A to start the test",
            f"There will be {self.trials} trials",
            "",
            "Note:",
            "• False starts will be counted as errors",
            "• Missing signals will also be counted",
            "• React as quickly and accurately as possible"
        ]
        
        y_pos = 200
        for instruction in instructions:
            if instruction == "":
                y_pos += 30
                continue
            
            if instruction.startswith("Note:"):
                color = self.YELLOW
                font = font_medium
            elif instruction.startswith("•"):
                color = self.WHITE
                font = font_small
            else:
                color = self.WHITE
                font = font_medium
            
            text = font.render(instruction, True, color)
            screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
            y_pos += 40
    
    def render_waiting(self, screen):
        """Render waiting screen"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        # Waiting prompt
        wait_text = font_large.render("Get Ready...", True, self.WHITE)
        screen.blit(wait_text, (self.width // 2 - wait_text.get_width() // 2, self.height // 2 - 50))
        
        # Progress display
        progress_text = font_medium.render(f"Trial {self.current_trial + 1} / {self.trials}", True, self.GRAY)
        screen.blit(progress_text, (self.width // 2 - progress_text.get_width() // 2, self.height // 2 + 50))
        
        # Warning text (flashing)
        if int(time.time() * 2) % 2:
            warning_text = font_medium.render("Don't press early!", True, self.RED)
            screen.blit(warning_text, (self.width // 2 - warning_text.get_width() // 2, self.height // 2 + 100))
    
    def render_signal(self, screen):
        """Render signal"""
        font_large = pygame.font.Font(None, 72)
        
        # Signal circle (pulse effect)
        pulse_size = 80 + math.sin(self.signal_pulse) * 20
        
        pygame.draw.circle(screen, self.current_signal_color, 
                         self.signal_position, int(pulse_size))
        pygame.draw.circle(screen, self.WHITE, 
                         self.signal_position, int(pulse_size), 3)
        
        # Reaction prompt
        if not self.is_distractor:
            react_text = font_large.render("React!", True, self.WHITE)
            screen.blit(react_text, (self.width // 2 - react_text.get_width() // 2, 100))
        
        # Progress display
        font_medium = pygame.font.Font(None, 48)
        progress_text = font_medium.render(f"Trial {self.current_trial + 1} / {self.trials}", True, self.GRAY)
        screen.blit(progress_text, (self.width // 2 - progress_text.get_width() // 2, self.height - 100))
    
    def render_result(self, screen):
        """Render result"""
        font_large = pygame.font.Font(None, 64)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        mode = self.get_current_mode()
        stats = self.calculate_statistics()
        
        # Mode name
        title_text = font_large.render(f"{mode['name']} - Results", True, self.CYAN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))
        
        if stats:
            # Main statistics
            avg_time = stats['average']
            rating, rating_color = self.get_performance_rating(avg_time)
            
            y_pos = 150
            results = [
                f"Average Reaction Time: {avg_time:.1f} ms",
                f"Fastest Reaction: {stats['fastest']:.1f} ms",
                f"Slowest Reaction: {stats['slowest']:.1f} ms",
                f"Consistency: {stats['consistency']:.1f} ms",
                "",
                f"Performance Rating: {rating}"
            ]
            
            for i, result in enumerate(results):
                if result == "":
                    y_pos += 30
                    continue
                
                if result.startswith("Performance Rating"):
                    color = rating_color
                    font = font_medium
                else:
                    color = self.WHITE
                    font = font_medium
                
                text = font.render(result, True, color)
                screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
                y_pos += 45
            
            # Accuracy
            total_attempts = self.correct_responses + self.false_starts + self.missed_signals
            if total_attempts > 0:
                accuracy = (self.correct_responses / total_attempts) * 100
                accuracy_text = font_medium.render(f"Accuracy: {accuracy:.1f}%", True, 
                                                 self.GREEN if accuracy >= 80 else self.YELLOW if accuracy >= 60 else self.RED)
                screen.blit(accuracy_text, (self.width // 2 - accuracy_text.get_width() // 2, y_pos))
                y_pos += 45
        
        # Control hints
        hint_text = font_small.render("Press A to continue to next mode, B to return to menu", True, self.WHITE)
        screen.blit(hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 80))
    
    def render_game_over(self, screen):
        """Render game over screen"""
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        font_small = pygame.font.Font(None, 36)
        
        # Title
        title_text = font_large.render("Test Complete!", True, self.GREEN)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        # Overall statistics
        if self.reaction_times:
            overall_stats = self.calculate_statistics()
            avg_time = overall_stats['average']
            rating, rating_color = self.get_performance_rating(avg_time)
            
            y_pos = 200
            summary = [
                f"Total Trials: {len(self.reaction_times)}",
                f"Overall Average Reaction Time: {avg_time:.1f} ms",
                f"Best Reaction Time: {overall_stats['fastest']:.1f} ms",
                f"Overall Performance: {rating}",
                "",
                f"Correct Responses: {self.correct_responses}",
                f"False Starts: {self.false_starts}",
                f"Missed Signals: {self.missed_signals}"
            ]
            
            for line in summary:
                if line == "":
                    y_pos += 30
                    continue
                
                if line.startswith("Overall Performance"):
                    color = rating_color
                elif line.startswith("Correct Responses"):
                    color = self.GREEN
                elif line.startswith("False Starts") or line.startswith("Missed Signals"):
                    color = self.RED
                else:
                    color = self.WHITE
                
                text = font_medium.render(line, True, color)
                screen.blit(text, (self.width // 2 - text.get_width() // 2, y_pos))
                y_pos += 40
        
        # Restart hint
        restart_text = font_small.render("Press Start to retry", True, self.WHITE)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, self.height - 80))
    
    def render_particles(self, screen):
        """Render particle effects"""
        for particle in self.particles:
            if particle['life'] > 0:
                alpha = int(particle['life'] * 255)
                size = max(1, int(particle['size'] * particle['life']))
                
                # Create semi-transparent surface
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                color_with_alpha = (*particle['color'], alpha)
                pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
                screen.blit(particle_surf, (particle['x'] - size, particle['y'] - size))
    
    def render_pause_overlay(self, screen):
        """Render pause overlay"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 72)
        font_medium = pygame.font.Font(None, 48)
        
        pause_text = font_large.render("Paused", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))
        
        continue_text = font_medium.render("Press Start to continue", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, self.height // 2 + 50))
    
    def cleanup(self):
        """Clean up game resources"""
        pass


# For standalone execution of this script, for testing
if __name__ == "__main__":
    try:
        # Initialize pygame
        pygame.init()
        
        # Set up window
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Reaction Test Game")
        
        # Create game instance
        game = ReactionTestGame(screen_width, screen_height)
        
        # Simulate controller input key mapping
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed",
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_b: "b_pressed",
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
            game_status = game.update(controller_input)
            
            # Render
            game.render(screen)
            pygame.display.flip()
            
            # Control frame rate
            clock.tick(60)
            
            # Check for game over
            if game_status.get("game_over") and not keys[pygame.K_RETURN]:
                pass
    
    except Exception as e:
        print(f"Error occurred during game execution: {e}")
    finally:
        pygame.quit()
        print("Reaction Test Game Ended")
