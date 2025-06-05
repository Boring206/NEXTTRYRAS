#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main.py - 主程式，負責整合所有模組 (Enhanced Version)

import os
import sys
import time
import json
import logging
import threading
import queue
from datetime import datetime
from enum import Enum
import pygame
from pygame.locals import *
import RPi.GPIO as GPIO
import subprocess
import signal # 用於信號處理
import psutil
import traceback

# 導入所需的本地模組
from screen_menu import SPIScreenManager
from matrix_keypad import MatrixKeypad
from gamepad_input import XboxController
from buzzer import BuzzerControl # 從 buzzer.py 導入
from traffic_light import TrafficLight
from power_button import GameControlButton, GAME_CONTROL_BUTTON_PIN # 從 power_button.py 導入

# 遊戲模組導入
sys.path.append(os.path.join(os.path.dirname(__file__), 'games'))
from games.game1 import SnakeGame
from games.game2 import BrickBreakerGame
from games.game3 import SpaceInvadersGame
from games.game4 import TicTacToeGame
from games.game5 import MemoryMatchGame
from games.game6 import SimpleMazeGame
from games.game7 import WhacAMoleGame
from games.game8 import TetrisLikeGame
from games.game9 import ReactionTestGame
from games.game10 import VampireSurvivorsGame
from games.game11 import LegendsOfValorGame  # 新增導入

# 全域設定
VERSION = "2.0.0"
HDMI_SCREEN_WIDTH = 800
HDMI_SCREEN_HEIGHT = 600
FPS = 60

# 硬體 GPIO 設定 (主程式中定義的交通燈，其他硬體 PIN 在各自模組中定義或傳遞)
TRAFFIC_LIGHT_RED_PIN = 4
TRAFFIC_LIGHT_YELLOW_PIN = 3
TRAFFIC_LIGHT_GREEN_PIN = 2

# 中文字型路徑設定 (請根據您的系統修改)
CHINESE_FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"

# --- 信號處理相關全域變數 ---
shutdown_requested_by_signal = False
game_console_instance_for_signal = None # 用於從信號處理函數訪問主控台實例

def signal_handler_usr1(signum, frame):
    """處理 SIGUSR1 信號 (通常由 power_button.py 在系統關機前發送)"""
    global shutdown_requested_by_signal
    global game_console_instance_for_signal
    logging.info(f"接收到 SIGUSR1 ({signum})，請求關閉遊戲主程序...")
    shutdown_requested_by_signal = True
    if game_console_instance_for_signal:
        game_console_instance_for_signal.running = False # 通知主循環停止

class GameState(Enum):
    """遊戲狀態枚舉"""
    STARTUP = "startup"
    MENU = "menu"
    INSTRUCTION = "instruction"
    GAME_STARTING = "game_starting"
    GAME = "game"
    GAME_PAUSED = "game_paused"
    GAME_OVER = "game_over"
    SETTINGS = "settings"
    SHUTDOWN = "shutdown"
    ERROR = "error"

class SystemConfig:
    """系統配置管理類"""
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.default_config = {
            "display": {"hdmi_width": HDMI_SCREEN_WIDTH, "hdmi_height": HDMI_SCREEN_HEIGHT, "fps": FPS, "fullscreen": False},
            "audio": {"enable_buzzer": True, "volume": 80, "startup_sound": True},
            "hardware": {"spi_screen_enabled": True, "xbox_controller_enabled": True, "matrix_keypad_enabled": True, "traffic_light_enabled": True, "power_button_enabled": True},
            "debug": {"log_level": "INFO", "show_fps": False, "hardware_monitor": False}
        }
        self.config = self.load_config()
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return self._merge_config(self.default_config, config)
            else:
                self.save_config(self.default_config); return self.default_config.copy()
        except Exception as e: logging.error(f"載入配置失敗: {e}"); return self.default_config.copy()
    def save_config(self, config=None):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config or self.config, f, indent=2, ensure_ascii=False)
        except Exception as e: logging.error(f"儲存配置失敗: {e}")
    def _merge_config(self, default, user):
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else: result[key] = value
        return result

class PerformanceMonitor:
    """性能監控類"""
    def __init__(self):
        self.start_time = time.time(); self.frame_count = 0; self.fps_history = []
        self.cpu_usage = 0; self.memory_usage = 0; self.temperature = 0
    def update(self):
        self.frame_count += 1; current_time = time.time()
        if current_time - self.start_time >= 1.0:
            fps = self.frame_count / (current_time - self.start_time)
            self.fps_history.append(fps)
            if len(self.fps_history) > 60: self.fps_history.pop(0)
            self.frame_count = 0; self.start_time = current_time
            self.cpu_usage = psutil.cpu_percent(); self.memory_usage = psutil.virtual_memory().percent
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f: self.temperature = int(f.read()) / 1000.0
            except: self.temperature = 0
    def get_average_fps(self): return sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0

class EnhancedGameConsole:
    """增強版多功能遊戲機主控制類"""
    def __init__(self):
        self._setup_logging()
        self.config = SystemConfig()
        logging.info(f"遊戲機系統啟動 v{VERSION}")
        self.games = [
            {"id": 1, "name": "貪吃蛇", "description": "搖桿控制方向。按A鈕加速。避免撞牆和自己。", "game_class": SnakeGame, "difficulty": "Easy"},
            {"id": 2, "name": "打磚塊", "description": "搖桿左右移動擋板。按A鈕發射球。清除所有磚塊。", "game_class": BrickBreakerGame, "difficulty": "Medium"},
            {"id": 3, "name": "太空侵略者", "description": "搖桿左右移動。按A鈕射擊。消滅所有外星人。", "game_class": SpaceInvadersGame, "difficulty": "Hard"},
            {"id": 4, "name": "井字遊戲", "description": "搖桿選擇格子。按A鈕確認。連成一線獲勝。", "game_class": TicTacToeGame, "difficulty": "Easy"},
            {"id": 5, "name": "記憶翻牌", "description": "搖桿選擇牌。按A鈕翻牌。記住位置配對。", "game_class": MemoryMatchGame, "difficulty": "Medium"},
            {"id": 6, "name": "簡易迷宮", "description": "搖桿控制方向。找到出口。時間越短越好。", "game_class": SimpleMazeGame, "difficulty": "Medium"},
            {"id": 7, "name": "打地鼠", "description": "搖桿移動槌子。按A鈕敲擊。反應要快！", "game_class": WhacAMoleGame, "difficulty": "Hard"},
            {"id": 8, "name": "俄羅斯方塊", "description": "搖桿移動旋轉。消除滿行得分。速度會加快。", "game_class": TetrisLikeGame, "difficulty": "Hard"},
            {"id": 9, "name": "反應力測試", "description": "出現信號時按A鈕。測試反應速度極限。", "game_class": ReactionTestGame, "difficulty": "Medium"},
            {"id": 10, "name": "吸血鬼倖存者", "description": "搖桿移動角色。自動攻擊敵人。升級武器生存！按A普攻、X鍵：小招", "game_class": VampireSurvivorsGame, "difficulty": "Hard"},

        ]
        self.state = GameState.STARTUP; self.previous_state = None; self.current_selection = 0
        self.current_game = None; self.running = True # 主循環控制旗標
        self.hdmi_screen = None; self.clock = None; self.spi_screen = None; self.keypad = None
        self.controller = None; self.buzzer = None; self.traffic_light = None
        self.power_button = None # 遊戲內控制按鈕的實例
        self.performance_monitor = PerformanceMonitor(); self.event_queue = queue.Queue()
        self.last_input_time = 0; self.input_cooldown = 0.2
        self.session_stats = {"start_time": datetime.now(), "games_played": 0, "total_score": 0, "best_scores": {}}
        self.monitor_thread = None; self.monitor_running = False
        self.font_large = None; self.font_medium = None; self.font_small = None; self.font_tiny = None
        self.font_title_main = None; self.font_item_menu = None; self.font_info_menu = None
        self.font_text_instruction = None; self.font_hint_instruction = None
        logging.info("遊戲機系統初始化完成")

    def _setup_logging(self):
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'gamebox_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()])

    def initialize_hardware(self):
        logging.info("開始硬體初始化...")
        try:
            if not self._init_gpio(): return False
            if not self._init_pygame(): return False
            hardware_results = {}
            if self.config.config["hardware"]["spi_screen_enabled"]: hardware_results["spi_screen"] = self._init_spi_screen()
            if self.config.config["hardware"]["matrix_keypad_enabled"]: hardware_results["keypad"] = self._init_keypad()
            if self.config.config["hardware"]["xbox_controller_enabled"]: hardware_results["controller"] = self._init_controller()
            if self.config.config["audio"]["enable_buzzer"]: hardware_results["buzzer"] = self._init_buzzer()
            if self.config.config["hardware"]["traffic_light_enabled"]: hardware_results["traffic_light"] = self._init_traffic_light()
            if self.config.config["hardware"]["power_button_enabled"]: hardware_results["power_button"] = self._init_power_button() # 初始化遊戲內控制按鈕
            failed_components = [k for k, v in hardware_results.items() if not v]
            if failed_components:
                logging.warning(f"以下硬體組件初始化失敗: {failed_components}")
                if len(failed_components) > len(hardware_results) / 2:
                    logging.error("超過一半的硬體組件初始化失敗，停止啟動"); return False
            if self.config.config["debug"]["hardware_monitor"]: self._start_system_monitor()
            self._play_startup_sequence()
            logging.info("硬體初始化完成"); return True
        except Exception as e:
            logging.error(f"硬體初始化過程中發生嚴重錯誤: {e}\n{traceback.format_exc()}")
            self._cleanup_on_error(); return False

    def _init_gpio(self):
        try:
            GPIO.setmode(GPIO.BCM) # 設定 GPIO 模式為 BCM
            GPIO.setwarnings(False) # 關閉 GPIO 警告
            logging.info("GPIO 初始化成功"); return True
        except Exception as e: logging.error(f"GPIO 初始化失敗: {e}"); return False

    def _init_pygame(self):
        try:
            pygame.init()
            pygame.display.set_caption(f"多功能遊戲機 v{VERSION}")
            flags = pygame.DOUBLEBUF # 啟用雙緩衝
            if self.config.config["display"]["fullscreen"]: flags |= pygame.FULLSCREEN
            self.hdmi_screen = pygame.display.set_mode((self.config.config["display"]["hdmi_width"], self.config.config["display"]["hdmi_height"]), flags)
            self.clock = pygame.time.Clock()
            logging.info("Pygame 初始化成功")
            try: # 載入中文字型
                self.font_title_main = pygame.font.Font(CHINESE_FONT_PATH, 72)
                self.font_item_menu = pygame.font.Font(CHINESE_FONT_PATH, 48)
                self.font_info_menu = pygame.font.Font(CHINESE_FONT_PATH, 24)
                self.font_text_instruction = pygame.font.Font(CHINESE_FONT_PATH, 36)
                self.font_hint_instruction = pygame.font.Font(CHINESE_FONT_PATH, 48)
                self.font_large = pygame.font.Font(CHINESE_FONT_PATH, 72)
                self.font_medium = pygame.font.Font(CHINESE_FONT_PATH, 48)
                self.font_small = pygame.font.Font(CHINESE_FONT_PATH, 36)
                self.font_tiny = pygame.font.Font(CHINESE_FONT_PATH, 24)
                logging.info(f"已成功載入中文字型: {CHINESE_FONT_PATH}")
            except pygame.error as e:
                logging.error(f"載入中文字型 '{CHINESE_FONT_PATH}' 失敗: {e}. 將使用預設字型。")
                # 退回預設字型
                sizes = {"title_main": 72, "item_menu": 48, "info_menu": 24, "text_instruction": 36, "hint_instruction": 48, "large": 72, "medium": 48, "small": 36, "tiny": 24}
                for name, size in sizes.items(): setattr(self, f"font_{name}", pygame.font.Font(None, size))
            return True
        except Exception as e: logging.error(f"Pygame 初始化失敗: {e}"); return False

    def _init_spi_screen(self):
        try:
            logging.info("正在初始化SPI螢幕...")
            if not os.path.exists('/dev/spidev0.0'): logging.error("SPI接口未啟用"); return False
            self.spi_screen = SPIScreenManager()
            if self.spi_screen and self.spi_screen.device:
                logging.info("SPI 螢幕初始化成功")
                self.spi_screen.display_custom_message("SPI螢幕", "初始化成功", duration=1, title_color=self.spi_screen.GREEN); return True
            else: logging.error("SPI 螢幕設備創建失敗"); self._log_spi_diagnosis(); return False
        except ImportError as e: logging.error(f"SPI 螢幕套件導入失敗: {e}. 請安裝 luma.lcd luma.core pillow"); return False
        except Exception as e: logging.error(f"SPI 螢幕初始化錯誤: {e}\n{traceback.format_exc()}"); self._log_spi_diagnosis(); return False
    def _log_spi_diagnosis(self):
        try:
            logging.error(f"SPI診斷: SPI設備 {'存在' if os.path.exists('/dev/spidev0.0') else '未找到'}. 檢查接線(DC:25,RST:24,LED:27,CS:8),電源,SPI啟用,螢幕型號(ILI9341).")
        except Exception as e: logging.error(f"SPI診斷記錄失敗: {e}")

    def _init_keypad(self):
        try: self.keypad = MatrixKeypad(); logging.info("矩陣鍵盤初始化成功"); return True
        except Exception as e: logging.error(f"矩陣鍵盤初始化失敗: {e}"); return False

    def _init_controller(self):
        try:
            logging.info("正在初始化Xbox控制器...")
            pygame.joystick.quit(); pygame.joystick.init()
            if pygame.joystick.get_count() == 0: logging.warning("未檢測到任何遊戲控制器"); return False
            self.controller = XboxController()
            if self.controller and self.controller.is_connected:
                logging.info(f"Xbox 控制器初始化成功 - 檢測到 {pygame.joystick.get_count()} 個控制器 ({self.controller.controller.get_name() if self.controller.controller else 'N/A'})"); return True
            else: logging.error("Xbox 控制器物件創建失敗"); self._log_controller_diagnosis(); return False
        except Exception as e: logging.error(f"Xbox 控制器初始化錯誤: {e}\n{traceback.format_exc()}"); self._log_controller_diagnosis(); return False
    def _log_controller_diagnosis(self):
        try:
            logging.error(f"控制器診斷: 數量 {pygame.joystick.get_count()}. 檢查USB,電源,驅動,配對.")
            for i in range(pygame.joystick.get_count()):
                try: logging.error(f"  控制器 {i}: {pygame.joystick.Joystick(i).get_name()}")
                except Exception as e: logging.error(f"  控制器 {i}: 無法讀取 ({e})")
        except Exception as e: logging.error(f"控制器診斷記錄失敗: {e}")

    def _init_buzzer(self): # 使用 buzzer.py 中的 BuzzerControl
        try:
            logging.info("正在初始化蜂鳴器 (GPIO 18)...")
            # BuzzerControl 的 __init__ 會處理 GPIO.setup
            self.buzzer = BuzzerControl(pin=18, initial_volume=self.config.config["audio"]["volume"])
            if self.buzzer:
                logging.info("蜂鳴器初始化成功")
                # 測試音效 (可選)
                # self.buzzer.play_tone(frequency=800, duration=0.1); time.sleep(0.2)
                return True
            else: logging.error("蜂鳴器物件創建失敗"); return False
        except Exception as e: logging.error(f"蜂鳴器初始化錯誤: {e}\n{traceback.format_exc()}"); return False

    def _init_traffic_light(self):
        try:
            self.traffic_light = TrafficLight(red_pin=TRAFFIC_LIGHT_RED_PIN, yellow_pin=TRAFFIC_LIGHT_YELLOW_PIN, green_pin=TRAFFIC_LIGHT_GREEN_PIN)
            logging.info("交通燈初始化成功"); return True
        except Exception as e: logging.error(f"交通燈初始化失敗: {e}"); return False

    def _init_power_button(self): # 初始化遊戲內控制按鈕
        try:
            # 使用 power_button.py 中定義的 GAME_CONTROL_BUTTON_PIN (預設為 26)
            self.power_button = GameControlButton(main_console_instance=self, button_pin=GAME_CONTROL_BUTTON_PIN)
            self.power_button.start_monitoring()
            logging.info(f"遊戲內控制按鈕 (GPIO {GAME_CONTROL_BUTTON_PIN}) 初始化並開始監控"); return True
        except Exception as e: logging.error(f"遊戲內控制按鈕初始化失敗: {e}\n{traceback.format_exc()}"); return False

    def _start_system_monitor(self):
        try:
            self.monitor_running = True
            self.monitor_thread = threading.Thread(target=self._system_monitor_loop, daemon=True)
            self.monitor_thread.start(); logging.info("系統監控已啟動")
        except Exception as e: logging.error(f"系統監控啟動失敗: {e}")
    def _system_monitor_loop(self):
        while self.monitor_running:
            try:
                cpu = psutil.cpu_percent(); mem = psutil.virtual_memory().percent
                if cpu > 80: logging.warning(f"CPU 使用率過高: {cpu}%")
                if mem > 80: logging.warning(f"記憶體使用率過高: {mem}%")
                if self.controller and not self.controller.is_connected: self.controller.check_connection()
                time.sleep(5)
            except Exception as e: logging.error(f"系統監控錯誤: {e}"); time.sleep(1)

    def _play_startup_sequence(self):
        if self.config.config["audio"]["startup_sound"] and self.buzzer:
            try: self.buzzer.play_startup_melody()
            except Exception as e: logging.error(f"播放啟動音效失敗: {e}")
        if self.traffic_light:
            try:
                self.traffic_light.green_on(); time.sleep(0.3); self.traffic_light.yellow_on(); time.sleep(0.3)
                self.traffic_light.red_on(); time.sleep(0.3); self.traffic_light.all_off()
            except Exception as e: logging.error(f"啟動燈效失敗: {e}")

    def run(self):
        global shutdown_requested_by_signal
        if not self.initialize_hardware():
            logging.error("硬體初始化失敗，無法啟動遊戲機")
            self._show_error_message("硬體初始化失敗"); time.sleep(5); return
        if self.spi_screen and self.spi_screen.device:
            self.spi_screen.display_custom_message("遊戲機", f"版本 {VERSION}\n正在啟動...", duration=2)

        while self.running: # 主循環，由 self.running 和 shutdown_requested_by_signal 控制
            if shutdown_requested_by_signal:
                logging.info("偵測到關機請求信號，正在停止主循環...")
                self.running = False # 確保再次設定以防萬一
                break

            try:
                self._handle_power_button_events() # 處理遊戲內按鈕事件
                if self.config.config["debug"]["hardware_monitor"]: self.performance_monitor.update()
                self._handle_current_state()
                self._handle_pygame_events()
                self.clock.tick(self.config.config["display"]["fps"])
            except Exception as e:
                logging.error(f"主循環錯誤: {e}\n{traceback.format_exc()}"); self.state = GameState.ERROR

        logging.info("主循環已結束，執行清理...")
        self.cleanup() # 主循環結束後執行清理

    def _handle_power_button_events(self): # 處理來自 GameControlButton 的事件
        if not self.power_button: return
        events = self.power_button.get_pending_events()
        for event in events:
            action = event.get("action")
            logging.debug(f"處理遊戲控制按鈕事件: {action}")
            if action == 'toggle_pause': self._handle_pause_toggle()
            elif action == 'return_to_menu': self._handle_return_to_menu()

    def _handle_pause_toggle(self):
        if self.state == GameState.GAME:
            self.state = GameState.GAME_PAUSED
            if self.traffic_light: self.traffic_light.yellow_on()
            if self.buzzer: self.buzzer.play_tone("navigate")
            logging.info("遊戲已暫停")
        elif self.state == GameState.GAME_PAUSED:
            self.state = GameState.GAME
            if self.traffic_light: self.traffic_light.green_on()
            if self.buzzer: self.buzzer.play_tone("navigate")
            logging.info("遊戲已繼續")

    def _handle_return_to_menu(self):
        if self.state in [GameState.GAME, GameState.GAME_PAUSED, GameState.INSTRUCTION, GameState.GAME_OVER]:
            if self.current_game: self.end_current_game()
            self.state = GameState.MENU
            if self.traffic_light: self.traffic_light.all_off()
            if self.buzzer: self.buzzer.play_tone("back")
            logging.info("已返回主選單")

    def _handle_current_state(self):
        if self.state == GameState.STARTUP: self.state = GameState.MENU
        elif self.state == GameState.MENU: self._handle_menu()
        elif self.state == GameState.INSTRUCTION: self._handle_instruction()
        elif self.state == GameState.GAME_STARTING: self._handle_game_starting()
        elif self.state == GameState.GAME: self._handle_game()
        elif self.state == GameState.GAME_PAUSED: self._handle_game_paused()
        elif self.state == GameState.GAME_OVER: self._handle_game_over()
        elif self.state == GameState.ERROR: self._handle_error()

    def _handle_menu(self):
        if self.spi_screen and self.spi_screen.device: self.spi_screen.display_menu(self.games, self.current_selection)
        if self._can_process_input(): self._process_menu_input()
        if self.hdmi_screen:
            self.hdmi_screen.fill((0,0,0)); self._render_menu_on_hdmi()
            if self.config.config["debug"]["show_fps"]: self._render_debug_info()
            pygame.display.flip()
    def _can_process_input(self): return (time.time() - self.last_input_time) >= self.input_cooldown
    def _process_menu_input(self):
        if self.keypad:
            key = self.keypad.get_key()
            if key is not None:
                self.last_input_time = time.time()
                try:
                    val = int(key)
                    if 1 <= val <= 9 and val <= len(self.games):
                        if self.buzzer: self.buzzer.play_tone("select")
                        self.current_selection = val - 1; self.state = GameState.INSTRUCTION
                        if self.traffic_light: self.traffic_light.yellow_on()
                except ValueError:
                    if key == 'D' and self.traffic_light: self.traffic_light.all_off()
        if self.controller:
            ctrl_in = self.controller.get_input()
            if ctrl_in:
                detected = False
                if ctrl_in["up_pressed"]: self.current_selection = (self.current_selection - 1 + len(self.games)) % len(self.games); detected = True
                elif ctrl_in["down_pressed"]: self.current_selection = (self.current_selection + 1) % len(self.games); detected = True
                elif ctrl_in["a_pressed"]:
                    if self.buzzer: self.buzzer.play_tone("select")
                    self.state = GameState.INSTRUCTION
                    if self.traffic_light: self.traffic_light.yellow_on(); detected = True
                if detected:
                    self.last_input_time = time.time()
                    if self.buzzer and (ctrl_in["up_pressed"] or ctrl_in["down_pressed"]): self.buzzer.play_tone("navigate")

    def _handle_instruction(self):
        game_data = self.games[self.current_selection]
        if self.spi_screen and self.spi_screen.device: self.spi_screen.display_game_instructions(game_data)
        if self._can_process_input():
            if self.keypad and self.keypad.get_key() == "A": self._start_game_sequence(game_data)
            elif self.keypad and self.keypad.get_key() == "D": self._return_to_menu()
            if self.controller:
                ctrl_in = self.controller.get_input()
                if ctrl_in and ctrl_in["a_pressed"]: self._start_game_sequence(game_data)
                elif ctrl_in and ctrl_in["b_pressed"]: self._return_to_menu()
        if self.hdmi_screen: self.hdmi_screen.fill((0,0,0)); self._render_instructions_on_hdmi(game_data); pygame.display.flip()
    def _start_game_sequence(self, game_data):
        if self.buzzer: self.buzzer.play_tone("game_start")
        self.state = GameState.GAME_STARTING; self.game_start_time = time.time(); self.selected_game_data = game_data
    def _return_to_menu(self): # 重複的方法，但為了清晰保留
        if self.buzzer: self.buzzer.play_tone("back")
        if self.traffic_light: self.traffic_light.all_off()
        self.state = GameState.MENU

    def _handle_game_starting(self):
        elapsed = time.time() - self.game_start_time
        if elapsed < 1.5:
            countdown = 3 - int(elapsed / 0.5)
            if countdown > 0:
                if self.traffic_light:
                    if countdown == 3: self.traffic_light.red_on()
                    elif countdown == 2: self.traffic_light.yellow_on()
                    elif countdown == 1: self.traffic_light.green_on()
                if self.buzzer and int(elapsed * 2) != getattr(self, '_last_beep', -1):
                    self.buzzer.play_tone(frequency=300 + countdown * 200, duration=0.2); self._last_beep = int(elapsed * 2)
        else: self._actually_start_game(self.selected_game_data)
    def _actually_start_game(self, game_data):
        try:
            self.current_game = game_data["game_class"](width=self.config.config["display"]["hdmi_width"], height=self.config.config["display"]["hdmi_height"], buzzer=self.buzzer)
            self.state = GameState.GAME; self.session_stats["games_played"] += 1
            if self.spi_screen and self.spi_screen.device: self.spi_screen.clear_screen()
            logging.info(f"遊戲 '{game_data['name']}' 已啟動")
        except Exception as e:
            logging.error(f"啟動遊戲 '{game_data['name']}' 失敗: {e}\n{traceback.format_exc()}")
            self._show_error_message(f"遊戲啟動失敗"); self.state = GameState.MENU

    def _handle_game(self):
        if self.current_game:
            ctrl_in = self.controller.get_input() if self.controller else {}

            # --- MODIFICATION START: Handle Xbox BACK button ---
            if ctrl_in and ctrl_in.get("back_pressed"):
                if self._can_process_input(): # Use existing input cooldown
                    logging.info("偵測到 Xbox 控制器 BACK 鍵按下，返回主選單。")
                    self._handle_return_to_menu() # Call existing return to menu method
                    self.last_input_time = time.time() # Update last input time
                    return # Return immediately, skip further game logic for this frame
            # --- MODIFICATION END ---

            status = self.current_game.update(ctrl_in)
            if status.get("game_over", False):
                self.state = GameState.GAME_OVER; self.game_over_data = status
                score = status.get("score", 0); self.session_stats["total_score"] += score
                name = self.games[self.current_selection]["name"]
                self.session_stats["best_scores"][name] = max(self.session_stats["best_scores"].get(name, 0), score)
            elif self.hdmi_screen: self.current_game.render(self.hdmi_screen); pygame.display.flip()

    def _handle_game_paused(self):
        if self.hdmi_screen and self.font_large and self.font_small:
            self.hdmi_screen.fill((0,0,0))
            txt_s = self.font_large.render("遊戲已暫停", True, (255,255,255)); rect = txt_s.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2))
            self.hdmi_screen.blit(txt_s, rect)
            hint_s = self.font_small.render("按遊戲控制鈕繼續", True, (200,200,200)); hint_r = hint_s.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2 + 100))
            self.hdmi_screen.blit(hint_s, hint_r)
            pygame.display.flip()

    def _handle_game_over(self):
        if not hasattr(self, '_game_over_start_time'):
            self._game_over_start_time = time.time()
            if self.buzzer: self.buzzer.play_tone("game_over")
            if self.traffic_light: self.traffic_light.red_on()
            if self.spi_screen and self.spi_screen.device:
                self.spi_screen.display_game_over(self.game_over_data.get("score",0), self.session_stats["best_scores"].get(self.games[self.current_selection]["name"]))
            logging.info(f"遊戲結束，分數: {self.game_over_data.get('score',0)}")
        if time.time() - self._game_over_start_time > 3: # 3秒後自動返回選單
            self._handle_return_to_menu() # 使用返回選單的統一方法
            delattr(self, '_game_over_start_time')

    def _handle_error(self):
        if self.hdmi_screen and self.font_medium:
            self.hdmi_screen.fill((50,0,0))
            txt_s = self.font_medium.render("系統錯誤", True, (255,255,255)); rect = txt_s.get_rect(center=(self.hdmi_screen.get_width()//2, self.hdmi_screen.get_height()//2))
            self.hdmi_screen.blit(txt_s, rect); pygame.display.flip()
        time.sleep(0.1)

    def _handle_pygame_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.GAME or self.state == GameState.GAME_PAUSED: self._handle_return_to_menu()
                    else: self.running = False
                elif event.key == pygame.K_F1: self.config.config["debug"]["show_fps"] = not self.config.config["debug"]["show_fps"]

    def _render_debug_info(self):
        if not self.hdmi_screen or not self.font_tiny: return
        y = 10; fps = self.font_tiny.render(f"FPS: {self.performance_monitor.get_average_fps():.1f}", True, (255,255,255))
        self.hdmi_screen.blit(fps, (10,y)); y+=25
        cpu = self.font_tiny.render(f"CPU: {self.performance_monitor.cpu_usage:.1f}%", True, (255,255,255))
        self.hdmi_screen.blit(cpu, (10,y)); y+=25
        mem = self.font_tiny.render(f"Memory: {self.performance_monitor.memory_usage:.1f}%", True, (255,255,255))
        self.hdmi_screen.blit(mem, (10,y)); y+=25
        if self.performance_monitor.temperature > 0:
            temp = self.font_tiny.render(f"Temp: {self.performance_monitor.temperature:.1f}°C", True, (255,255,255))
            self.hdmi_screen.blit(temp, (10,y))

    def _show_error_message(self, message):
        logging.error(message)
        if self.spi_screen and self.spi_screen.device: self.spi_screen.display_custom_message("錯誤", message, duration=3)

    def _render_menu_on_hdmi(self):
        if not (self.hdmi_screen and self.font_title_main and self.font_item_menu and self.font_info_menu): return
        title_s = self.font_title_main.render(f"多功能遊戲機 v{VERSION}", True, (255,255,255))
        self.hdmi_screen.blit(title_s, (HDMI_SCREEN_WIDTH//2 - title_s.get_width()//2, 50))
        
        # Session statistics in top-right corner with smaller font
        stats_t = f"本次遊玩: {self.session_stats['games_played']} 場 | 總分: {self.session_stats['total_score']}"
        if self.font_tiny:  # Use smaller font
            stats_s = self.font_tiny.render(stats_t, True, (150,150,150))
        else:
            stats_s = self.font_info_menu.render(stats_t, True, (150,150,150))
        # Position in top-right corner
        stats_x = HDMI_SCREEN_WIDTH - stats_s.get_width() - 10
        stats_y = 10
        self.hdmi_screen.blit(stats_s, (stats_x, stats_y))
        
        for i, game in enumerate(self.games):
            color = (255,255,0) if i == self.current_selection else (200,200,200); y_pos = 150 + i * 45
            item_s = self.font_item_menu.render(f"{game['id']}. {game['name']}", True, color)
            self.hdmi_screen.blit(item_s, (50, y_pos))
            diff_c = {"Easy":(0,255,0),"Medium":(255,255,0),"Hard":(255,0,0)}.get(game.get("difficulty","Medium"),(255,255,255))
            diff_s = self.font_info_menu.render(f"[{game.get('difficulty','Medium')}]", True, diff_c)
            self.hdmi_screen.blit(diff_s, (600, y_pos + 10))

    def _render_instructions_on_hdmi(self, game_data):
        if not (self.hdmi_screen and self.font_title_main and self.font_text_instruction and self.font_hint_instruction): return
        title_s = self.font_title_main.render(game_data["name"], True, (255,255,255))
        self.hdmi_screen.blit(title_s, (HDMI_SCREEN_WIDTH//2 - title_s.get_width()//2, 80))  # Changed from 100 to 80
        diff = game_data.get("difficulty","Medium")
        diff_c = {"Easy":(0,255,0),"Medium":(255,255,0),"Hard":(255,0,0)}.get(diff,(255,255,255))
        diff_s = self.font_text_instruction.render(f"難度: {diff}", True, diff_c)
        self.hdmi_screen.blit(diff_s, (HDMI_SCREEN_WIDTH//2 - diff_s.get_width()//2, 180))  # Changed from 160 to 180
        desc_lines = game_data["description"].split('。'); y_offset = 0
        for line in desc_lines:
            if line.strip():
                desc_s = self.font_text_instruction.render(line.strip()+"。", True, (200,200,200))
                self.hdmi_screen.blit(desc_s, (HDMI_SCREEN_WIDTH//2 - desc_s.get_width()//2, 220 + y_offset)); y_offset += 40
        hint_s = self.font_hint_instruction.render("按 A/確認 開始遊戲 或 B/返回 返回選單", True, (150,150,150))
        self.hdmi_screen.blit(hint_s, (HDMI_SCREEN_WIDTH//2 - hint_s.get_width()//2, HDMI_SCREEN_HEIGHT - 100))

    def end_current_game(self):
        if self.current_game:
            if hasattr(self.current_game, 'cleanup'): self.current_game.cleanup()
            self.current_game = None; logging.info("當前遊戲已結束並清理")

    def _cleanup_on_error(self):
        logging.info("執行錯誤清理...")
        if self.spi_screen: self.spi_screen.cleanup()
        if self.keypad: self.keypad.cleanup()
        if self.controller: self.controller.cleanup()
        if self.buzzer: self.buzzer.cleanup()
        if self.traffic_light: self.traffic_light.cleanup()
        if self.power_button: self.power_button.cleanup() # 清理遊戲內控制按鈕
        if pygame.get_init(): pygame.quit()

    def cleanup(self):
        logging.info("開始系統清理...")
        if self.monitor_running:
            self.monitor_running = False
            if self.monitor_thread and self.monitor_thread.is_alive(): self.monitor_thread.join(timeout=1)
        self.end_current_game()
        try: self.config.save_config(); self._save_session_stats()
        except Exception as e: logging.error(f"儲存數據失敗: {e}")

        # 清理順序調整，先清理依賴 Pygame 的，最後關閉 Pygame
        if self.buzzer: self.buzzer.cleanup()
        if self.power_button: self.power_button.cleanup() # 清理 GameControlButton
        if self.spi_screen: self.spi_screen.cleanup()
        if self.keypad: self.keypad.cleanup()
        if self.controller: self.controller.cleanup()
        if self.traffic_light: self.traffic_light.cleanup()

        if pygame.get_init(): pygame.quit(); logging.info("Pygame 已關閉")
        # GPIO.cleanup() 會在主程式的 finally 區塊執行
        logging.info("遊戲機系統清理完成 (GPIO 清理將在主腳本結束時進行)")

    def _save_session_stats(self):
        try:
            stats_file = os.path.join(os.path.dirname(__file__), 'session_stats.json'); all_stats = {}
            if os.path.exists(stats_file):
                with open(stats_file, 'r', encoding='utf-8') as f: all_stats = json.load(f)
            session_id = self.session_stats["start_time"].strftime("%Y%m%d_%H%M%S")
            all_stats[session_id] = {
                "start_time": self.session_stats["start_time"].isoformat(), "end_time": datetime.now().isoformat(),
                "games_played": self.session_stats["games_played"], "total_score": self.session_stats["total_score"],
                "best_scores": self.session_stats["best_scores"]
            }
            if len(all_stats) > 30:
                for old_session in sorted(all_stats.keys())[:-30]: del all_stats[old_session]
            with open(stats_file, 'w', encoding='utf-8') as f: json.dump(all_stats, f, indent=2, ensure_ascii=False)
            logging.info(f"會話統計已儲存: {session_id}")
        except Exception as e: logging.error(f"儲存統計數據失敗: {e}")

if __name__ == "__main__":
    # 設定日誌 (如果 EnhancedGameConsole 未設定 StreamHandler，可以在此處補上)
    # EnhancedGameConsole._setup_logging() 已經包含了 StreamHandler

    # 設定 SIGUSR1 信號處理器
    signal.signal(signal.SIGUSR1, signal_handler_usr1)

    power_button_process = None
    game_console_instance = None # 初始化為 None

    try:
        main_pid = str(os.getpid())
        # 確保 power_button.py 在與 main.py 相同的目錄下
        power_button_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "power_button.py")

        if os.path.exists(power_button_script_path):
            logging.info(f"嘗試啟動 power_button.py (主程序 PID: {main_pid})...")
            # 使用 sudo 執行 power_button.py 以便其有權限執行 shutdown
            power_button_process = subprocess.Popen(
                ['sudo', 'python3', power_button_script_path, main_pid],
                preexec_fn=os.setpgrp # 創建新的進程組，方便後續一起終止
            )
            logging.info(f"power_button.py 已在背景啟動 (子程序 PID: {power_button_process.pid})")
        else:
            logging.warning(f"警告: power_button.py 未找到於: {power_button_script_path}")

        game_console_instance = EnhancedGameConsole()
        game_console_instance_for_signal = game_console_instance # 使其可被信號處理器訪問
        game_console_instance.run() # 啟動遊戲機主循環

    except KeyboardInterrupt:
        logging.info("主程式被使用者中斷 (Ctrl+C)")
        if game_console_instance:
            game_console_instance.running = False # 通知主循環停止
    except Exception as e:
        logging.error(f"主程式發生未預期錯誤: {e}\n{traceback.format_exc()}")
    finally:
        logging.info("主程式 finally 區塊開始執行清理...")

        # 確保在 game_console_instance 存在且其 run 方法已結束後才調用 cleanup
        # 如果 run() 是因為異常退出，可能需要手動調用 cleanup
        # 但正常的流程是 run() 結束後會自行調用 cleanup()
        if game_console_instance and not game_console_instance.running: # 如果是因為 running=False 退出循環
             pass # cleanup 已在 run() 結束時調用
        elif game_console_instance: # 如果是因為其他原因 (如 KeyboardInterrupt) 導致 run() 未完成
            logging.info("由於 KeyboardInterrupt 或其他異常，手動觸發 EnhancedGameConsole 清理...")
            game_console_instance.cleanup()

        # 終止 power_button.py 子程序
        if power_button_process and power_button_process.poll() is None: # 檢查進程是否仍在運行
            logging.info(f"嘗試終止 power_button.py 子程序 (PID: {power_button_process.pid})...")
            try:
                # 發送 SIGTERM 給整個進程組
                os.killpg(os.getpgid(power_button_process.pid), signal.SIGTERM)
                power_button_process.wait(timeout=2) # 等待子程序終止
                logging.info("power_button.py 子程序已成功終止 (SIGTERM)")
            except ProcessLookupError:
                logging.warning("power_button.py 子程序已自行結束。")
            except subprocess.TimeoutExpired:
                logging.warning("終止 power_button.py 超時，嘗試 SIGKILL...")
                try:
                    os.killpg(os.getpgid(power_button_process.pid), signal.SIGKILL)
                    power_button_process.wait(timeout=1)
                    logging.info("power_button.py 子程序已成功終止 (SIGKILL)")
                except Exception as e_kill:
                    logging.error(f"使用 SIGKILL 終止 power_button.py 失敗: {e_kill}")
            except Exception as e_term:
                logging.error(f"終止 power_button.py 時發生其他錯誤: {e_term}")

        # 最終的 GPIO 清理
        # 確保在所有 GPIO 操作都完成後執行
        # EnhancedGameConsole.cleanup() 內部不應再調用 GPIO.cleanup()
        # 應由主腳本的最後來執行
        if GPIO.getmode() is not None: # 檢查 GPIO 是否曾被設定模式
            logging.info("執行最終的 GPIO.cleanup()...")
            GPIO.cleanup()

        logging.info("主程式已結束。")