# BQ280 keypad / PTT on ADC channel 1 (resistor ladder).
# Idle and pressed readings are the verified BQ280 values; retune per board.
from misc import ADC

PTT_CHANNEL = 1
IDLE = 1201              # ~reading when nothing is pressed
PTT_PRESSED = 493        # ~reading while PTT is held
THRESHOLD = (IDLE + PTT_PRESSED) // 2   # midpoint

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
