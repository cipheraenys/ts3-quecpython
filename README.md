# ts3-quecpython

QuecPython device layer for the TS3-RTOS client on handheld PoC radios. The
portable client core is a separate repo: https://github.com/cipheraenys/ts3-core

One folder per device under `devices/`. Every device implements the same small
surface, so the app code above stays device-agnostic — the same idea as
`core/port.h` on the C side.

## Device contract

Each `devices/<name>/` provides three modules with this surface:

**display.py**
- `init()` — power the panel, return the driver
- `clear(color)` — fill the screen (RGB565)
- `lvgl_attach()` — register as an LVGL display, return the active screen

**audio.py**
- `say(text, volume=...)` — on-chip TTS, returns 0 on success
- `play_wav(path)` — play a WAV through the speaker
- `record(path, seconds)` — record the mic to a WAV

**keypad.py**
- `read()` — raw key / PTT reading
- `ptt_pressed()` — True while PTT is held

The constants at the top of each module (pins, thresholds, controller) are the
only part that changes between boards.

## Devices

- `devices/bq280/` — BQ280 handheld (EC600M / ASR1606). Hardware map in its README.

## Add a device

Copy `devices/bq280/` to `devices/<name>/`, keep the module surface, retune the
constants for your board, and run each module's `demo()` on the device to confirm.
