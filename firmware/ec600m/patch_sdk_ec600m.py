"""Patch HeliosSDK sources for the EC600MEU_LA board. Idempotent.

usage: patch_sdk_ec600m.py [<sdk root>]
"""
import os
import sys

sdk = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/helios_src/HeliosSDK")


def patch(rel, old, new, marker):
    path = os.path.join(sdk, rel)
    text = open(path).read()
    if marker in text:
        print("skip  ", rel)
        return
    assert text.count(old) == 1, "%s: anchor missing or not unique" % rel
    open(path, "w").write(text.replace(old, new))
    print("patch ", rel)


# 1. Audio channel table: same as the other ASR boards, channel 0 only.
patch("services/microPython/ports/quectel/core/source/modaudio.c",
      "#elif defined(BOARD_EC800NCN_LA)\n\t{1, 0, 0}\n",
      "#elif defined(BOARD_EC800NCN_LA)\n\t{1, 0, 0}\n#elif defined(BOARD_EC600MEU_LA)\n\t{1, 0, 0}\n",
      "BOARD_EC600MEU_LA")

# 2. LCD type enum: libHeliosAPI.a (EC600N) was built with HELIOS_LCD_TYPE_RGB666.
patch("peripheral/helios_lcd.h",
      "|| defined(BOARD_EC800NCN_LA))\n\t HELIOS_LCD_TYPE_RGB666,",
      "|| defined(BOARD_EC800NCN_LA) || defined(BOARD_EC600MEU_LA))\n\t HELIOS_LCD_TYPE_RGB666,",
      "BOARD_EC600MEU_LA")

# 3. With QUECTHING off, modwifilocator.c still needs Quos_md5*: build quos_md5.c alone.
patch("services/microPython/microPython.mk",
      "$(NAME)_COMPONENTS += components/quecsdk\nendif\nendif\n",
      "$(NAME)_COMPONENTS += components/quecsdk\nendif\nelse\n"
      "# modwifilocator.c only needs Quos_md5*\n"
      "$(NAME)_SRCS += ../../components/quecsdk/kernel/quos_md5.c\n"
      "$(NAME)_INCS += ../../components/quecsdk/kernel ../../components/quecsdk/driverLayer\n"
      "endif\n",
      "quos_md5.c\n")

# 4. Same for the qstr Makefile, which has its own include list.
patch("services/microPython/ports/quectel/core/Makefile",
      "INC += -I$(ROOT)/components/quecsdk/kernel \nendif\n",
      "INC += -I$(ROOT)/components/quecsdk/kernel \nelse\n"
      "# modwifilocator.c includes quos_md5.h\n"
      "INC += -I$(ROOT)/components/quecsdk/driverLayer\n"
      "INC += -I$(ROOT)/components/quecsdk/kernel\n"
      "endif\n",
      "quecsdk/driverLayer\nINC")

# 5. Use the board's linkscript.ld when it has one (EC600M runs in place; EC600N loads to RAM).
patch("Makefile",
      "export LD_FILE = system/platform/$(strip $(PLAT))/scripts/linkscript.ld\n",
      "BOARD_LD_FILE = system/platform/$(strip $(PLAT))/boards/$(strip $(BOARD))/linkscript.ld\n"
      "export LD_FILE = $(if $(wildcard $(BOARD_LD_FILE)),$(BOARD_LD_FILE),"
      "system/platform/$(strip $(PLAT))/scripts/linkscript.ld)\n",
      "BOARD_LD_FILE")

# 6. devreport.c sends the IMEI to iot-south.quectel.com:6789 when a Chinese SIM is present.
patch("services/microPython/ports/quectel/core/source/mpconfigport.h",
      "#define MICROPY_ENABLE_DEVICE_REPORT          (1)\n",
      "#if defined(BOARD_EC600MEU_LA)\n"
      "#define MICROPY_ENABLE_DEVICE_REPORT          (0)  /* no IMEI report to Quectel */\n"
      "#else\n"
      "#define MICROPY_ENABLE_DEVICE_REPORT          (1)\n"
      "#endif\n",
      "no IMEI report to Quectel")
