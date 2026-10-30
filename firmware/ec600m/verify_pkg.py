"""Check a packed EC600M firmware against the stock package. Exits 1 on any failure.

usage: verify_pkg.py <pkg> <stock package dir>
"""
import json
import os
import struct
import sys
import zipfile
import zlib

pkg, stock = sys.argv[1:3]
z = zipfile.ZipFile(pkg)
names = set(z.namelist())
app, ptab = z.read("customer_app.bin"), z.read("partition.bin")
i = ptab.find(b"customer_app\0")
init = struct.unpack_from("<3I", app, 8)
data_load, data_start, data_end = struct.unpack_from("<3I", app, 28)
tag_ok = app[:8] == b"QUECTEL\0"
len_ok = struct.unpack_from("<I", ptab, i + 60)[0] == len(app)
crc_ok = struct.unpack_from("<I", ptab, len(ptab) - 4)[0] == zlib.crc32(ptab[:-4])
print("tag         :", "OK" if tag_ok else "BAD %r" % app[:8])
print("init fns    : %s" % " ".join("0x%08X" % f for f in init))
print("data        : load 0x%08X start 0x%08X end 0x%08X" % (data_load, data_start, data_end))
print("ptable len  :", "OK" if len_ok else "BAD")
print("ptable crc  :", "OK" if crc_ok else "BAD")

stock_ptab = open(os.path.join(stock, "partition.bin"), "rb").read()
allowed = set(range(i + 60, i + 64)) | set(range(len(ptab) - 4, len(ptab)))
diff = set(k for k in range(len(ptab)) if ptab[k] != stock_ptab[k])
print("ptable diff :", "OK" if diff <= allowed else "UNEXPECTED %s" % sorted(diff - allowed))

needed = {e["image"] for e in json.load(open(os.path.join(stock, "download.json"))) if e.get("image")}
print("download.json images:", "OK" if needed <= names else "MISSING %s" % (needed - names))
others = [n for n in names if n not in ("customer_app.bin", "partition.bin")]
same = [n for n in others if z.read(n) == open(os.path.join(stock, n), "rb").read()]
print("other images: %d/%d identical to stock; left out: %s"
      % (len(same), len(others), ", ".join(sorted(set(os.listdir(stock)) - names))))
ok = tag_ok and len_ok and crc_ok and diff <= allowed and needed <= names and len(same) == len(others)
sys.exit(0 if ok else 1)
