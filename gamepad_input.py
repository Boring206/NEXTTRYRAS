#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# gamepad_input.py - 遊戲控制器輸入處理

import pygame
import time
import logging
import sys # 用於在測試時清除行

logger = logging.getLogger(__name__)

class XboxController:
    # ==============================================================================
    # << 請根據您的手把測試結果修改以下按鈕和軸的索引 >>
    # 不同的手把，甚至同一手把在不同模式下，這些對應都可能不同。
    # 執行 `python3 gamepad_input.py` 來找出您手把的正確對應。
    # ==============================================================================

    # 按鈕 (Buttons) - 範例值，基於常見的 Xbox 控制器
    BUTTON_A = 0      # 通常是南邊的按鈕 (例如 Xbox 的 A, PS 的 X)
    BUTTON_B = 1      # 通常是東邊的按鈕 (例如 Xbox 的 B, PS 的 O)
    BUTTON_X = 2      # 通常是西邊的按鈕 (例如 Xbox 的 X, PS 的 □)
    BUTTON_Y = 3      # 通常是北邊的按鈕 (例如 Xbox 的 Y, PS 的 Δ)
    BUTTON_LB = 4     # 左上肩鍵 (Left Bumper)
    BUTTON_RB = 5     # 右上肩鍵 (Right Bumper)
    BUTTON_BACK = 6   # "Back", "Select", "View" 或類似按鈕
    BUTTON_START = 7  # "Start", "Menu", "Options" 或類似按鈕
    BUTTON_LS = 8     # 左搖桿按下 (Left Stick pressed)
    BUTTON_RS = 9     # 右搖桿按下 (Right Stick pressed)
    # 如果您的手把有更多按鈕，可以繼續添加，例如 BUTTON_GUIDE = 10 等

    # 軸 (Axes) - 範例值
    AXIS_LEFT_STICK_X = 0  # 左搖桿 X (-1.0 左, 1.0 右)
    AXIS_LEFT_STICK_Y = 1  # 左搖桿 Y (-1.0 上, 1.0 下) - Pygame 通常上方為負
    AXIS_RIGHT_STICK_X = 3 # 右搖桿 X
    AXIS_RIGHT_STICK_Y = 4 # 右搖桿 Y
    AXIS_LT = 2           # 左扳機 (Left Trigger, Pygame 中通常是 -1.0 未按 到 1.0 全按)
    AXIS_RT = 5           # 右扳機 (Right Trigger)
    # 某些手把可能將 LT/RT 合併為一個軸，或者有不同的軸數量和順序

    # 方向鍵 (Hat - 通常只有一個 hat，索引為 0)
    HAT_INDEX = 0 # Pygame 中第一個方向鍵(hat)的索引

    # 搖桿死區，避免微小移動被偵測
    STICK_DEADZONE = 0.25
    TRIGGER_THRESHOLD = 0.5 # 扳機被視為「按下」的閾值 (標準化後的 0-1 值)

    def __init__(self, joystick_id=0):
        self.joystick_id = joystick_id
        self.controller = None
        self.is_connected = False
        self.last_input_time = 0
        self.input_cooldown = 0.03 # 輸入處理的最小間隔，防止過於頻繁

        self.button_states = {} 
        self.prev_button_states = {}
        self.dpad_state = (0,0)
        self.prev_dpad_state = (0,0)

        if not pygame.joystick.get_init():
            logger.warning("Pygame joystick 模組未初始化。請在主程式中調用 pygame.joystick.init()")

        if pygame.joystick.get_count() > joystick_id:
            try:
                self.controller = pygame.joystick.Joystick(joystick_id)
                self.controller.init()
                self.is_connected = True
                logger.info(f"控制器 '{self.controller.get_name()}' (ID: {joystick_id}) 連接成功。")
                logger.info(f"  按鈕數量: {self.controller.get_numbuttons()}")
                logger.info(f"  軸數量: {self.controller.get_numaxes()}")
                logger.info(f"  方向鍵(Hats)數量: {self.controller.get_numhats()}")

                for i in range(self.controller.get_numbuttons()):
                    self.button_states[i] = False
                    self.prev_button_states[i] = False
            except pygame.error as e:
                logger.error(f"初始化控制器 ID {joystick_id} 失敗: {e}")
                self.controller = None; self.is_connected = False
        else:
            logger.warning(f"未找到 ID 為 {joystick_id} 的控制器。")

    def check_connection(self): # Pygame 通常透過事件處理插拔
        return self.is_connected

    def get_input(self):
        if not self.is_connected or not self.controller:
            return None

        # current_time = time.time() # 如果需要冷卻時間控制
        # if current_time - self.last_input_time < self.input_cooldown:
        #     return None 
        # self.last_input_time = current_time

        pygame.event.pump() 

        self.prev_button_states = self.button_states.copy()
        for i in range(self.controller.get_numbuttons()):
            self.button_states[i] = self.controller.get_button(i)
        
        self.prev_dpad_state = self.dpad_state
        if self.controller.get_numhats() > 0:
            self.dpad_state = self.controller.get_hat(self.HAT_INDEX)
        else:
            self.dpad_state = (0,0)

        # 處理軸
        num_axes = self.controller.get_numaxes()
        left_stick_x = self.controller.get_axis(self.AXIS_LEFT_STICK_X) if num_axes > self.AXIS_LEFT_STICK_X else 0.0
        left_stick_y = self.controller.get_axis(self.AXIS_LEFT_STICK_Y) if num_axes > self.AXIS_LEFT_STICK_Y else 0.0
        right_stick_x = self.controller.get_axis(self.AXIS_RIGHT_STICK_X) if num_axes > self.AXIS_RIGHT_STICK_X else 0.0
        right_stick_y = self.controller.get_axis(self.AXIS_RIGHT_STICK_Y) if num_axes > self.AXIS_RIGHT_STICK_Y else 0.0
        
        # 扳機值 (Pygame 原始值通常是 -1.0 到 1.0)
        raw_lt_value = self.controller.get_axis(self.AXIS_LT) if num_axes > self.AXIS_LT else -1.0
        raw_rt_value = self.controller.get_axis(self.AXIS_RT) if num_axes > self.AXIS_RT else -1.0
        
        # 標準化扳機值到 0.0 (未按) 到 1.0 (全按)
        lt_value_normalized = (raw_lt_value + 1.0) / 2.0
        rt_value_normalized = (raw_rt_value + 1.0) / 2.0

        # 應用死區
        if abs(left_stick_x) < self.STICK_DEADZONE: left_stick_x = 0.0
        if abs(left_stick_y) < self.STICK_DEADZONE: left_stick_y = 0.0
        if abs(right_stick_x) < self.STICK_DEADZONE: right_stick_x = 0.0
        if abs(right_stick_y) < self.STICK_DEADZONE: right_stick_y = 0.0

        input_map = {
            "left_stick_x": left_stick_x, "left_stick_y": left_stick_y,
            "right_stick_x": right_stick_x, "right_stick_y": right_stick_y,
            "lt_pressed": lt_value_normalized > self.TRIGGER_THRESHOLD,
            "rt_pressed": rt_value_normalized > self.TRIGGER_THRESHOLD,
            "lt_value": lt_value_normalized, "rt_value": rt_value_normalized,

            "a_down": self.button_states.get(self.BUTTON_A, False),
            "b_down": self.button_states.get(self.BUTTON_B, False),
            "x_down": self.button_states.get(self.BUTTON_X, False),
            "y_down": self.button_states.get(self.BUTTON_Y, False),
            "lb_down": self.button_states.get(self.BUTTON_LB, False),
            "rb_down": self.button_states.get(self.BUTTON_RB, False),
            "back_down": self.button_states.get(self.BUTTON_BACK, False),
            "start_down": self.button_states.get(self.BUTTON_START, False),
            "ls_down": self.button_states.get(self.BUTTON_LS, False),
            "rs_down": self.button_states.get(self.BUTTON_RS, False),

            "a_pressed": self.button_states.get(self.BUTTON_A, False) and not self.prev_button_states.get(self.BUTTON_A, False),
            "b_pressed": self.button_states.get(self.BUTTON_B, False) and not self.prev_button_states.get(self.BUTTON_B, False),
            "x_pressed": self.button_states.get(self.BUTTON_X, False) and not self.prev_button_states.get(self.BUTTON_X, False),
            "y_pressed": self.button_states.get(self.BUTTON_Y, False) and not self.prev_button_states.get(self.BUTTON_Y, False),
            "lb_pressed": self.button_states.get(self.BUTTON_LB, False) and not self.prev_button_states.get(self.BUTTON_LB, False),
            "rb_pressed": self.button_states.get(self.BUTTON_RB, False) and not self.prev_button_states.get(self.BUTTON_RB, False),
            "back_pressed": self.button_states.get(self.BUTTON_BACK, False) and not self.prev_button_states.get(self.BUTTON_BACK, False),
            "start_pressed": self.button_states.get(self.BUTTON_START, False) and not self.prev_button_states.get(self.BUTTON_START, False),
            "ls_pressed": self.button_states.get(self.BUTTON_LS, False) and not self.prev_button_states.get(self.BUTTON_LS, False),
            "rs_pressed": self.button_states.get(self.BUTTON_RS, False) and not self.prev_button_states.get(self.BUTTON_RS, False),

            "dpad_up": self.dpad_state[1] == 1, "dpad_down": self.dpad_state[1] == -1,
            "dpad_left": self.dpad_state[0] == -1, "dpad_right": self.dpad_state[0] == 1,
            "up_pressed": self.dpad_state[1] == 1 and self.prev_dpad_state[1] != 1,
            "down_pressed": self.dpad_state[1] == -1 and self.prev_dpad_state[1] != -1,
            "left_pressed": self.dpad_state[0] == -1 and self.prev_dpad_state[0] != -1,
            "right_pressed": self.dpad_state[0] == 1 and self.prev_dpad_state[0] != 1,
            "dpad_raw": self.dpad_state
        }
        return input_map

    def rumble(self, low_frequency_rumble, high_frequency_rumble, duration_ms):
        if self.is_connected and self.controller and hasattr(self.controller, 'rumble'):
            try:
                self.controller.rumble(float(low_frequency_rumble), float(high_frequency_rumble), int(duration_ms))
                logger.debug(f"控制器震動: Low={low_frequency_rumble}, High={high_frequency_rumble}, Duration={duration_ms}ms")
                return True
            except Exception as e: logger.warning(f"控制器震動失敗: {e}")
        return False

    def stop_rumble(self):
        if self.is_connected and self.controller and hasattr(self.controller, 'rumble'):
            try: self.controller.rumble(0, 0, 0); logger.debug("已停止控制器震動。")
            except Exception: pass

    def cleanup(self):
        if self.controller:
            self.stop_rumble(); self.controller.quit()
            self.controller = None
        self.is_connected = False
        logger.info(f"控制器 (ID: {self.joystick_id}) 資源已清理。")


if __name__ == '__main__':
    pygame.init()
    pygame.joystick.init()
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("測試 XboxController...")

    if pygame.joystick.get_count() == 0:
        logger.error("未偵測到任何遊戲控制器。請連接控制器後再試。")
        pygame.quit(); exit()

    controller = XboxController(joystick_id=0)

    if not controller.is_connected:
        logger.error("控制器連接失敗，測試終止。")
        pygame.quit(); exit()

    print(f"已連接控制器: {controller.controller.get_name()}")
    print("按任意按鈕或移動搖桿進行測試。按 Y 鍵測試震動。(Ctrl+C 結束)")
    print("注意觀察終端輸出的事件詳情以獲取按鈕/軸的索引。")

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
                
                # 打印詳細的 Pygame 搖桿事件
                if event.type == pygame.JOYAXISMOTION:
                    print(f"  Pygame Event: JOYAXISMOTION - Joystick ID: {event.instance_id}, Axis: {event.axis}, Value: {event.value:.3f}")
                elif event.type == pygame.JOYBALLMOTION: # 不常見
                    print(f"  Pygame Event: JOYBALLMOTION - Joystick ID: {event.instance_id}, Ball: {event.ball}, Rel: {event.rel}")
                elif event.type == pygame.JOYBUTTONDOWN:
                    print(f"  Pygame Event: JOYBUTTONDOWN - Joystick ID: {event.instance_id}, Button: {event.button}")
                elif event.type == pygame.JOYBUTTONUP:
                    print(f"  Pygame Event: JOYBUTTONUP - Joystick ID: {event.instance_id}, Button: {event.button}")
                elif event.type == pygame.JOYHATMOTION: # 方向鍵
                    print(f"  Pygame Event: JOYHATMOTION - Joystick ID: {event.instance_id}, Hat Index: {event.hat}, Value: {event.value}")
                elif event.type == pygame.JOYDEVICEADDED:
                    logger.info(f"偵測到新搖桿: Pygame Device Index={event.device_index}. Instance ID={event.instance_id if hasattr(event, 'instance_id') else 'N/A'}")
                    # 如果是我們正在使用的控制器斷開後重連，可能需要重新初始化
                    if not controller.is_connected and event.device_index == controller.joystick_id : # 假設 device_index 對應 joystick_id
                        logger.info("嘗試重新初始化控制器...")
                        controller = XboxController(joystick_id=controller.joystick_id) # 重新實例化
                elif event.type == pygame.JOYDEVICEREMOVED:
                    logger.warning(f"搖桿已移除: Pygame Instance ID={event.instance_id}")
                    if event.instance_id == controller.joystick_id:
                        controller.is_connected = False # 更新狀態

            if not controller.is_connected:
                # 清除上一行 (如果之前有打印 "控制器已斷開...")
                # sys.stdout.write("\033[F\033[K")
                print("控制器已斷開，請重新連接或結束測試...", end="\r")
                time.sleep(0.5)
                continue
            else:
                # 如果剛重新連接，清除 "控制器已斷開" 的訊息
                print(" " * 50, end="\r")


            inputs = controller.get_input() # 獲取處理後的輸入
            if inputs:
                # 收集有意義的輸入以顯示
                active_inputs_str = []
                if inputs["a_pressed"]: active_inputs_str.append("A pressed")
                if inputs["b_pressed"]: active_inputs_str.append("B pressed")
                if inputs["x_pressed"]: active_inputs_str.append("X pressed")
                if inputs["y_pressed"]:
                    active_inputs_str.append("Y pressed (測試震動)")
                    controller.rumble(0.6, 0.6, 300)
                
                if inputs["start_pressed"]: active_inputs_str.append("Start pressed")
                if inputs["back_pressed"]: active_inputs_str.append("Back pressed")
                if inputs["lb_pressed"]: active_inputs_str.append("LB pressed")
                if inputs["rb_pressed"]: active_inputs_str.append("RB pressed")

                # 為了避免洗版，只在數值顯著時打印搖桿和扳機值
                if abs(inputs["left_stick_x"]) > 0.15 or abs(inputs["left_stick_y"]) > 0.15:
                    active_inputs_str.append(f"LStick({inputs['left_stick_x']:.2f},{inputs['left_stick_y']:.2f})")
                if abs(inputs["right_stick_x"]) > 0.15 or abs(inputs["right_stick_y"]) > 0.15:
                    active_inputs_str.append(f"RStick({inputs['right_stick_x']:.2f},{inputs['right_stick_y']:.2f})")
                if inputs["lt_value"] > 0.05 : active_inputs_str.append(f"LT:{inputs['lt_value']:.2f}")
                if inputs["rt_value"] > 0.05 : active_inputs_str.append(f"RT:{inputs['rt_value']:.2f}")

                dpad_str = []
                if inputs["dpad_up"]: dpad_str.append("Up")
                if inputs["dpad_down"]: dpad_str.append("Down")
                if inputs["dpad_left"]: dpad_str.append("Left")
                if inputs["dpad_right"]: dpad_str.append("Right")
                if dpad_str: active_inputs_str.append(f"DPad:[{','.join(dpad_str)}]")

                if active_inputs_str:
                    # 清除上一行並打印新的狀態
                    sys.stdout.write("\033[K") # 清除當前行
                    print("當前活動輸入: " + ", ".join(active_inputs_str), end="\r")
                else:
                    # 如果沒有活動輸入，也清除上一行，避免殘留舊訊息
                    sys.stdout.write("\033[K")
                    print("無活動輸入 (等待操作)...", end="\r")
            
            time.sleep(0.02) # 控制更新頻率

    except KeyboardInterrupt:
        print("\n測試被中斷。")
    except Exception as e:
        print(f"\n測試過程中發生錯誤: {e}")
        logger.error("測試主循環錯誤", exc_info=True)
    finally:
        print("\n執行清理...")
        if controller:
            controller.cleanup()
        pygame.joystick.quit()
        pygame.quit()
        print("測試結束，資源已清理。")

