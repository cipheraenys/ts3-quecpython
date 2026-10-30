# BQ280 PoC handheld — QuecPython hardware bringup

This is a device target, not a `core/port.h` implementation: the unit runs QuecPython (MicroPython), so the C++ core does not run on it. For the C++ route on the same module family see [ports/quecopen-ec600m](../../ports/quecopen-ec600m/README.md).

Field notes for the white-label PoC walkie-talkie this project was tested on. Everything below
was verified on the physical unit unless a line says otherwise.

## Device

| | |
|---|---|
| Unit | BQ280 (BinQi), also sold rebranded (e.g. as "Motorola T280") |
| Module | Quectel **EC600MCN_LA** — LTE Cat 1 bis |
| SoC | ASR **ASR1606** ("CraneL"), Cortex-R4, bootrom `2021.10.16` |
| Stock firmware | vendor PoC app on the XIN-PTT / **BND** (Shanlitech) platform, built on the QuecOpen C-SDK |
| Power control | rotary **volume/power knob** (turn clockwise = on), not a push button. On the 1606, PWRKEY must be held low ≈620 ms to boot. |
| Display | SPI LCD, controller **ST7735**, **128×160** |

## Download mode & flashing

- The ASR bootrom enters a download window on a **cold boot** (battery fully removed, or knob
  OFF→ON) when **USB‑VBUS is connected** — it waits ≈1 s, enumerating as **"Quectel Download
  Port"** (`VID 2ECC PID 3004`). With a running app you can also force it with `AT+QDOWNLOAD=1`
  on the AT port. There is **no dedicated USB_BOOT pin** on CraneL; the mechanism is PMIC
  restart-cmd + VBUS detect (from the bootrom `boot2` source).
- Flash with `adownload` from the ASR Flashing Tool (aboot). It takes an **aboot `.zip`
  package** (a `download.json` manifest plus partition images / `preboot.img` / `flasher.img`).
  QuecPython `.bin` firmware is itself such a zip — flash it directly.
- **Recovery is always possible**: download mode is in the bootrom and survives any app flash.
  `factory_a`/`factory_b` (per-unit RF calibration) are marked `productionOnly`, so a normal
  (non-production) flash **preserves the RF cal**.
- The aboot "upload" (dump) format is **not** a re-flashable image — a partition dumped this way
  will not boot if written back. Keep the vendor firmware package if you need a true restore.

## QuecPython firmware

- Use the **base** build, not the POC demo. The POC demo (`EC600MCNLER…_POC_XBND_OCPU_QPY…`)
  has an auto-running `broad_poc_app` **baked into the firmware** (not the user filesystem —
  erasing `customer_fs` does not remove it); it holds the REPL and mis-drives the LCD.
- Flashed here: `QPY_OCPU_V0001_EC600M_EULA_FW` → reports `EC600MEULAR06A01M08_OCPU_QPY`.
  This is the **EU-LA** variant; it boots and runs on the CN-LA hardware, but its modem/band
  firmware is for EU/LatAm — cellular data on an Indonesian SIM is **unverified**. The exact
  CN-LA base build (`EC600MCNLAR01A01M08_XBND_OCPU_QPY_BETA0831`) would match better; it is on
  Quectel's portal (developer.quectel.com, Resource Download), not a public direct link.
- Versions: QuecPython **3.4.0**, MicroPython **1.13.0**.

## REPL access (the part that is easy to get stuck on)

- The REPL is a normal MicroPython serial REPL at **115200**, but on its **own USB interface**
  — Windows names it **"Quectel USB REPL Port"**. It is **not** the AT port and **not** DIAG.
- That interface only enumerates once the **`Quectel_Windows_USB_DriverA_Customer`** driver is
  installed. Without it you see only AT + DIAG (and two interfaces sit at error code 28), and
  the REPL is unreachable — QPYcom will show a `>>>` that never responds.
- Once the driver is in, any serial terminal (or script) can drive the REPL directly; QPYcom is
  not required. Ctrl-C interrupts, Ctrl-E/Ctrl-D is paste mode for multi-line blocks.

## LCD

- **Controller ST7735, 128×160, SPI clock 13000.** Backlight is **GPIO14**, active-high.
- CS/RST/DC ride the module's fixed LCD pins — the `SPICS`/`SPIRST`/`SPIDC` arguments in the
  reference driver are stored but unused, so they do not need to be correct.
- Working driver: the `ST7735` class from QuecPython **`solution-POC`, branch `baofeng`,
  `code/dev/lcd.py`**. The `EC600MCNLE-Demo` branch's driver (ST7789 240×240) does **not** drive
  this panel — wrong controller, so no command reaches it and the screen stays lit-but-white.
- Minimal bringup over the REPL:

  ```python
  import sys
  sys.path.append('/usr')            # /usr is not on sys.path by default
  import lcd_bf                       # the baofeng code/dev/lcd.py, uploaded to /usr/
  from machine import Pin
  Pin(Pin.GPIO14, Pin.OUT, Pin.PULL_DISABLE, 1)   # backlight on
  g = lcd_bf.ST7735()                 # ST7735 128x160 init
  g.clear(0xF800)                     # fill red (RGB565); 0x07E0 green, 0x001F blue
  ```

- The driver class exposes only `clear` / `display_on` / `display_off`. Text and UI use the
  firmware's built-in **`lvgl`** module (as the demo's `code/ui/` does).

## Verified vs not

- **Verified on hardware:** download-mode recovery and flashing; clean QuecPython boot and a
  working REPL; LCD backlight (GPIO14) and fill (ST7735); the three driver modules import and
  run (`keypad.read()` = 1201 idle on ADC ch1; `display.clear` fills; `sound.say` returns 0).
- **Not verified:** cellular data on the EU-LA firmware (no SIM in the unit); mic record, the
  PTT-pressed ADC swing, and actual speaker loudness (all need a person at the device);
  running this project's TS3 client under QuecPython.

## Drivers

`display.py`, `sound.py`, `keypad.py` implement the device contract (see the repo
README). Constants are transcribed from verified REPL sessions; run each module's
`demo()` on the device once to confirm.

The speaker/TTS module is `sound.py`, not `audio.py`: `audio` is a QuecPython
built-in and a file of that name on the path would never load (the built-in wins).

`display.py` imports the vendor `lcd_bf` ST7735 driver (QuecPython solution-POC,
`baofeng` branch). It is not copied here — put `lcd_bf.py` on the device (e.g.
`/usr/lcd_bf.py`) yourself.

Deploy: upload the `.py` files to `/usr`, then:

```python
import sys; sys.path.append('/usr')   # /usr is not on the import path by default
import display, sound, keypad
display.init(); display.clear(display.RED)
sound.say('halo'); print(keypad.ptt_pressed())
```
