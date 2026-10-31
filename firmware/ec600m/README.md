# EC600M QuecPython firmware from HeliosSDK

Builds QuecPython for the Quectel EC600M (ASR1606) from the public HeliosSDK, which has no
EC600M board. The new board `EC600MEU_LA` links the EC600N `libHeliosAPI.a` with the EC600M
`ql_common_api`; `ec600m_shim.c` bridges the differences (missing kernel names, UART init and
receive callback, LCD init layout, NOR flash API, per-task storage).

Status: runs on the BQ280. The REPL answers on the USB REPL port; `machine.Pin`, `misc.ADC`
and `audio.TTS` calls return normally. LCD, audio output and networking are not tested yet.

## Inputs (not in this repo)

| Input | Where |
|---|---|
| HeliosSDK `9d145cc` + 7 submodules | gitee `quecpython/HeliosSDK`, via `fetch/fetch_all.sh` |
| GCC 10.2.1 | `gcc-arm-none-eabi-10-2020-q4-major` (Arm) |
| `7z` on `PATH` | HeliosSDK's `build.sh` calls it |
| EC600M QuecOpen C-SDK | Quectel; only `ql-application/threadx/common/lib/ql_common_api.lib` is used |
| Stock EC600M QuecPython package, unzipped | Quectel, `QPY_OCPU_V0001_EC600M_EULA_FW`; `pack_ec600m.py` reuses its images |

## Build (Linux / WSL)

```sh
export COMPILER_PATH=~/helios_tc/gcc-arm-none-eabi-10-2020-q4-major
export CROSS=$COMPILER_PATH/bin/arm-none-eabi- QUECOPEN_SDK=~/ec600m/sdk/ql-sdk
SDK=~/helios_src/HeliosSDK STOCK=~/fw_ec600m_qpy/pkg

fetch/fetch_all.sh 3600 $SDK        # rerun until every FINAL line shows fail=0
python3 patch_sdk_ec600m.py $SDK
python3 mkboard_ec600m.py $SDK
(cd $SDK && sh build.sh make services/microPython @EC600MEU_LA EC600MEULA_HELIOS)
python3 pack_ec600m.py $SDK/output/binary/EC600MEULA_HELIOS.bin $STOCK EC600MEULA_HELIOS.bin
python3 verify_pkg.py EC600MEULA_HELIOS.bin $STOCK
```

HeliosSDK's `build.sh` exits with an error at its EC600N packaging step (`DBG.7z` is not in
the public SDK). `output/binary/EC600MEULA_HELIOS.bin` is written before that;
`pack_ec600m.py` replaces the packaging.

## Flash

Same as stock QuecPython (see [devices/bq280](../../devices/bq280/README.md)):

```
adownload -u -a -s 115200 -q EC600MEULA_HELIOS.bin
```

Then cold boot. To go back, flash the stock QuecPython package the same way.

If `adownload` stops mid-transfer (USB error 31), run it again: the bootloader is erased by then,
so the module stays in download mode.

## Boot self-test

At boot the image looks up every kernel function it may call and writes the missing names to
`ec600m_api_report`. Take its address from `output/binary/EC600MEULA_HELIOS.map` (0x7E3A8CA8 in
the current build), then in the REPL:

```python
import uctypes
print(bytes(uctypes.bytearray_at(0x7E3A8CA8, 2048)).split(b'\0')[0].decode())
```

A missing name means that feature returns -1; it has to be bridged in `ec600m_shim.c`. The
current build reports 62 of 299 missing: SMS, voice call, cell locator, Wi-Fi scan, FOTA, APN
get/set, AMR stream, `printf`/`vprintf` and a few others.

## Limits

- `Pin.GPIO42`..`45` are not available (the pin table keeps the EC600N's 41 entries).
- Camera, QR code, JPEG, SD card and Quectel cloud are compiled out.
- Device report (IMEI sent to Quectel) is compiled out.
- `uos.uname()` shows an empty `qpyver` (`ql_dev_get_qpy_version` is missing).
- ADC channel 1 reads about 1120 at idle; the stock firmware reads 1201. Not investigated.

## Files

| File | |
|---|---|
| `patch_sdk_ec600m.py` | HeliosSDK source patches |
| `mkboard_ec600m.py` | creates the board; runs `patch_maps_ec600m.py`, `gen_api_names.py` |
| `ec600m_shim.c`, `ec600m_linkscript.ld` | board sources |
| `pack_ec600m.py`, `verify_pkg.py` | package and check against stock |
| `fetch/` | Gitee downloader (clones of this repo drop mid-transfer) |
| `analysis/` | disassembly helpers used while porting |
