#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# traffic_light.py - 交通燈 LED 控制模組

import RPi.GPIO as GPIO
import time
import logging

logger = logging.getLogger(__name__)

class TrafficLight:
    def __init__(self, red_pin, yellow_pin, green_pin):
        """
        初始化交通燈。
        :param red_pin: 紅燈 GPIO pin (BCM)
        :param yellow_pin: 黃燈 GPIO pin (BCM)
        :param green_pin: 綠燈 GPIO pin (BCM)
        """
        self.red_pin = red_pin
        self.yellow_pin = yellow_pin
        self.green_pin = green_pin
        self.pins = [self.red_pin, self.yellow_pin, self.green_pin]

        try:
            # GPIO.setmode(GPIO.BCM) # 通常由主程式設定
            # GPIO.setwarnings(False)

            for pin in self.pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW) # 預設所有燈關閉
            
            logger.info(f"交通燈初始化成功. Red: {red_pin}, Yellow: {yellow_pin}, Green: {green_pin}")

        except RuntimeError as e:
            logger.error(f"交通燈 GPIO 設定失敗: {e}. 可能 GPIO 模式未設定或引腳已被使用。")
        except Exception as e:
            logger.error(f"交通燈初始化時發生未知錯誤: {e}", exc_info=True)

    def red_on(self):
        self.all_off()
        GPIO.output(self.red_pin, GPIO.HIGH)
        logger.debug("紅燈亮")

    def yellow_on(self):
        self.all_off()
        GPIO.output(self.yellow_pin, GPIO.HIGH)
        logger.debug("黃燈亮")

    def green_on(self):
        self.all_off()
        GPIO.output(self.green_pin, GPIO.HIGH)
        logger.debug("綠燈亮")

    def all_off(self):
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)
        logger.debug("所有交通燈熄滅")

    def cycle(self, delay=1):
        """執行一個完整的交通燈循環"""
        logger.info("開始交通燈循環...")
        self.green_on()
        time.sleep(delay * 2)
        self.yellow_on()
        time.sleep(delay)
        self.red_on()
        time.sleep(delay * 2)
        self.all_off()
        logger.info("交通燈循環結束。")

    def cleanup(self):
        """清理 GPIO 資源 (可選)"""
        self.all_off()
        logger.info("交通燈清理 (通常由主程序 GPIO.cleanup() 完成)")
        # for pin in self.pins:
        #     GPIO.cleanup(pin)

if __name__ == '__main__':
    # 此處為測試程式碼
    logging.basicConfig(level=logging.DEBUG)
    logger.info("測試 TrafficLight...")

    # 假設的 GPIO Pins (BCM 模式)
    RED_LED_PIN = 4
    YELLOW_LED_PIN = 3
    GREEN_LED_PIN = 2
    
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        traffic_light = TrafficLight(RED_LED_PIN, YELLOW_LED_PIN, GREEN_LED_PIN)
        
        print("測試交通燈 (Ctrl+C 結束測試):")
        
        print("紅燈亮 (2秒)...")
        traffic_light.red_on()
        time.sleep(2)
        
        print("黃燈亮 (2秒)...")
        traffic_light.yellow_on()
        time.sleep(2)
        
        print("綠燈亮 (2秒)...")
        traffic_light.green_on()
        time.sleep(2)
        
        traffic_light.all_off()
        print("所有燈熄滅。")
        time.sleep(1)
        
        print("執行交通燈循環 (延遲1秒)...")
        traffic_light.cycle(delay=1)
        
        print("測試完成。")

    except KeyboardInterrupt:
        print("\n測試被中斷。")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        logger.error(f"測試錯誤: {e}", exc_info=True)
    finally:
        print("執行 GPIO 清理...")
        GPIO.cleanup()
