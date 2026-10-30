# BQ280 (EC600M / ASR1606) display: ST7735 128x160 over the module's fixed SPI pins.
# Wraps the vendor `lcd_bf` driver (QuecPython solution-POC, baofeng branch), which
# must already be on the device (e.g. /usr/lcd_bf.py) — its source is not copied here.
# Constants are the verified BQ280 config; retune per board.
from machine import Pin
import lcd_bf

BACKLIGHT_PIN = Pin.GPIO14          # active-high
WIDTH, HEIGHT = 128, 160
SPI_CLK = 13000

# RGB565
BLACK, WHITE, RED, GREEN, BLUE = 0x0000, 0xFFFF, 0xF800, 0x07E0, 0x001F

_lcd = None


def init():
    """Power the backlight and bring up the ST7735. Returns the driver object."""
    global _lcd
    Pin(BACKLIGHT_PIN, Pin.OUT, Pin.PULL_DISABLE, 1)
    _lcd = lcd_bf.ST7735(width=WIDTH, height=HEIGHT, clk=SPI_CLK, dir=0)
    return _lcd


def clear(color=BLACK):
    _lcd.clear(color)


def lvgl_attach():
    """Register the ST7735 as an LVGL display. Call after init(); returns the active screen."""
    import lvgl as lv
    lv.init()
    db = lv.disp_draw_buf_t()
    buf = bytearray(WIDTH * HEIGHT * 2)
    db.init(buf, None, len(buf))
    dd = lv.disp_drv_t()
    dd.init()
    dd.draw_buf = db
    dd.flush_cb = _lcd._lcd.lcd_write
    dd.hor_res = WIDTH
    dd.ver_res = HEIGHT
    dd.sw_rotate = 1
    dd.rotated = lv.DISP_ROT._180
    dd.register()
    lv.tick_inc(5)
    return lv.scr_act()


def demo():
    init()
    clear(RED)


if __name__ == "__main__":
    demo()
