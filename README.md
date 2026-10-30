# ts3-quecpython

QuecPython device layer for the TS3-RTOS client on handheld PoC radios.
The portable client core lives in a separate repo: https://github.com/cipheraenys/ts3-core

## Status

Hardware bring-up notes only. Device drivers (LCD, audio, PTT) land here during Path A bring-up.

See `targets/bq280-quecpython/README.md` for the verified BQ280 hardware map
(ST7735 LCD, speaker/TTS, mic, ADC keypad/PTT, REPL access).
