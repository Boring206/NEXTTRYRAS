#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# power_button.py - 處理遊戲內控制按鈕事件及系統關機按鈕

import RPi.GPIO as GPIO
import time
import os
import signal
import subprocess
import threading
import queue
import logging
import sys

# --- GPIO 設定 (BCM 模式) ---
# 此按鈕用於遊戲內的「暫停/返回選單」等操作，由 GameControlButton 類別處理
# ****** 已將預設值從 26 修改為 5，以避免與矩陣鍵盤的 GPIO 26 衝突 ******
# ****** 請確保 GPIO 5 在您的系統上是空閒的，並將按鈕連接到此引腳 ******
GAME_CONTROL_BUTTON_PIN = 5
# 此按鈕用於「長按關機」，由腳本主執行緒 (if __name__ == "__main__":) 處理
# ****** 已將 GPIO 3 修改為 GPIO 22，以避免與交通燈黃燈衝突 ******
# ****** 新接線方式：3.3V -> 按鈕一端 -> GPIO 22，使用內部下拉電阻 ******
SYSTEM_SHUTDOWN_BUTTON_PIN = 22

# --- 按鈕參數 ---
DEBOUNCE_TIME_GAME_CONTROL = 0.05
DEBOUNCE_TIME_SHUTDOWN = 0.05
LONG_PRESS_DURATION = 3

if __name__ == "__main__":
    log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    logger = logging.getLogger("PowerButtonScript")
else:
    logger = logging.getLogger(__name__)


class GameControlButton:
    def __init__(self, main_console_instance, button_pin=GAME_CONTROL_BUTTON_PIN): # 使用更新後的預設 PIN
        self.main_console = main_console_instance
        self.button_pin = button_pin
        self.event_queue = queue.Queue()
        self._monitoring_thread = None
        self._stop_monitoring = threading.Event()
        self.last_press_time = 0

        try:
            # GPIO.setmode(GPIO.BCM) # 由主程式設定
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info(f"GameControlButton 初始化於 GPIO {self.button_pin}")
        except RuntimeError as e:
            logger.error(f"GameControlButton GPIO {self.button_pin} 設定失敗: {e}. 可能已被使用或模式衝突。")
            raise # 讓主程式知道初始化失敗

    def start_monitoring(self):
        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._stop_monitoring.clear()
            self._monitoring_thread = threading.Thread(target=self._monitor_button, daemon=True)
            self._monitoring_thread.start()
            logger.info(f"GameControlButton 開始監控 GPIO {self.button_pin}")

    def _monitor_button(self):
        press_count = 0
        short_press_detected_time = 0
        button_held_down = False # 新增狀態，追蹤按鈕是否持續按下

        while not self._stop_monitoring.is_set():
            try:
                current_button_state = GPIO.input(self.button_pin) == GPIO.LOW # True if pressed

                if current_button_state: # 按鈕被按下
                    if not button_held_down: # 之前是釋放狀態，現在剛按下
                        button_held_down = True
                        current_time = time.time()
                        if (current_time - self.last_press_time) > DEBOUNCE_TIME_GAME_CONTROL:
                            # 記錄按鈕按下的時間點
                            button_down_time = current_time
                            time.sleep(0.02) # 短暫延遲以確認是穩定按下

                            # 等待按鈕釋放或持續按下超過短按定義的時間
                            # 這個迴圈用於確定是短按還是其他（如果需要更複雜的長按檢測）
                            # 但對於 GameControlButton，我們主要關心短按釋放
                            # 為了簡化，我們在按鈕釋放時判斷按下次數
                            
                            # 在 main.py 中，GameControlButton 的事件是基於短按的
                            # 這裡的邏輯是，每次有效的按下（去抖動後）就增加 press_count
                            # 並在一定時間內根據 press_count 決定事件類型
                            
                            press_count += 1
                            if press_count == 1: # 第一次短按
                                short_press_detected_time = current_time
                                # 事件在釋放時或計時後發送可能更好，但目前邏輯是立即計數
                                # 為了符合 main.py 中 toggle_pause/return_to_menu 的預期，
                                # 我們這裡只記錄按下次數，具體事件由 main.py 判斷。
                                # 或者，我們可以在這裡決定事件類型。
                                # 為了更精確的單擊/雙擊，事件應該在按鈕釋放時產生。
                                logger.debug(f"GameControl 按鈕 (GPIO {self.button_pin}) 偵測到按下，計數: {press_count}")


                            self.last_press_time = current_time # 更新的是有效按下的時間
                else: # 按鈕被釋放
                    if button_held_down: # 之前是按下狀態，現在剛釋放
                        button_held_down = False
                        current_time = time.time()
                        logger.debug(f"GameControl 按鈕 (GPIO {self.button_pin}) 釋放")

                        if press_count == 1 and (current_time - short_press_detected_time) < 1.0 : # 1秒內的第一次有效按下後釋放
                            logger.info(f"GameControl 按鈕 (GPIO {self.button_pin}) 短按1次事件")
                            self.event_queue.put({"action": "toggle_pause", "timestamp": current_time})
                            # press_count = 0 # 單擊後重置或等待超時重置
                        elif press_count >= 2 and (current_time - short_press_detected_time) < 1.0: # 1秒內的第二次或更多次按下後釋放
                            logger.info(f"GameControl 按鈕 (GPIO {self.button_pin}) 短按2+次事件 -> 返回選單")
                            self.event_queue.put({"action": "return_to_menu", "timestamp": current_time})
                            press_count = 0 # 雙擊後重置
                
                # 超時重置 press_count
                if press_count > 0 and (time.time() - short_press_detected_time) >= 1.0:
                    if press_count == 1 and not button_held_down: # 如果是單擊且已釋放，並且超時
                         # 這個邏輯可能需要調整，因為單擊事件已在釋放時發送
                         # 此處重置是為了下一次點擊序列
                        logger.debug(f"GameControl 按鈕計數超時重置 (之前計數: {press_count})")
                    press_count = 0


                time.sleep(0.02)
            except RuntimeError as e:
                logger.error(f"GameControlButton 監控 GPIO {self.button_pin} 時發生 RuntimeError: {e}")
                break
            except Exception as e:
                logger.error(f"GameControlButton 監控時發生未知錯誤: {e}", exc_info=True)
                time.sleep(0.1)

    def get_pending_events(self):
        events = []
        while not self.event_queue.empty():
            try: events.append(self.event_queue.get_nowait())
            except queue.Empty: break
        return events

    def stop_monitoring(self):
        logger.info(f"GameControlButton 停止監控 GPIO {self.button_pin}")
        self._stop_monitoring.set()
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=1.0)
        self._monitoring_thread = None

    def cleanup(self):
        self.stop_monitoring()
        logger.info(f"GameControlButton (GPIO {self.button_pin}) 清理完成")

def handle_shutdown_signal(signum, frame):
    logger.info(f"接收到信號 {signum}，準備關機。")
    perform_shutdown("接收到外部信號")

def perform_shutdown(reason=""):
    logger.info(f"執行系統關機... 原因: {reason}")
    try: subprocess.call(['sudo', 'shutdown', '-h', 'now'])
    except Exception as e: logger.error(f"執行關機指令失敗: {e}")
    sys.exit(0)

def monitor_system_shutdown_button(main_process_pid=None):
    try:
        GPIO.setmode(GPIO.BCM)
        # 修改為下拉電阻，因為新接線方式是 3.3V -> 按鈕 -> GPIO 22
        GPIO.setup(SYSTEM_SHUTDOWN_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    except RuntimeError as e:
        # 如果是因為 'A physical pull up resistor is fitted on this channel!'
        # 仍然可以繼續，但如果是其他 RuntimeError，則可能是問題
        if "pull up resistor is fitted" in str(e):
            logger.warning(f"GPIO {SYSTEM_SHUTDOWN_BUTTON_PIN} 設定警告: {e} (通常可忽略)")
        else:
            logger.error(f"系統關機按鈕 GPIO {SYSTEM_SHUTDOWN_BUTTON_PIN} 設定失敗: {e}")
            return # 無法監控

    logger.info(f"系統關機按鈕監控已啟動於 GPIO {SYSTEM_SHUTDOWN_BUTTON_PIN}")
    if main_process_pid: logger.info(f"將在關機前嘗試通知主程序 PID: {main_process_pid}")

    last_input_time = 0
    button_pressed_time = None

    while True:
        try:
            # 修改邏輯：使用下拉電阻時，按下為 HIGH，釋放為 LOW
            if GPIO.input(SYSTEM_SHUTDOWN_BUTTON_PIN) == GPIO.HIGH:
                current_time = time.time()
                if (current_time - last_input_time) > DEBOUNCE_TIME_SHUTDOWN:
                    if button_pressed_time is None:
                        button_pressed_time = current_time
                        logger.debug(f"系統關機按鈕 (GPIO {SYSTEM_SHUTDOWN_BUTTON_PIN}) 按下")
                    if (current_time - button_pressed_time) >= LONG_PRESS_DURATION:
                        logger.info(f"系統關機按鈕長按 {LONG_PRESS_DURATION} 秒，觸發關機。")
                        if main_process_pid:
                            try:
                                os.kill(main_process_pid, signal.SIGUSR1)
                                logger.info(f"已發送 SIGUSR1 信號至 PID {main_process_pid}")
                                time.sleep(2)
                            except ProcessLookupError: logger.warning(f"主程序 PID {main_process_pid} 未找到。")
                            except Exception as e: logger.error(f"發送信號至 PID {main_process_pid} 失敗: {e}")
                        perform_shutdown(f"按鈕長按 {LONG_PRESS_DURATION} 秒")
                last_input_time = current_time
            else:
                if button_pressed_time is not None: logger.debug(f"系統關機按鈕 (GPIO {SYSTEM_SHUTDOWN_BUTTON_PIN}) 釋放")
                button_pressed_time = None
            time.sleep(0.1)
        except KeyboardInterrupt: logger.info("系統關機按鈕監控被手動中斷 (Ctrl+C)"); break
        except RuntimeError as e: logger.error(f"系統關機按鈕監控時發生 RuntimeError: {e}"); break
        except Exception as e: logger.error(f"系統關機按鈕監控時發生未知錯誤: {e}", exc_info=True); time.sleep(1)
    
    # GPIO.cleanup([SYSTEM_SHUTDOWN_BUTTON_PIN]) # 主程式會統一清理
    logger.info("系統關機按鈕監控已停止。")

if __name__ == "__main__":
    logger.info("power_button.py 作為主腳本啟動...")
    main_pid = None
    if len(sys.argv) > 1:
        try: main_pid = int(sys.argv[1]); logger.info(f"接收到主遊戲程式 PID: {main_pid}")
        except ValueError: logger.warning(f"無效的主程式 PID 參數: {sys.argv[1]}")
    try:
        monitor_system_shutdown_button(main_process_pid=main_pid)
    except Exception as e: logger.error(f"power_button.py 主執行緒發生嚴重錯誤: {e}", exc_info=True)
    finally:
        logger.info("power_button.py 主腳本結束。")
        # GPIO.cleanup() # 讓主程式的 finally 區塊負責最終的 GPIO.cleanup()
