# BQ280 device drivers (QuecPython)

Thin Python modules over the verified BQ280 (EC600M / ASR1606) hardware. The
constants are transcribed from working REPL sessions — see
`../targets/bq280-quecpython/README.md` for the full hardware map. Run each
module's `demo()` on the device once to confirm before relying on them.

- `display.py` — ST7735 128x160 + LVGL attach. Wraps the vendor `lcd_bf` module.
- `audio.py` — speaker/PA, on-chip TTS, mic record.
- `keypad.py` — PTT on ADC channel 1.

## `lcd_bf` dependency

`display.py` imports `lcd_bf`, the ST7735 driver from the QuecPython solution-POC
(`baofeng` branch). It is vendor code and is not copied here — put `lcd_bf.py` on
the device (e.g. `/usr/lcd_bf.py`) yourself.

## Deploy

Upload the `.py` files to the device (e.g. into `/usr`), then:

```python
import sys; sys.path.append('/usr')   # /usr is not on the import path by default
import display, audio, keypad
display.init(); display.clear(display.RED)
audio.say('halo')
print(keypad.ptt_pressed())
```
