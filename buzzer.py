#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# buzzer.py - 蜂鳴器控制模組

import RPi.GPIO as GPIO
import time
import logging

# 建議將日誌記錄器命名與主程式一致或相關
logger = logging.getLogger(__name__) # 或者使用 'game_console.buzzer' 等

class BuzzerControl:
    def __init__(self, pin, initial_volume=50): # initial_volume 作為佔空比 (0-100)
        self.pin = pin
        self.pwm = None
        self.volume = initial_volume # 預設音量 (佔空比)
        self.is_playing = False

        GPIO.setmode(GPIO.BCM) # 確保 GPIO 模式已設定
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW) # 預設不發聲

        # 預定義音效 (頻率 Hz, 持續時間 秒)
        self.sounds = {
            "select": (1000, 0.05),
            "navigate": (800, 0.05),
            "game_start": (1200, 0.1),
            "game_over": (500, 0.3),
            "back": (600, 0.05),
            "error": (300, 0.5),
        }
        logger.info(f"BuzzerControl 初始化於 GPIO {self.pin}")

    def _play(self, frequency, duration):
        if frequency <= 0 or duration <= 0:
            logger.warning(f"無效的頻率 ({frequency}) 或持續時間 ({duration})")
            return
        if self.is_playing: # 避免同時播放多個音效導致衝突
            self.stop()

        self.is_playing = True
        try:
            self.pwm = GPIO.PWM(self.pin, frequency)
            self.pwm.start(self.volume) # 使用設定的音量 (佔空比)
            time.sleep(duration)
        except RuntimeError as e:
            # PWM 可能已經被使用或未正確清理
            logger.error(f"播放音效時發生 RuntimeError: {e}. 嘗試重新設定 PWM。")
            # 可以嘗試 GPIO.cleanup(self.pin) 後重新 setup，但需謹慎
        except Exception as e:
            logger.error(f"播放音效時發生未知錯誤: {e}")
        finally:
            self.stop() # 確保音效播放完畢後停止

    def play_tone(self, sound_name=None, frequency=None, duration=None):
        """
        播放預定義音效或指定頻率和持續時間的音效。
        :param sound_name: 預定義音效的名稱 (如 "select", "game_over")
        :param frequency: 自訂頻率 (Hz)
        :param duration: 自訂持續時間 (秒)
        """
        if sound_name and sound_name in self.sounds:
            freq, dur = self.sounds[sound_name]
            logger.debug(f"播放預定義音效: {sound_name} (Freq: {freq}Hz, Dur: {dur}s)")
            self._play(freq, dur)
        elif frequency and duration:
            logger.debug(f"播放自訂音效 (Freq: {frequency}Hz, Dur: {duration}s)")
            self._play(frequency, duration)
        else:
            logger.warning("未指定有效的音效名稱或頻率/持續時間")

    def play_startup_melody(self):
        """播放開機音效"""
        logger.info("播放開機音效")
        melody = [
            (262, 0.15), (330, 0.15), (392, 0.15), (523, 0.3) # C4, E4, G4, C5
        ]
        for freq, dur in melody:
            if not self.is_playing: # 確保不會打斷自己
                self._play(freq, dur)
                time.sleep(0.05) # 音符間短暫停頓
            else:
                break

    def play_shutdown_melody(self):
        """播放關機音效 (如果需要)"""
        logger.info("播放關機音效")
        melody = [
            (523, 0.3), (392, 0.15), (330, 0.15), (262, 0.15) # C5, G4, E4, C4
        ]
        for freq, dur in melody:
            if not self.is_playing:
                self._play(freq, dur)
                time.sleep(0.05)
            else:
                break

    def set_volume(self, volume_percent):
        """
        設定音量 (透過 PWM 佔空比)。
        :param volume_percent: 0 到 100 之間的整數。
        """
        if 0 <= volume_percent <= 100:
            self.volume = volume_percent
            logger.info(f"蜂鳴器音量設定為: {self.volume}%")
            if self.pwm and self.is_playing: # 如果正在播放，立即更改音量
                self.pwm.ChangeDutyCycle(self.volume)
        else:
            logger.warning(f"無效的音量值: {volume_percent}. 請輸入 0-100 之間的值。")


    def stop(self):
        """停止當前播放的音效"""
        if self.pwm:
            self.pwm.stop()
            # self.pwm = None # 釋放 PWM 資源，但注意 RPi.GPIO 的 PWM 物件管理
        GPIO.output(self.pin, GPIO.LOW) # 確保引腳為低電平
        self.is_playing = False
        # logger.debug("蜂鳴器已停止")


    def cleanup(self):
        """清理 GPIO 資源"""
        logger.info(f"清理蜂鳴器 GPIO {self.pin}")
        self.stop()
        # GPIO.cleanup(self.pin) # 注意：如果在多處使用 GPIO，單獨清理特定引腳可能導致問題。
                               # 通常在主程式結束時執行一次 GPIO.cleanup()。
                               # 如果 BuzzerControl 是唯一使用此 pin 的，則可以清理。
                               # 考慮到主程式的 GPIO.cleanup()，這裡可以選擇不清理或僅停止PWM。

if __name__ == '__main__':
    # 簡單測試程式碼
    logging.basicConfig(level=logging.DEBUG) # 設定日誌級別以查看調試訊息
    buzzer_pin_test = 18 # BCM
    
    try:
        # GPIO.setmode(GPIO.BCM) # BuzzerControl 內部會設定
        # GPIO.setwarnings(False) # 主程式中通常會設定
        
        my_buzzer = BuzzerControl(buzzer_pin_test)
        
        print("測試蜂鳴器 (GPIO BCM 18)...")
        
        print("播放啟動音效...")
        my_buzzer.play_startup_melody()
        time.sleep(1)
        
        print("播放 'select' 音效...")
        my_buzzer.play_tone("select")
        time.sleep(0.5)

        print("播放 'game_over' 音效...")
        my_buzzer.play_tone("game_over")
        time.sleep(1)

        print("播放自訂音效 (1500Hz, 0.2s)...")
        my_buzzer.play_tone(frequency=1500, duration=0.2)
        time.sleep(0.5)

        print("設定音量為 20% 並播放...")
        my_buzzer.set_volume(20)
        my_buzzer.play_tone(frequency=880, duration=0.5) # A5
        time.sleep(1)

        print("設定音量為 80% 並播放...")
        my_buzzer.set_volume(80)
        my_buzzer.play_tone(frequency=440, duration=0.5) # A4
        time.sleep(1)

        print("測試完成。")

    except KeyboardInterrupt:
        print("測試被中斷")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        logger.error(f"測試錯誤: {e}", exc_info=True)
    finally:
        print("執行 GPIO 清理...")
        GPIO.cleanup() # 清理所有使用的 GPIO 通道
