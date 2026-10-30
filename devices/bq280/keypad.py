# BQ280 keypad / PTT on ADC channel 1 (resistor ladder).
# IDLE verified on the BQ280 (1201); PTT_PRESSED unverified. Retune per board.
from misc import ADC

PTT_CHANNEL = 1
IDLE = 1201              # nothing pressed
PTT_PRESSED = 493        # PTT held
THRESHOLD = (IDLE + PTT_PRESSED) // 2

_adc = None


def read():
    """Raw ADC value on the keypad channel."""
    global _adc
    if _adc is None:
        _adc = ADC()
    return _adc.read(PTT_CHANNEL)


def ptt_pressed():
    """True while PTT is held (the reading swings below the midpoint)."""
    return read() < THRESHOLD


def demo():
    print("raw", read(), "ptt", ptt_pressed())


if __name__ == "__main__":
    demo()
