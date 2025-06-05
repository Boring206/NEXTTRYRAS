#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# game10.py - Vampire Survivors-like Game Implementation (Optimized for Raspberry Pi)

import random
import pygame
import time
import math
from pygame.locals import *

class VampireSurvivorsGame:
    """Vampire Survivors-like Game Class"""
    
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
        self.PURPLE = (128, 0, 128)
        self.ORANGE = (255, 165, 0)
        self.CYAN = (0, 255, 255)
        self.DARK_RED = (139, 0, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_GRAY = (192, 192, 192)
        
        # Game parameters
        self.player_size = 20
        self.player_speed = 3
        self.enemy_base_speed = 1.5
        self.projectile_speed = 8
        self.experience_orb_size = 8
        
        # Game state
        self.game_over = False
        self.paused = False
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.score = 0
        self.kill_count = 0
        self.survival_time = 0
        
        # Player
        self.player_x = width // 2
        self.player_y = height // 2
        self.player_health = 100
        self.player_max_health = 100
        self.player_regen = 0.1
        
        # Manual attack system
        self.manual_attack_cooldown = 0.3  # A鍵普通攻擊冷卻
        self.manual_attack_last_time = 0
        self.special_attack_cooldown = 2.0  # X鍵小招冷卻
        self.special_attack_last_time = 0
        
        # Manual skills
        self.manual_skills = {
            'normal_attack': {
                'name': 'NORMAL ATTACK',
                'damage': 15,
                'range': 150,
                'cooldown': 0.3,
                'description': 'SHOOT'
            },
            'special_attack': {
                'name': 'BOOM TIPS',
                'damage': 40,
                'range': 100,
                'cooldown': 2.0,
                'description': 'BOOM! Area of effect attack'
            }
        }

        # Weapons system (for auto attacks)
        self.weapons = {
            'basic_shot': {
                'name': 'Basic Shot',
                'level': 0,  # Changed to 0, because it's now manual attack
                'damage': 10,
                'cooldown': 1.0,
                'last_shot': 0,
                'range': 200,
                'projectile_count': 1,
                'description': 'Automatically shoots the nearest enemy'
            },
            'fireball': {
                'name': 'Fireball',
                'level': 0,
                'damage': 25,
                'cooldown': 2.0,
                'last_shot': 0,
                'range': 250,
                'projectile_count': 1,
                'description': 'Automatically launches a high-damage fireball'
            },
            'ice_shard': {
                'name': 'Ice Shard',
                'level': 0,
                'damage': 15,
                'cooldown': 1.5,
                'last_shot': 0,
                'range': 180,
                'projectile_count': 3,
                'description': 'Automatically slows enemies'
            },
            'lightning': {
                'name': 'Chain Lightning',
                'level': 0,
                'damage': 20,
                'cooldown': 3.0,
                'last_shot': 0,
                'range': 300,
                'projectile_count': 1,
                'description': 'Automatically performs a chain attack'
            }
        }
        
        # Enemies and projectiles
        self.enemies = []
        self.projectiles = []
        self.experience_orbs = []
        self.particles = []
        
        # Enemy types
        self.enemy_types = {
            'zombie': {
                'health': 30,
                'speed': 1.0,
                'damage': 15,
                'exp_value': 5,
                'color': self.DARK_GREEN,
                'size': 15
            },
            'skeleton': {
                'health': 20,
                'speed': 1.5,
                'damage': 10,
                'exp_value': 3,
                'color': self.LIGHT_GRAY,
                'size': 12
            },
            'vampire': {
                'health': 80,
                'speed': 0.8,
                'damage': 30,
                'exp_value': 20,
                'color': self.DARK_RED,
                'size': 18
            },
            'ghost': {
                'health': 15,
                'speed': 2.0,
                'damage': 8,
                'exp_value': 4,
                'color': self.CYAN,
                'size': 14
            }
        }
        
        # Spawn control
        self.enemy_spawn_timer = 0
        self.enemy_spawn_interval = 2.0
        self.wave_intensity = 1.0
        
        # Level up system
        self.level_up_choices = []
        self.showing_level_up = False
        self.level_up_choice_index = 0
        
        # Performance optimization
        self.max_enemies = 50  # Limit for Raspberry Pi
        self.max_projectiles = 30
        self.max_particles = 100
        
        # Fonts
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 24)
        
        # Initialize game
        self.reset_game()
    
    def reset_game(self):
        """Reset game to initial state"""
        self.game_over = False
        self.paused = False
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        self.score = 0
        self.kill_count = 0
        self.survival_time = 0
        
        self.player_x = self.width // 2
        self.player_y = self.height // 2
        self.player_health = self.player_max_health
        
        # Reset manual attack timers
        self.manual_attack_last_time = 0
        self.special_attack_last_time = 0
        
        # Reset weapons (all start at level 0 now)
        for weapon in self.weapons.values():
            weapon['level'] = 0
            weapon['last_shot'] = 0
        
        self.enemies.clear()
        self.projectiles.clear()
        self.experience_orbs.clear()
        self.particles.clear()
        
        self.enemy_spawn_timer = 0
        self.wave_intensity = 1.0
        self.showing_level_up = False
        self.level_up_choices.clear()

    def spawn_enemy(self):
        """Spawn a new enemy"""
        if len(self.enemies) >= self.max_enemies:
            return
        
        # Choose enemy type based on survival time
        if self.survival_time < 30:
            enemy_type = random.choice(['zombie', 'skeleton'])
        elif self.survival_time < 60:
            enemy_type = random.choice(['zombie', 'skeleton', 'ghost'])
        else:
            enemy_type = random.choice(['zombie', 'skeleton', 'ghost', 'vampire'])
        
        # Spawn outside screen
        side = random.randint(0, 3)
        if side == 0:  # Top
            x = random.randint(0, self.width)
            y = -20
        elif side == 1:  # Right
            x = self.width + 20
            y = random.randint(0, self.height)
        elif side == 2:  # Bottom
            x = random.randint(0, self.width)
            y = self.height + 20
        else:  # Left
            x = -20
            y = random.randint(0, self.height)
        
        enemy_data = self.enemy_types[enemy_type].copy()
        enemy = {
            'x': x,
            'y': y,
            'type': enemy_type,
            'health': enemy_data['health'] * self.wave_intensity,
            'max_health': enemy_data['health'] * self.wave_intensity,
            'speed': enemy_data['speed'] * (1 + self.survival_time / 120),
            'damage': enemy_data['damage'],
            'exp_value': enemy_data['exp_value'],
            'color': enemy_data['color'],
            'size': enemy_data['size'],
            'last_damage_time': 0,
            'frozen_until': 0
        }
        
        self.enemies.append(enemy)
    
    def update_enemies(self, delta_time):
        """Update enemy positions and behavior"""
        current_time = time.time()
        
        for enemy in self.enemies[:]:
            # Skip if frozen
            if current_time < enemy['frozen_until']:
                continue
            
            # Move towards player
            dx = self.player_x - enemy['x']
            dy = self.player_y - enemy['y']
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # Normalize and apply speed
                move_x = (dx / distance) * enemy['speed'] * 60 * delta_time
                move_y = (dy / distance) * enemy['speed'] * 60 * delta_time
                
                enemy['x'] += move_x
                enemy['y'] += move_y
            
            # Check collision with player
            player_distance = math.sqrt(
                (enemy['x'] - self.player_x) ** 2 + 
                (enemy['y'] - self.player_y) ** 2
            )
            
            if player_distance < (enemy['size'] + self.player_size) / 2:
                # Damage player
                if current_time - enemy['last_damage_time'] > 1.0:
                    self.player_health -= enemy['damage']
                    enemy['last_damage_time'] = current_time
                    
                    # Create damage particles
                    self.create_damage_particles(self.player_x, self.player_y, self.RED)
                    
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=200, duration=0.1)
                    
                    if self.player_health <= 0:
                        self.game_over = True
                        if self.buzzer:
                            self.buzzer.play_tone(frequency=150, duration=1.0)
    
    def fire_weapons(self):
        """Fire all available weapons"""
        current_time = time.time()
        
        for weapon_key, weapon in self.weapons.items():
            if weapon['level'] == 0:
                continue
            
            if current_time - weapon['last_shot'] >= weapon['cooldown']:
                # Find nearest enemy
                nearest_enemy = self.find_nearest_enemy()
                if nearest_enemy:
                    distance = math.sqrt(
                        (nearest_enemy['x'] - self.player_x) ** 2 + 
                        (nearest_enemy['y'] - self.player_y) ** 2
                    )
                    
                    if distance <= weapon['range']:
                        self.create_projectile(weapon_key, weapon, nearest_enemy)
                        weapon['last_shot'] = current_time
    
    def find_nearest_enemy(self):
        """Find the nearest enemy to the player"""
        nearest = None
        min_distance = float('inf')
        
        for enemy in self.enemies:
            distance = math.sqrt(
                (enemy['x'] - self.player_x) ** 2 + 
                (enemy['y'] - self.player_y) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                nearest = enemy
        
        return nearest
    
    def create_projectile(self, weapon_key, weapon, target):
        """Create projectile for weapon"""
        if len(self.projectiles) >= self.max_projectiles:
            return
        
        # Calculate direction to target
        dx = target['x'] - self.player_x
        dy = target['y'] - self.player_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return
        
        # Normalize direction
        dir_x = dx / distance
        dir_y = dy / distance
        
        # Create projectiles based on weapon type
        for i in range(weapon['projectile_count']):
            angle_offset = 0
            if weapon['projectile_count'] > 1:
                angle_offset = (i - weapon['projectile_count'] / 2) * 0.3
            
            # Apply angle offset
            cos_offset = math.cos(angle_offset)
            sin_offset = math.sin(angle_offset)
            
            final_dir_x = dir_x * cos_offset - dir_y * sin_offset
            final_dir_y = dir_x * sin_offset + dir_y * cos_offset
            
            projectile = {
                'x': self.player_x,
                'y': self.player_y,
                'vx': final_dir_x * self.projectile_speed,
                'vy': final_dir_y * self.projectile_speed,
                'damage': weapon['damage'] * weapon['level'],
                'weapon_type': weapon_key,
                'lifetime': 3.0,
                'size': 5
            }
            
            self.projectiles.append(projectile)
        
        # Play sound effect
        if self.buzzer:
            frequency = {'basic_shot': 800, 'fireball': 600, 'ice_shard': 1000, 'lightning': 1200}
            self.buzzer.play_tone(frequency=frequency.get(weapon_key, 800), duration=0.1)
    
    def manual_normal_attack(self):
        """Handle manual normal attack (A key)"""
        current_time = time.time()
        
        if current_time - self.manual_attack_last_time >= self.manual_attack_cooldown:
            # Find nearest enemy for targeting
            nearest_enemy = self.find_nearest_enemy()
            if nearest_enemy:
                # Check if enemy is in range
                distance = math.sqrt(
                    (nearest_enemy['x'] - self.player_x) ** 2 + 
                    (nearest_enemy['y'] - self.player_y) ** 2
                )
                
                if distance <= self.manual_skills['normal_attack']['range']:
                    # Calculate direction to target
                    dx = nearest_enemy['x'] - self.player_x
                    dy = nearest_enemy['y'] - self.player_y
                    
                    if distance > 0:
                        # Normalize direction
                        dir_x = dx / distance
                        dir_y = dy / distance
                        
                        # Create projectile
                        if len(self.projectiles) < self.max_projectiles:
                            projectile = {
                                'x': self.player_x,
                                'y': self.player_y,
                                'vx': dir_x * self.projectile_speed,
                                'vy': dir_y * self.projectile_speed,
                                'damage': self.manual_skills['normal_attack']['damage'],
                                'weapon_type': 'manual_normal',
                                'lifetime': 3.0,
                                'size': 6
                            }
                            self.projectiles.append(projectile)
                        
                        # Update cooldown
                        self.manual_attack_last_time = current_time
                        
                        # Play sound effect
                        if self.buzzer:
                            self.buzzer.play_tone(frequency=900, duration=0.1)

    def manual_special_attack(self):
        """Handle manual special attack (X key)"""
        current_time = time.time()
        
        if current_time - self.special_attack_last_time >= self.special_attack_cooldown:
            # Area of effect attack around player
            attack_range = self.manual_skills['special_attack']['range']
            attack_damage = self.manual_skills['special_attack']['damage']
            
            # Damage all enemies in range
            enemies_hit = 0
            for enemy in self.enemies[:]:
                distance = math.sqrt(
                    (enemy['x'] - self.player_x) ** 2 + 
                    (enemy['y'] - self.player_y) ** 2
                )
                
                if distance <= attack_range:
                    enemy['health'] -= attack_damage
                    enemies_hit += 1
                    
                    # Create hit particles
                    self.create_hit_particles(enemy['x'], enemy['y'], self.ORANGE)
                    
                    # Check if enemy is dead
                    if enemy['health'] <= 0:
                        self.kill_enemy(enemy)
            
            if enemies_hit > 0:
                # Create explosion effect around player
                for _ in range(20):
                    if len(self.particles) >= self.max_particles:
                        break
                    
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    
                    particle = {
                        'x': self.player_x,
                        'y': self.player_y,
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed,
                        'color': self.ORANGE,
                        'lifetime': 1.0,
                        'size': random.uniform(4, 8)
                    }
                    self.particles.append(particle)
                
                # Update cooldown
                self.special_attack_last_time = current_time
                
                # Play sound effect
                if self.buzzer:
                    self.buzzer.play_tone(frequency=500, duration=0.3)

    def apply_level_up_choice(self, choice):
        """Apply the selected level up choice"""
        if choice['type'] == 'weapon':
            self.weapons[choice['key']]['level'] += 1
        elif choice['type'] == 'manual_normal':
            self.manual_skills['normal_attack']['damage'] += 5
            self.manual_attack_cooldown = max(0.1, self.manual_attack_cooldown - 0.05)
            self.manual_skills['normal_attack']['cooldown'] = self.manual_attack_cooldown
        elif choice['type'] == 'manual_special':
            self.manual_skills['special_attack']['damage'] += 10
            self.manual_skills['special_attack']['range'] += 10
        elif choice['type'] == 'health':
            self.player_max_health += 20
            self.player_health += 20
        elif choice['type'] == 'speed':
            self.player_speed += 0.5
        elif choice['type'] == 'regen':
            self.player_regen += 0.1
        
        self.showing_level_up = False
        self.level_up_choices.clear()

    def update_projectiles(self, delta_time):
        """Update projectile positions and collisions"""
        for projectile in self.projectiles[:]:
            # Move projectile
            projectile['x'] += projectile['vx'] * delta_time
            projectile['y'] += projectile['vy'] * delta_time
            projectile['lifetime'] -= delta_time
            
            # Remove if expired or out of bounds
            if (projectile['lifetime'] <= 0 or 
                projectile['x'] < -50 or projectile['x'] > self.width + 50 or
                projectile['y'] < -50 or projectile['y'] > self.height + 50):
                self.projectiles.remove(projectile)
                continue
            
            # Check collision with enemies
            for enemy in self.enemies[:]:
                distance = math.sqrt(
                    (projectile['x'] - enemy['x']) ** 2 + 
                    (projectile['y'] - enemy['y']) ** 2
                )
                
                if distance < (projectile['size'] + enemy['size']) / 2:
                    # Deal damage
                    enemy['health'] -= projectile['damage']
                    
                    # Special weapon effects
                    if projectile['weapon_type'] == 'ice_shard':
                        enemy['frozen_until'] = time.time() + 1.0
                    elif projectile['weapon_type'] == 'lightning':
                        self.chain_lightning(enemy, projectile['damage'] // 2, 2)
                    
                    # Create hit particles
                    hit_color = self.WHITE
                    if projectile['weapon_type'] == 'manual_normal':
                        hit_color = self.BLUE
                    elif projectile['weapon_type'] == 'lightning':
                        hit_color = self.YELLOW
                    elif projectile['weapon_type'] == 'fireball':
                        hit_color = self.ORANGE
                    
                    self.create_hit_particles(enemy['x'], enemy['y'], hit_color)
                    
                    # Remove projectile
                    if projectile in self.projectiles:
                        self.projectiles.remove(projectile)
                    
                    # Check if enemy is dead
                    if enemy['health'] <= 0:
                        self.kill_enemy(enemy)
                    
                    break
    
    def chain_lightning(self, origin_enemy, damage, chains_left):
        """Chain lightning effect"""
        if chains_left <= 0:
            return
        
        # Find nearby enemies
        for enemy in self.enemies:
            if enemy == origin_enemy:
                continue
            
            distance = math.sqrt(
                (enemy['x'] - origin_enemy['x']) ** 2 + 
                (enemy['y'] - origin_enemy['y']) ** 2
            )
            
            if distance < 80:  # Chain range
                enemy['health'] -= damage
                self.create_hit_particles(enemy['x'], enemy['y'], self.YELLOW)
                
                if enemy['health'] <= 0:
                    self.kill_enemy(enemy)
                else:
                    self.chain_lightning(enemy, damage // 2, chains_left - 1)
                break
    
    def kill_enemy(self, enemy):
        """Handle enemy death"""
        # Add experience
        self.experience += enemy['exp_value']
        self.score += enemy['exp_value'] * 10
        self.kill_count += 1
        
        # Create experience orb
        orb = {
            'x': enemy['x'],
            'y': enemy['y'],
            'value': enemy['exp_value'],
            'lifetime': 10.0
        }
        self.experience_orbs.append(orb)
        
        # Create death particles
        self.create_death_particles(enemy['x'], enemy['y'], enemy['color'])
        
        # Remove enemy
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        
        if self.buzzer:
            self.buzzer.play_tone(frequency=400, duration=0.05)
    
    def update_experience_orbs(self, delta_time):
        """Update experience orbs"""
        for orb in self.experience_orbs[:]:
            orb['lifetime'] -= delta_time
            
            # Remove expired orbs
            if orb['lifetime'] <= 0:
                self.experience_orbs.remove(orb)
                continue
            
            # Check if player is nearby to collect
            distance = math.sqrt(
                (orb['x'] - self.player_x) ** 2 + 
                (orb['y'] - self.player_y) ** 2
            )
            
            if distance < 30:
                # Move orb towards player
                dx = self.player_x - orb['x']
                dy = self.player_y - orb['y']
                if distance > 0:
                    orb['x'] += (dx / distance) * 200 * delta_time
                    orb['y'] += (dy / distance) * 200 * delta_time
                
                # Collect if close enough
                if distance < 15:
                    self.experience_orbs.remove(orb)
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=600, duration=0.05)
    
    def check_level_up(self):
        """Check if player should level up"""
        if self.experience >= self.experience_to_next_level:
            self.level += 1
            self.experience -= self.experience_to_next_level
            self.experience_to_next_level = int(self.experience_to_next_level * 1.2)
            
            # Generate level up choices
            self.generate_level_up_choices()
            self.showing_level_up = True
            
            if self.buzzer:
                self.buzzer.play_tone(frequency=1000, duration=0.3)
    
    def generate_level_up_choices(self):
        """Generate random level up choices"""
        choices = []
        
        # Weapon upgrades (auto weapons)
        for weapon_key, weapon in self.weapons.items():
            if weapon['level'] < 5:  # Max level 5
                choice = {
                    'type': 'weapon',
                    'key': weapon_key,
                    'name': weapon['name'],
                    'description': f"LEVEL {weapon['level']} → {weapon['level'] + 1} (自動攻擊)"
                }
                choices.append(choice)
        
        # Manual skill upgrades
        manual_choices = [
            {'type': 'manual_normal', 'name': 'NORMAL ATTACK', 'description': 'DAMAGE +5, CD -0.05秒'},
            {'type': 'manual_special', 'name': 'TIPS', 'description': 'DAMAGE +10, RANGE +10'},
        ]
        choices.extend(manual_choices)
        
        # Stat upgrades
        stat_choices = [
            {'type': 'health', 'name': 'LIFE LIMIT', 'description': '+20 LIFE LIMIT'},
            {'type': 'speed', 'name': 'SPEED', 'description': '+0.5 SPEED'},
            {'type': 'regen', 'name': 'LIFE REGENERATION', 'description': '+0.1 HP restored per second'}
        ]
        choices.extend(stat_choices)
        
        # Select 3 random choices
        self.level_up_choices = random.sample(choices, min(3, len(choices)))
        self.level_up_choice_index = 0

    def apply_level_up_choice(self, choice):
        """Apply the selected level up choice"""
        if choice['type'] == 'weapon':
            self.weapons[choice['key']]['level'] += 1
        elif choice['type'] == 'manual_normal':
            self.manual_skills['normal_attack']['damage'] += 5
            self.manual_attack_cooldown = max(0.1, self.manual_attack_cooldown - 0.05)
            self.manual_skills['normal_attack']['cooldown'] = self.manual_attack_cooldown
        elif choice['type'] == 'manual_special':
            self.manual_skills['special_attack']['damage'] += 10
            self.manual_skills['special_attack']['range'] += 10
        elif choice['type'] == 'health':
            self.player_max_health += 20
            self.player_health += 20
        elif choice['type'] == 'speed':
            self.player_speed += 0.5
        elif choice['type'] == 'regen':
            self.player_regen += 0.1
        
        self.showing_level_up = False
        self.level_up_choices.clear()

    def create_hit_particles(self, x, y, color):
        """Create hit effect particles"""
        for _ in range(5):
            if len(self.particles) >= self.max_particles:
                break
            
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-50, 50),
                'vy': random.uniform(-50, 50),
                'color': color,
                'lifetime': 0.5,
                'size': random.uniform(2, 4)
            }
            self.particles.append(particle)
    
    def create_death_particles(self, x, y, color):
        """Create death effect particles"""
        for _ in range(10):
            if len(self.particles) >= self.max_particles:
                break
            
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-100, 100),
                'color': color,
                'lifetime': 1.0,
                'size': random.uniform(3, 6)
            }
            self.particles.append(particle)
    
    def create_damage_particles(self, x, y, color):
        """Create damage effect particles"""
        for _ in range(8):
            if len(self.particles) >= self.max_particles:
                break
            
            particle = {
                'x': x,
                'y': y,
                'vx': random.uniform(-80, 80),
                'vy': random.uniform(-80, 80),
                'color': color,
                'lifetime': 0.8,
                'size': random.uniform(2, 5)
            }
            self.particles.append(particle)
    
    def update_particles(self, delta_time):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['lifetime'] -= delta_time
            particle['vy'] += 150 * delta_time  # Gravity
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def update(self, controller_input=None):
        """Update game state"""
        if self.game_over:
            if controller_input and controller_input.get("start_pressed"):
                self.reset_game()
            return {"game_over": self.game_over, "score": self.score}
        
        if self.paused:
            if controller_input and controller_input.get("start_pressed"):
                self.paused = False
            return {"game_over": self.game_over, "paused": self.paused}
        
        current_time = time.time()
        delta_time = current_time - getattr(self, '_last_update_time', current_time)
        self._last_update_time = current_time
        
        # Handle level up screen
        if self.showing_level_up:
            if controller_input:
                if controller_input.get("up_pressed"):
                    self.level_up_choice_index = (self.level_up_choice_index - 1) % len(self.level_up_choices)
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=300, duration=0.05)
                elif controller_input.get("down_pressed"):
                    self.level_up_choice_index = (self.level_up_choice_index + 1) % len(self.level_up_choices)
                    if self.buzzer:
                        self.buzzer.play_tone(frequency=300, duration=0.05)
                elif controller_input.get("a_pressed"):
                    self.apply_level_up_choice(self.level_up_choices[self.level_up_choice_index])
            return {"game_over": False}
        
        # Update survival time
        self.survival_time += delta_time
        
        # Handle manual attacks
        if controller_input:
            if controller_input.get("a_pressed"):
                self.manual_normal_attack()
            if controller_input.get("x_pressed"):
                self.manual_special_attack()
        
        # Player movement with analog stick support
        if controller_input:
            # Initialize left stick parameters if not exists
            if not hasattr(self, 'stick_threshold'):
                self.stick_threshold = 0.3  # Lower threshold for movement
            
            moved = False
            
            # Left stick input
            stick_x = controller_input.get("left_stick_x", 0.0)
            stick_y = controller_input.get("left_stick_y", 0.0)
            
            if abs(stick_x) > self.stick_threshold or abs(stick_y) > self.stick_threshold:
                move_x = stick_x * self.player_speed * 60 * delta_time
                move_y = stick_y * self.player_speed * 60 * delta_time
                
                # Apply movement with bounds checking
                new_x = max(self.player_size, min(self.width - self.player_size, self.player_x + move_x))
                new_y = max(self.player_size, min(self.height - self.player_size, self.player_y + move_y))
                
                self.player_x = new_x
                self.player_y = new_y
                moved = True
            
            # D-pad movement (takes priority)
            if controller_input.get("left_pressed"):
                self.player_x = max(self.player_size, self.player_x - self.player_speed * 60 * delta_time)
                moved = True
            elif controller_input.get("right_pressed"):
                self.player_x = min(self.width - self.player_size, self.player_x + self.player_speed * 60 * delta_time)
                moved = True
            
            if controller_input.get("up_pressed"):
                self.player_y = max(self.player_size, self.player_y - self.player_speed * 60 * delta_time)
                moved = True
            elif controller_input.get("down_pressed"):
                self.player_y = min(self.height - self.player_size, self.player_y + self.player_speed * 60 * delta_time)
                moved = True
            
            # Pause
            if controller_input.get("start_pressed"):
                self.paused = True
        
        # Player regeneration
        if self.player_health < self.player_max_health:
            self.player_health = min(self.player_max_health, 
                                   self.player_health + self.player_regen * delta_time)
        
        # Enemy spawning
        self.enemy_spawn_timer += delta_time
        spawn_rate = max(0.5, self.enemy_spawn_interval - self.survival_time / 60)
        
        if self.enemy_spawn_timer >= spawn_rate:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0
        
        # Update wave intensity
        self.wave_intensity = 1 + self.survival_time / 120
        
        # Update game objects
        self.update_enemies(delta_time)
        self.fire_weapons()
        self.update_projectiles(delta_time)
        self.update_experience_orbs(delta_time)
        self.update_particles(delta_time)
        
        # Check level up
        self.check_level_up()
        
        return {"game_over": self.game_over, "score": self.score}
    
    def render(self, screen):
        """Render game screen"""
        # Clear screen
        screen.fill(self.BLACK)
        
        if self.game_over:
            self.render_game_over(screen)
            return
        
        if self.paused:
            self.render_pause(screen)
            return
        
        # Render particles (background layer)
        for particle in self.particles:
            if particle['lifetime'] > 0:
                alpha = min(255, int(particle['lifetime'] * 255))
                size = max(1, int(particle['size'] * particle['lifetime']))
                color = (*particle['color'][:3], alpha)
                
                # Create surface for alpha blending
                particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surf, color, (size, size), size)
                screen.blit(particle_surf, (int(particle['x'] - size), int(particle['y'] - size)))
        
        # Render experience orbs
        for orb in self.experience_orbs:
            pulse = 1 + 0.3 * math.sin(time.time() * 5)
            size = int(self.experience_orb_size * pulse)
            pygame.draw.circle(screen, self.YELLOW, 
                             (int(orb['x']), int(orb['y'])), size)
            pygame.draw.circle(screen, self.WHITE, 
                             (int(orb['x']), int(orb['y'])), size, 2)
        
        # Render enemies
        for enemy in self.enemies:
            color = enemy['color']
            
            # Frozen effect
            if time.time() < enemy['frozen_until']:
                color = self.CYAN
            
            # Enemy body
            pygame.draw.circle(screen, color, 
                             (int(enemy['x']), int(enemy['y'])), enemy['size'])
            pygame.draw.circle(screen, self.WHITE, 
                             (int(enemy['x']), int(enemy['y'])), enemy['size'], 2)
            
            # Health bar
            if enemy['health'] < enemy['max_health']:
                bar_width = enemy['size'] * 2
                bar_height = 4
                bar_x = enemy['x'] - bar_width // 2
                bar_y = enemy['y'] - enemy['size'] - 8
                
                health_ratio = enemy['health'] / enemy['max_health']
                
                pygame.draw.rect(screen, self.RED, 
                               (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(screen, self.GREEN, 
                               (bar_x, bar_y, bar_width * health_ratio, bar_height))
        
        # Render projectiles
        for projectile in self.projectiles:
            color = self.WHITE
            if projectile['weapon_type'] == 'fireball':
                color = self.ORANGE
            elif projectile['weapon_type'] == 'ice_shard':
                color = self.CYAN
            elif projectile['weapon_type'] == 'lightning':
                color = self.YELLOW
            elif projectile['weapon_type'] == 'manual_normal':
                color = self.BLUE
            
            pygame.draw.circle(screen, color, 
                             (int(projectile['x']), int(projectile['y'])), projectile['size'])
        
        # Render player
        pygame.draw.circle(screen, self.BLUE, 
                         (int(self.player_x), int(self.player_y)), self.player_size)
        pygame.draw.circle(screen, self.WHITE, 
                         (int(self.player_x), int(self.player_y)), self.player_size, 3)
        
        # Render UI
        self.render_ui(screen)
        
        # Render level up screen
        if self.showing_level_up:
            self.render_level_up(screen)
    
    def render_ui(self, screen):
        """Render user interface"""
        # Health bar
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 10
        
        health_ratio = self.player_health / self.player_max_health
        
        pygame.draw.rect(screen, self.RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, self.GREEN, (bar_x, bar_y, bar_width * health_ratio, bar_height))
        pygame.draw.rect(screen, self.WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Health text
        health_text = self.font_small.render(f"HP: {int(self.player_health)}/{self.player_max_health}", 
                                           True, self.WHITE)
        screen.blit(health_text, (bar_x, bar_y + bar_height + 5))
        
        # Experience bar
        exp_bar_y = bar_y + bar_height + 30
        exp_ratio = self.experience / self.experience_to_next_level
        
        pygame.draw.rect(screen, self.GRAY, (bar_x, exp_bar_y, bar_width, 15))
        pygame.draw.rect(screen, self.PURPLE, (bar_x, exp_bar_y, bar_width * exp_ratio, 15))
        pygame.draw.rect(screen, self.WHITE, (bar_x, exp_bar_y, bar_width, 15), 2)
        
        # Manual attack cooldowns
        current_time = time.time()
        
        # Normal attack cooldown (A key)
        normal_cd_remaining = max(0, self.manual_attack_cooldown - (current_time - self.manual_attack_last_time))
        normal_cd_ratio = 1 - (normal_cd_remaining / self.manual_attack_cooldown)
        
        cd_bar_y = exp_bar_y + 25
        cd_bar_width = 90
        
        pygame.draw.rect(screen, self.GRAY, (bar_x, cd_bar_y, cd_bar_width, 12))
        pygame.draw.rect(screen, self.GREEN, (bar_x, cd_bar_y, cd_bar_width * normal_cd_ratio, 12))
        pygame.draw.rect(screen, self.WHITE, (bar_x, cd_bar_y, cd_bar_width, 12), 1)
        
        normal_text = self.font_small.render("A:NORMAL ATTACK", True, self.WHITE)
        screen.blit(normal_text, (bar_x + cd_bar_width + 5, cd_bar_y - 2))
        
        # Special attack cooldown (X key)
        special_cd_remaining = max(0, self.special_attack_cooldown - (current_time - self.special_attack_last_time))
        special_cd_ratio = 1 - (special_cd_remaining / self.special_attack_cooldown)
        
        cd_bar_y += 20
        
        pygame.draw.rect(screen, self.GRAY, (bar_x, cd_bar_y, cd_bar_width, 12))
        pygame.draw.rect(screen, self.ORANGE, (bar_x, cd_bar_y, cd_bar_width * special_cd_ratio, 12))
        pygame.draw.rect(screen, self.WHITE, (bar_x, cd_bar_y, cd_bar_width, 12), 1)
        
        special_text = self.font_small.render("X:TIPS", True, self.WHITE)
        screen.blit(special_text, (bar_x + cd_bar_width + 5, cd_bar_y - 2))
        
        # Level and stats
        level_text = self.font_small.render(f"level: {self.level}", True, self.WHITE)
        screen.blit(level_text, (bar_x, cd_bar_y + 25))
        
        time_text = self.font_small.render(f"time: {int(self.survival_time)}s", True, self.WHITE)
        screen.blit(time_text, (bar_x, cd_bar_y + 45))
        
        kills_text = self.font_small.render(f"kill: {self.kill_count}", True, self.WHITE)
        screen.blit(kills_text, (bar_x, cd_bar_y + 65))
        
        # Score in top right
        score_text = self.font_medium.render(f"score: {self.score}", True, self.WHITE)
        screen.blit(score_text, (self.width - score_text.get_width() - 10, 10))

    def render_level_up(self, screen):
        """Render level up choice screen"""
        # Overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Title
        title_text = self.font_large.render("upgrade!", True, self.YELLOW)
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 100))
        
        # Choices
        start_y = 200
        for i, choice in enumerate(self.level_up_choices):
            color = self.YELLOW if i == self.level_up_choice_index else self.WHITE
            
            choice_text = self.font_medium.render(choice['name'], True, color)
            desc_text = self.font_small.render(choice['description'], True, self.GRAY)
            
            y_pos = start_y + i * 80
            
            # Selection indicator
            if i == self.level_up_choice_index:
                pygame.draw.rect(screen, (50, 50, 100), 
                               (50, y_pos - 10, self.width - 100, 60))
            
            screen.blit(choice_text, (100, y_pos))
            screen.blit(desc_text, (100, y_pos + 30))
        
        # Instructions
        instruction_text = self.font_small.render("方向鍵選擇，A鍵確認", True, self.WHITE)
        screen.blit(instruction_text, (self.width // 2 - instruction_text.get_width() // 2, 
                                     self.height - 50))
    
    def render_pause(self, screen):
        """Render pause screen"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        
        pause_text = self.font_large.render("遊戲暫停", True, self.YELLOW)
        screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, 
                                self.height // 2 - 50))
        
        continue_text = self.font_medium.render("按 Start 繼續", True, self.WHITE)
        screen.blit(continue_text, (self.width // 2 - continue_text.get_width() // 2, 
                                  self.height // 2 + 50))
    
    def render_game_over(self, screen):
        """Render game over screen"""
        screen.fill(self.BLACK)
        
        # Game Over title
        game_over_text = self.font_large.render("遊戲結束", True, self.RED)
        screen.blit(game_over_text, (self.width // 2 - game_over_text.get_width() // 2, 150))
        
        # Stats
        stats = [
            f"score: {self.score}",
            f"urival_time: {int(self.survival_time)} 秒",
            f"kill_count: {self.kill_count}",
            f"level: {self.level}"
        ]
        
        y_pos = 250
        for stat in stats:
            stat_text = self.font_medium.render(stat, True, self.WHITE)
            screen.blit(stat_text, (self.width // 2 - stat_text.get_width() // 2, y_pos))
            y_pos += 40
        
        # Restart instruction
        restart_text = self.font_medium.render("按 Start 重新開始", True, self.YELLOW)
        screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 
                                 self.height - 100))
    
    def cleanup(self):
        """Clean up game resources"""
        pass

# Test code
if __name__ == "__main__":
    try:
        pygame.init()
        screen_width = 800
        screen_height = 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Vampire Survivors-like Game Test")
        
        class MockBuzzer:
            def play_tone(self, frequency=None, duration=None):
                print(f"Buzzer: freq={frequency}, dur={duration}")
        
        game = VampireSurvivorsGame(screen_width, screen_height, buzzer=MockBuzzer())
        
        key_mapping = {
            pygame.K_UP: "up_pressed",
            pygame.K_DOWN: "down_pressed", 
            pygame.K_LEFT: "left_pressed",
            pygame.K_RIGHT: "right_pressed",
            pygame.K_a: "a_pressed",
            pygame.K_x: "x_pressed",
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
            
            game.update(controller_input)
            game.render(screen)
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
    
    except Exception as e:
        print(f"Game execution error: {e}")
        pygame.quit()
