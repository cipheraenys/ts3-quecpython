# BQ280 sound: speaker/PA, on-chip TTS, mic record.
# Named `sound`, not `audio`: `audio` is a QuecPython built-in that would shadow this file.
# Constants are the verified BQ280 config; retune per board.
import audio

SPK_PA_GPIO = 25
SPK_VOLUME = 11          # max safe on BQ280 (<= 11)
TTS_VOLUME = 9           # <= 9

_spk = None
_tts = None


def speaker():
    """Lazily open the speaker with the PA enabled. Returns the Audio object."""
    global _spk
    if _spk is None:
        _spk = audio.Audio(0)
        _spk.set_pa(SPK_PA_GPIO)
        _spk.setSpeakerpaSwitch(1)
        _spk.setVolume(SPK_VOLUME)
    return _spk


def play_wav(path):
    """Play a WAV file through the speaker. Returns the driver status (0 = ok)."""
    return speaker().play(2, 0, path)


def say(text, volume=TTS_VOLUME):
    """Speak UTF-8 text via on-chip TTS. Returns 0 on success."""
    global _tts
    if _tts is None:
        _tts = audio.TTS(0)
    _tts.setVolume(volume)
    return _tts.play(2, 1, 2, text)


def record(path, seconds):
    """Record `seconds` of mic audio to a WAV file. Returns 0 on success."""
    return audio.Record(0).start(path, seconds)


def demo():
    return say("halo")


if __name__ == "__main__":
    demo()
