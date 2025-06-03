#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# matrix_keypad.py - 4x4 矩陣鍵盤控制模組

import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)

class MatrixKeypad:
    # 按鍵對應 (可根據實際鍵盤修改)
    KEYPAD_LAYOUT = [
        ['A', '3', '2', '1'],
        ['B', '6', '5', '4'],
        ['C', '9', '8', '7'],
        ['D', '#', '0', '*']
    ]

    # GPIO 設定 (BCM 模式)
    # 請根據您的實際接線修改這些 GPIO Pin
    ROW_PINS = [6, 13, 19, 26]  # Rows: R1, R2, R3, R4
    COL_PINS = [12, 16, 20, 21] # Columns: C1, C2, C3, C4

    def __init__(self, row_pins=None, col_pins=None, layout=None, debounce_delay=0.05):
        """
        初始化矩陣鍵盤。
        :param row_pins: 行 GPIO pins 列表 (BCM)
        :param col_pins: 列 GPIO pins 列表 (BCM)
        :param layout: 按鍵佈局列表
        :param debounce_delay: 按鍵去抖動延遲 (秒)
        """
        self.row_pins = row_pins if row_pins else self.ROW_PINS
        self.col_pins = col_pins if col_pins else self.COL_PINS
        self.layout = layout if layout else self.KEYPAD_LAYOUT
        self.debounce_delay = debounce_delay
        self.last_key_press_time = 0
        self.last_key = None

        if len(self.row_pins) != len(self.layout) or len(self.col_pins) != len(self.layout[0]):
            msg = "行/列 GPIO pins 數量與按鍵佈局不匹配。"
            logger.error(msg)
            raise ValueError(msg)

        try:
            # GPIO.setmode(GPIO.BCM) # 通常由主程式設定
            # GPIO.setwarnings(False)

            # 設定行 GPIO 為輸出，預設高電平
            for pin in self.row_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)

            # 設定列 GPIO 為輸入，啟用上拉電阻
            for pin in self.col_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            logger.info(f"矩陣鍵盤初始化成功. Rows: {self.row_pins}, Cols: {self.col_pins}")

        except RuntimeError as e:
            logger.error(f"矩陣鍵盤 GPIO 設定失敗: {e}. 可能 GPIO 模式未設定或引腳已被使用。")
            # 可以考慮在這裡拋出異常或設定一個失敗狀態
        except Exception as e:
            logger.error(f"矩陣鍵盤初始化時發生未知錯誤: {e}", exc_info=True)


    def get_key(self):
        """
        掃描鍵盤並返回按下的按鍵值。
        如果沒有按鍵按下，返回 None。
        """
        current_time = time.time()
        
        # 基本的去抖動：如果距離上次有效按鍵時間太短，則忽略
        if self.last_key and (current_time - self.last_key_press_time < self.debounce_delay * 2): # 給予更長的冷卻時間
             # 如果是同一個按鍵持續按下，則不返回 (避免重複觸發)
             # 若要實現長按，需要更複雜的邏輯
            return None 

        pressed_key = None
        for r_idx, row_pin in enumerate(self.row_pins):
            # 將當前行拉低
            GPIO.output(row_pin, GPIO.LOW)
            
            for c_idx, col_pin in enumerate(self.col_pins):
                # 如果列為低電平，表示有按鍵按下
                if GPIO.input(col_pin) == GPIO.LOW:
                    # 等待一小段時間去抖動
                    time.sleep(self.debounce_delay)
                    # 再次確認按鍵是否仍然按下
                    if GPIO.input(col_pin) == GPIO.LOW:
                        pressed_key = self.layout[r_idx][c_idx]
                        self.last_key_press_time = current_time
                        self.last_key = pressed_key
                        logger.debug(f"偵測到按鍵: {pressed_key}")
                        break # 找到按鍵，跳出內層循環
            
            # 將當前行恢復為高電平
            GPIO.output(row_pin, GPIO.HIGH)
            
            if pressed_key:
                break # 找到按鍵，跳出外層循環
        
        if not pressed_key: # 如果這次掃描沒有按鍵，清除上次按鍵記錄
            self.last_key = None

        return pressed_key

    def cleanup(self):
        """清理 GPIO 資源 (可選)"""
        # 通常由主程式統一清理 GPIO
        logger.info("矩陣鍵盤清理 (通常由主程序 GPIO.cleanup() 完成)")
        # for pin in self.row_pins:
        #     GPIO.cleanup(pin)
        # for pin in self.col_pins:
        #     GPIO.cleanup(pin)


if __name__ == '__main__':
    # 此處為測試程式碼
    logging.basicConfig(level=logging.DEBUG)
    logger.info("測試 MatrixKeypad...")

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # 使用預設的 GPIO Pins 和佈局
        keypad = MatrixKeypad()
        print("請按下矩陣鍵盤上的按鍵 (Ctrl+C 結束測試):")
        
        active_key = None
        while True:
            key = keypad.get_key()
            if key:
                if key != active_key : # 只有在新按鍵按下時才打印
                    print(f"按鍵按下: {key}")
                    active_key = key
            else:
                active_key = None # 按鍵已釋放

            time.sleep(0.05) # 短暫延遲，避免 CPU 過度使用

    except KeyboardInterrupt:
        print("\n測試被中斷。")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        logger.error(f"測試錯誤: {e}", exc_info=True)
    finally:
        print("執行 GPIO 清理...")
        GPIO.cleanup()
