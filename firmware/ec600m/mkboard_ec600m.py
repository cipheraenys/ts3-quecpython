"""Create the EC600MEU_LA board in HeliosSDK from EC600NCN_LA.

Installs the EC600M ql_common_api.a, ec600m_shim.c and linkscript.ld; patches libHeliosAPI.a
(weakened duplicates, LCD init and UART config redirected to the shim, pin and UART maps);
generates ec600m_api_names.h; turns off unused features; registers the board in platform.json.
Run patch_sdk_ec600m.py as well.

usage: mkboard_ec600m.py [<sdk root>]
env:   CROSS (toolchain prefix), QUECOPEN_SDK (EC600M QuecOpen ql-sdk directory)
"""
import json
import os
import re
import shutil
import subprocess
import sys

CROSS = os.environ.get("CROSS", os.path.expanduser(
    "~/helios_tc/gcc-arm-none-eabi-10-2020-q4-major/bin/arm-none-eabi-"))
QUECOPEN_SDK = os.environ.get("QUECOPEN_SDK", os.path.expanduser("~/ec600m/sdk/ql-sdk"))

sdk = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/helios_src/HeliosSDK")
here = os.path.dirname(os.path.abspath(__file__))
boards = os.path.join(sdk, "system/platform/ASR/boards")
src, dst = os.path.join(boards, "EC600NCN_LA"), os.path.join(boards, "EC600MEU_LA")
lib = os.path.join(dst, "libraries", "libHeliosAPI.a")
api = os.path.join(dst, "libraries", "ql_common_api.a")

# Not used on the BQ280: camera, QR codes, SD card, Quectel cloud.
OFF = ["CONFIG_CAMERA", "CONFIG_CAMERA_DECODE", "CONFIG_CAMERA_SAVEPHOTOS",
       "CONFIG_JPEG", "CONFIG_QRCODE", "CONFIG_QUECTHING", "CONFIG_SPI_SDCARD"]

# helios_sockets.c in libHeliosAPI defines these too; keep the EC600M ql_common_api versions.
DUPS = ["inet_aton", "inet_ntoa", "inet_ntop", "inet_pton", "inet6_aton", "inet6_ntoa",
        "ipaddr_addr", "ql_get_soc_errno", "ql_soc_generate_port"]

if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst, symlinks=True)
os.rename(os.path.join(dst, "EC600NCN_LA.mk"), os.path.join(dst, "EC600MEU_LA.mk"))
mk = os.path.join(dst, "EC600MEU_LA.mk")
body = open(mk).read().replace("EC600NCN_LA", "EC600MEU_LA")
open(mk, "w").write(body + "\n$(NAME)_SRCS += ec600m_shim.c\n")

# ql_common_api: the EC600M build, whose startup (ql_main.o) matches the EC600M kernel.
shutil.copyfile(os.path.join(QUECOPEN_SDK, "ql-application/threadx/common/lib/ql_common_api.lib"), api)
shutil.copyfile(os.path.join(here, "ec600m_shim.c"), os.path.join(dst, "ec600m_shim.c"))
shutil.copyfile(os.path.join(here, "ec600m_linkscript.ld"), os.path.join(dst, "linkscript.ld"))
print("board files: ql_common_api.a (EC600M), ec600m_shim.c, linkscript.ld")

subprocess.run([CROSS + "objcopy"] + ["--weaken-symbol=" + s for s in DUPS] + [lib], check=True)
# Calls the shim adapts: LCD init struct layout; UART config result and receive callback.
subprocess.run([CROSS + "objcopy",
                "--redefine-sym", "ql_lcd_init=ec600n_ql_lcd_init",
                "--redefine-sym", "ql_uart_set_dcbconfig=ec600m_uart_set_dcbconfig",
                "--redefine-sym", "Helios_UART_Init=ec600n_Helios_UART_Init", lib], check=True)
print("libHeliosAPI.a: weakened %d duplicates, LCD init and UART init/config -> shim" % len(DUPS))
subprocess.run([sys.executable, "-I", os.path.join(here, "patch_maps_ec600m.py"), lib], check=True)
subprocess.run([sys.executable, "-I", os.path.join(here, "gen_api_names.py"), sdk, api, lib,
                os.path.join(dst, "ec600m_shim.c"), os.path.join(dst, "ec600m_api_names.h")],
               check=True)

cfg = os.path.join(dst, "config", "config.mk")
text = open(cfg).read()
for k in OFF:
    text = re.sub(r"^%s=y$" % k, "# %s is not set" % k, text, flags=re.M)
open(cfg, "w").write(text)
hdr = os.path.join(dst, "config", "autoconf.h")
text = open(hdr).read()
for k in OFF:
    text = re.sub(r"^#define %s 1\n" % k, "", text, flags=re.M)
open(hdr, "w").write(text)
print("config: off", " ".join(k[len("CONFIG_"):] for k in OFF))

pj = os.path.join(sdk, "system/platform/platform.json")
plat = json.load(open(pj))
if "EC600MEU_LA" not in plat["ASR"]:
    plat["ASR"].append("EC600MEU_LA")
    json.dump(plat, open(pj, "w"), indent="\t")
print("platform.json: EC600MEU_LA registered")
