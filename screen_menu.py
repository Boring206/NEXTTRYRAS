#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# screen_menu.py - SPI 螢幕選單顯示管理 (已修正 getsize 錯誤)

from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9341 # 假設使用 ILI9341 控制器的 SPI 螢幕
from PIL import Image, ImageDraw, ImageFont
import time
import logging
import os

logger = logging.getLogger(__name__)

# 中文字型路徑
try:
    CHINESE_FONT_PATH_SPI = os.environ.get("CHINESE_FONT_PATH", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
    if not os.path.exists(CHINESE_FONT_PATH_SPI):
        CHINESE_FONT_PATH_SPI = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
        if not os.path.exists(CHINESE_FONT_PATH_SPI):
             CHINESE_FONT_PATH_SPI = "arial.ttf" # Pillow 會嘗試尋找系統中的 arial
    logger.info(f"SPI Screen Menu 使用字型路徑: {CHINESE_FONT_PATH_SPI}")
except Exception as e:
    logger.error(f"讀取 SPI 中文字型路徑時發生錯誤: {e}")
    CHINESE_FONT_PATH_SPI = "arial.ttf"


class SPIScreenManager:
    WHITE = (255, 255, 255); BLACK = (0, 0, 0); RED = (255, 0, 0)
    GREEN = (0, 255, 0); BLUE = (0, 0, 255); YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255); MAGENTA = (255, 0, 255)

    def __init__(self, port=0, device_cs=0, gpio_dc=25, gpio_rst=24, gpio_led=27, rotate=0):
        self.device = None; self.width = 0; self.height = 0
        self.font_small = None; self.font_medium = None; self.font_large = None
        try:
            serial_interface = spi(port=port, device=device_cs, gpio_DC=gpio_dc, gpio_RST=gpio_rst)
            self.device = ili9341(serial_interface, active_low=False, gpio_LIGHT=gpio_led, rotate=rotate)
            if rotate % 2 == 1: self.width, self.height = self.device.height, self.device.width
            else: self.width, self.height = self.device.width, self.device.height
            logger.info(f"SPI 螢幕 (ILI9341) 初始化成功. 解析度: {self.width}x{self.height}, 旋轉: {rotate*90}度")
            self._load_fonts(); self.clear_screen()
        except FileNotFoundError: logger.error("SPI 設備未找到。請確認 SPI 介面已啟用。"); self.device = None
        except ImportError: logger.error("luma.lcd 或 luma.core 套件未安裝。"); self.device = None
        except Exception as e: logger.error(f"SPI 螢幕初始化失敗: {e}", exc_info=True); self.device = None

    def _load_fonts(self):
        try:
            # 根據螢幕大小調整字型大小
            if self.height <= 128: size_s, size_m, size_l = 10, 12, 16
            elif self.height <= 240: size_s, size_m, size_l = 14, 18, 24
            else: size_s, size_m, size_l = 16, 22, 30
            self.font_small = ImageFont.truetype(CHINESE_FONT_PATH_SPI, size_s)
            self.font_medium = ImageFont.truetype(CHINESE_FONT_PATH_SPI, size_m)
            self.font_large = ImageFont.truetype(CHINESE_FONT_PATH_SPI, size_l)
            logger.info("SPI 螢幕字型載入成功。")
        except IOError:
            logger.warning(f"字型檔案 '{CHINESE_FONT_PATH_SPI}' 未找到或無法讀取。將使用預設字型。")
            self.font_small, self.font_medium, self.font_large = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()
        except Exception as e:
            logger.error(f"載入 SPI 螢幕字型時發生錯誤: {e}")
            self.font_small, self.font_medium, self.font_large = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default()

    def get_text_width(self, text, font):
        """輔助函數：獲取文字寬度 (使用 getmask)"""
        if not text or not font: return 0
        return font.getmask(text).size[0]

    def get_text_height(self, text, font):
        """輔助函數：獲取文字高度 (使用 getmask)"""
        if not text or not font: return 0
        # getmask().size[1] 通常是字元本身的像素高度，
        # 對於行高，有時需要考慮字體的 ascent 和 descent
        # font.getmetrics() 返回 (ascent, descent)，行高約為 ascent + descent
        # 但 getmask().size[1] 在許多情況下也夠用
        metrics = font.getmetrics()
        return metrics[0] + metrics[1] # 使用 ascent + descent 作為行高

    def is_available(self): return self.device is not None
    def clear_screen(self, color=BLACK):
        if not self.is_available(): return
        with canvas(self.device) as draw: draw.rectangle(self.device.bounding_box, outline=color, fill=color)

    def display_text(self, text, x, y, font=None, fill_color=WHITE, background_color=BLACK, clear=False):
        if not self.is_available(): return
        font_to_use = font or self.font_medium
        with canvas(self.device) as draw:
            if clear: draw.rectangle(self.device.bounding_box, outline=background_color, fill=background_color)
            draw.text((x, y), text, font=font_to_use, fill=fill_color)

    def display_multiline_text(self, lines, start_x, start_y, font=None, fill_color=WHITE, line_spacing_ratio=1.2, background_color=BLACK, clear=False, center_horizontal=False):
        if not self.is_available(): return
        font_to_use = font or self.font_medium
        current_y = start_y
        
        base_line_height = self.get_text_height("T", font_to_use) # 用一個標準字符獲取基準行高

        with canvas(self.device) as draw:
            if clear: draw.rectangle(self.device.bounding_box, outline=background_color, fill=background_color)
            for line in lines:
                # 使用 draw.textbbox 獲取實際繪製的邊界框來計算寬度
                # (x1, y1, x2, y2) = draw.textbbox((start_x, current_y), line, font=font_to_use)
                # text_width = x2 - x1
                # text_height_from_bbox = y2 - y1 # 這是繪製後的實際高度
                
                # 或者使用 getmask 獲取文字本身的寬度
                text_width = self.get_text_width(line, font_to_use)

                actual_x = start_x
                if center_horizontal: actual_x = (self.width - text_width) // 2
                
                draw.text((actual_x, current_y), line, font=font_to_use, fill=fill_color)
                current_y += int(base_line_height * line_spacing_ratio)


    def display_custom_message(self, title, message, duration=2, title_color=YELLOW, msg_color=WHITE, bg_color=BLACK):
        if not self.is_available(): return
        
        lines = []
        if title: lines.append({"text": title, "font": self.font_medium, "color": title_color})

        char_width_estimate = self.get_text_width("國", self.font_small)
        if char_width_estimate == 0: char_width_estimate = 8 # 備用值
        max_chars_per_line = self.width // char_width_estimate - 1
        if max_chars_per_line <=0: max_chars_per_line = 10 # 確保至少能放幾個字

        current_line_text = ""
        if isinstance(message, str):
            for char_idx, char_val in enumerate(message):
                if len(current_line_text) < max_chars_per_line and char_val != '\n':
                    current_line_text += char_val
                else:
                    if current_line_text: lines.append({"text": current_line_text, "font": self.font_small, "color": msg_color})
                    current_line_text = char_val if char_val != '\n' else ""
            if current_line_text: lines.append({"text": current_line_text, "font": self.font_small, "color": msg_color})
        elif isinstance(message, list):
            for item in message: lines.append({"text": str(item), "font": self.font_small, "color": msg_color})

        y_padding = 5
        total_text_height = 0
        line_height_spacing_ratio = 1.3 # 行高乘以這個比例作為間距

        for line_info in lines:
            total_text_height += int(self.get_text_height("T", line_info["font"]) * line_height_spacing_ratio)
        
        start_y = (self.height - total_text_height) // 2
        if start_y < y_padding: start_y = y_padding

        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline=bg_color, fill=bg_color)
            current_y = start_y
            
            for line_info in lines:
                font_to_use = line_info["font"]
                text_to_draw = line_info["text"]
                text_color = line_info["color"]
                
                # text_bbox = draw.textbbox((0, current_y), text_to_draw, font=font_to_use)
                # text_w = text_bbox[2] - text_bbox[0]
                text_w = self.get_text_width(text_to_draw, font_to_use)
                
                draw.text(((self.width - text_w) // 2, current_y), text_to_draw, font=font_to_use, fill=text_color)
                current_y += int(self.get_text_height("T", font_to_use) * line_height_spacing_ratio)
        
        if duration > 0: time.sleep(duration)

    def display_menu(self, menu_items, current_selection, title="選擇遊戲"):
        if not self.is_available(): return
        
        title_height = self.get_text_height("T", self.font_medium) if title else 0
        item_height = self.get_text_height("T", self.font_small)
        line_spacing = 1.3 # 行高倍數

        # 確保分母不為零
        denominator_item_page = item_height * line_spacing
        if denominator_item_page == 0:
            logger.warning("Calculated item_height * line_spacing is zero. Defaulting items_per_page to 1.")
            items_per_page = 1
        else:
            items_per_page = int((self.height - (title_height * line_spacing if title else 0) - 10) // denominator_item_page)
        
        if items_per_page <= 0: items_per_page = 1
        
        start_index = (current_selection // items_per_page) * items_per_page
        end_index = min(start_index + items_per_page, len(menu_items))
        
        display_elements = [] # 每個元素是 {"text": ..., "font": ..., "color": ..., "highlight": ..., "y_pos": ...}
        current_y_draw = 5

        if title:
            display_elements.append({
                "text": title, "font": self.font_medium, "color": self.YELLOW, 
                "highlight": False, "y_pos": current_y_draw
            })
            current_y_draw += int(title_height * line_spacing)


        for i in range(start_index, end_index): # Error was here if start/end_index were float
            item = menu_items[i]
            text = f"{item.get('id', i+1)}. {item.get('name', '未知項目')}"
            
            char_w_est = self.get_text_width("國", self.font_small)
            if char_w_est == 0: char_w_est = 6
            max_item_len = self.width // char_w_est - 2
            if max_item_len <=0: max_item_len = 5
            if len(text) > max_item_len: text = text[:max_item_len-3] + "..."

            display_elements.append({
                "text": text, "font": self.font_small, "color": self.WHITE,
                "highlight": (i == current_selection), "y_pos": current_y_draw
            })
            current_y_draw += int(item_height * line_spacing)

        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline=self.BLACK, fill=self.BLACK)
            for element in display_elements:
                # text_bbox_draw = draw.textbbox((0, element["y_pos"]), element["text"], font=element["font"])
                # text_w_draw = text_bbox_draw[2] - text_bbox_draw[0]
                # text_h_draw = text_bbox_draw[3] - text_bbox_draw[1]
                text_w_draw = self.get_text_width(element["text"], element["font"])
                text_h_draw = self.get_text_height("T", element["font"]) # 用基準高度

                x_pos = (self.width - text_w_draw) // 2
                if element["highlight"]:
                    # 高亮背景範圍稍微擴大一點
                    draw.rectangle((0, element["y_pos"] - 2, self.width, element["y_pos"] + text_h_draw + 2), fill=self.BLUE)
                    draw.text((x_pos, element["y_pos"]), element["text"], font=element["font"], fill=self.YELLOW)
                else:
                    draw.text((x_pos, element["y_pos"]), element["text"], font=element["font"], fill=element["color"])
    
    def display_game_instructions(self, game_data):
        if not self.is_available(): return
        title = game_data.get("name", "遊戲說明")
        raw_desc = game_data.get("description", "無說明")
        
        lines_to_display = []
        if title: lines_to_display.append({"text": title, "font": self.font_medium, "color": self.YELLOW})

        char_w_est_instr = self.get_text_width("測", self.font_small)
        if char_w_est_instr == 0: char_w_est_instr = 7
        max_chars = self.width // char_w_est_instr -1
        if max_chars <=0 : max_chars = 8

        current_line_desc = ""
        # 簡單分行，可以考慮更智能的斷詞
        for word_group in raw_desc.replace('。', '。\n').replace('！', '！\n').replace('？', '？\n').split('\n'):
            words = list(word_group) # 按字分割
            for word_char in words:
                if self.get_text_width(current_line_desc + word_char, self.font_small) <= self.width - 10 : # 留點邊距
                    current_line_desc += word_char
                else:
                    if current_line_desc: lines_to_display.append({"text":current_line_desc, "font":self.font_small, "color":self.WHITE})
                    current_line_desc = word_char
            if current_line_desc: #處理剩餘部分
                 lines_to_display.append({"text":current_line_desc, "font":self.font_small, "color":self.WHITE})
                 current_line_desc = ""


        lines_to_display.append({"text": " ", "font": self.font_small, "color": self.WHITE}) # 空行
        lines_to_display.append({"text": "A:開始 B:返回", "font": self.font_small, "color": self.CYAN})

        current_y_pos = 5
        line_h_ratio = 1.3
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, fill=self.BLACK)
            for line_info in lines_to_display:
                font = line_info["font"]
                text = line_info["text"]
                color = line_info["color"]
                # text_box = draw.textbbox((5, current_y_pos), text, font=font)
                # text_w = text_box[2] - text_box[0]
                text_w = self.get_text_width(text, font)
                
                x_text_pos = 5 # 預設靠左
                # 如果是標題或提示，可以考慮居中
                if text == title or "A:開始" in text:
                     x_text_pos = (self.width - text_w) // 2

                draw.text((x_text_pos, current_y_pos), text, font=font, fill=color)
                current_y_pos += int(self.get_text_height("T", font) * line_h_ratio)


    def display_game_over(self, score, best_score=None):
        if not self.is_available(): return
        elements = [{"text": "遊戲結束！", "font": self.font_large, "color": self.RED}]
        elements.append({"text": f"分數: {score}", "font": self.font_medium, "color": self.WHITE})
        if best_score is not None:
            elements.append({"text": f"最高分: {best_score}", "font": self.font_medium, "color": self.YELLOW})
        elements.append({"text": " ", "font": self.font_small, "color": self.WHITE})
        elements.append({"text": "3秒後返回選單", "font": self.font_small, "color": self.CYAN})
        
        current_y_pos = self.height // 4
        line_h_ratio_over = 1.4
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, fill=self.BLACK)
            for el in elements:
                # text_b = draw.textbbox((0, current_y_pos), el["text"], font=el["font"])
                # text_w = text_b[2] - text_b[0]
                text_w = self.get_text_width(el["text"], el["font"])
                draw.text(((self.width - text_w)//2, current_y_pos), el["text"], font=el["font"], fill=el["color"])
                current_y_pos += int(self.get_text_height("T", el["font"]) * line_h_ratio_over)
        # time.sleep(3) # 阻塞，應由主循環控制

    def cleanup(self):
        if self.device:
            try: self.device.cleanup(); logger.info("SPI 螢幕資源已清理")
            except Exception as e: logger.error(f"清理 SPI 螢幕時發生錯誤: {e}")
        self.device = None

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("測試 SPIScreenManager (已修正 getsize)...")
    screen = SPIScreenManager(port=0, device_cs=0, gpio_dc=25, gpio_rst=24, gpio_led=27, rotate=0)
    if screen.is_available():
        logger.info(f"螢幕寬度: {screen.width}, 高度: {screen.height}")
        screen.display_custom_message("系統啟動", "遊戲機載入中...", duration=1, title_color=screen.GREEN)
        sample_games = [{"id": 1, "name": "貪吃蛇範例"}, {"id": 2, "name": "打磚塊"}, {"id": 3, "name": "宇宙戰艦"}]
        screen.display_menu(sample_games, current_selection=1, title="請選擇")
        time.sleep(2)
        screen.display_game_instructions({"name": "貪吃蛇", "description": "用方向鍵控制蛇。吃到食物變長。勿撞牆或自己。"})
        time.sleep(3)
        screen.display_game_over(score=123, best_score=1000)
        # display_game_over 不再包含 sleep
        time.sleep(1) # 在測試腳本中控制延遲
        screen.display_text("測試完成!", x=10, y=screen.height//2, font=screen.font_large, clear=True)
        time.sleep(1)
        screen.clear_screen(); logger.info("SPI 螢幕測試完成。"); screen.cleanup()
    else: logger.error("SPI 螢幕初始化失敗，無法執行測試。")

