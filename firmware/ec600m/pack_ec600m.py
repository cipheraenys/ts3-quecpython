"""Build a flashable EC600M QuecPython package around a Helios customer_app.

Copies the stock aboot package, replaces customer_app.bin, and updates the customer_app image
length and the trailing CRC32 in partition.bin. Leaves out firmware.bin, system.img and
fota.json: download.json does not use them, and they carry the stock table and app.

usage: pack_ec600m.py <app.bin> <stock package dir> <out.bin>
"""
import os
import struct
import sys
import zipfile
import zlib

app_bin, stock_dir, out_path = sys.argv[1:4]

TAG = b"QUECTEL\0"  # first 8 bytes of the stock customer_app.bin
DROP = {"firmware.bin", "system.img", "fota.json"}
body = open(app_bin, "rb").read()
app = TAG + body

ptable = bytearray(open(os.path.join(stock_dir, "partition.bin"), "rb").read())
assert ptable[:4] == b"BTPA", "not an ASR partition table"
assert struct.unpack_from("<I", ptable, len(ptable) - 4)[0] == zlib.crc32(bytes(ptable[:-4])), \
    "stock partition.bin trailer is not CRC32 of the table"
pos = ptable.find(b"customer_app\0")
assert pos > 0 and ptable.find(b"customer_app\0", pos + 1) < 0, "customer_app entry not unique"
size, addr, imglen = struct.unpack_from("<3I", ptable, pos + 52)
assert addr == 0x80534000, "unexpected customer_app address 0x%08X" % addr
assert len(app) <= size, "app %d bytes > partition %d bytes" % (len(app), size)
assert struct.unpack_from("<I", body, 24)[0] == 0x7E320000, "header data_start is not 0x7E320000"
struct.pack_into("<I", ptable, pos + 60, len(app))
struct.pack_into("<I", ptable, len(ptable) - 4, zlib.crc32(bytes(ptable[:-4])))
print("customer_app: %d bytes (stock %d), %d bytes free" % (len(app), imglen, size - len(app)))

with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(os.listdir(stock_dir)):
        if name in DROP:
            continue
        if name == "customer_app.bin":
            z.writestr(name, app)
        elif name == "partition.bin":
            z.writestr(name, bytes(ptable))
        else:
            z.write(os.path.join(stock_dir, name), name)
print("wrote", out_path, "(left out: %s)" % ", ".join(sorted(DROP)))
