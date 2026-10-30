"""Replace the EC600N Pin.GPIOn and PWMn tables in libHeliosAPI.a with the EC600M ones.

EC600M values are from the stock EC600M QuecPython customer_app.bin (pin_map at file offsets
0x129104 and 0x12926C, pwm_map at 0x12CEEC). The tables keep 41 GPIO entries, so the
EC600M-only Pin.GPIO42..45 are not available.

usage: patch_maps_ec600m.py <libHeliosAPI.a>
env:   CROSS (toolchain prefix)
"""
import os
import struct
import subprocess
import sys
import tempfile

lib = os.path.abspath(sys.argv[1])
CROSS = os.environ.get("CROSS", os.path.expanduser(
    "~/helios_tc/gcc-arm-none-eabi-10-2020-q4-major/bin/arm-none-eabi-"))

EC600N_PINS = [21, 25, 26, 22, 24, 23, 28, 121, 122, 2, 17, 19, 18, 16, 20, 14, 32, 31, 33, 36,
               3, 4, 5, 6, 7, 8, 9, 11, 10, 35, 15, 13, 12, 27, 34, 51, 52, 54, 53, 30, 29]
EC600M_PINS = [21, 25, 26, 22, 24, 23, 20, 27, 31, 2, 17, 19, 18, 16, 28, 14, 32, 117, 33, 36,
               5, 71, 72, 6, 7, 4, 9, 11, 10, 35, 15, 13, 12, 50, 34, 51, 52, 54, 53, 30, 29]
EC600N_PWM = [6, 7, 31, 32]
EC600M_PWM = [10, 11, 117, 32]


def table(ids, socs):
    return b"".join(struct.pack("<ii", i, s) for i, s in zip(ids, socs))


PATCHES = [  # (object, section, expected EC600N bytes, EC600M bytes)
    (obj, ".rodata.pin_map", table(range(1, 42), EC600N_PINS), table(range(1, 42), EC600M_PINS))
    for obj in ("helios_gpio.c.o", "helios_extint.c.o", "helios_audio.c.o")
] + [("helios_pwm.c.o", ".data.pwm_map", table(range(4), EC600N_PWM), table(range(4), EC600M_PWM))]

with tempfile.TemporaryDirectory() as tmp:
    for obj, sec, old, new in PATCHES:
        subprocess.run([CROSS + "ar", "x", lib, obj], cwd=tmp, check=True)
        cur = subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", sec, obj, "/dev/stdout"],
                             cwd=tmp, capture_output=True, check=True).stdout
        if cur == new:
            print("skip  %-18s %s (already EC600M)" % (obj, sec))
            continue
        assert cur == old, "%s %s does not hold the expected EC600N table" % (obj, sec)
        assert len(new) == len(old)
        blob = os.path.join(tmp, "new.bin")
        open(blob, "wb").write(new)
        subprocess.run([CROSS + "objcopy", "--update-section", "%s=%s" % (sec, blob), obj], cwd=tmp, check=True)
        subprocess.run([CROSS + "ar", "r", lib, obj], cwd=tmp, check=True)
        print("patch %-18s %s -> EC600M" % (obj, sec))
