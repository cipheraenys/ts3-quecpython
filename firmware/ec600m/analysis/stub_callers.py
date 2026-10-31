"""For each kernel name, find its by-name stub in a stock customer_app.bin and the code that calls it.

usage: stub_callers.py <customer_app.bin> <objdump -D output of it> <name> [<name> ...]
"""
import re
import struct
import sys

app, dis_path = sys.argv[1], sys.argv[2]
d = open(app, "rb").read()[8:]
base = 0x80534008
dis = open(dis_path).read().splitlines()
index = {}
for i, line in enumerate(dis):
    m = re.match(r"^([0-9a-f]{8}):", line)
    if m:
        index[int(m.group(1), 16)] = i


def words(v):
    return [base + i for i in range(0, len(d) - 3, 2) if struct.unpack_from("<I", d, i)[0] == v]


def show(addr, before, after=2):
    i = index.get(addr)
    if i is not None:
        print("\n".join(dis[max(0, i - before):i + after]))


for name in sys.argv[3:]:
    s = d.find(name.encode() + b"\0")
    for lit in words(base + s):
        for st in range(lit - 0x40, lit, 2):
            for ref in words(st | 1):
                print("=== %s: stub 0x%08x, pointer at 0x%08x" % (name, st, ref))
                lit_line = "0x%08x" % ref
                for i, line in enumerate(dis):
                    if "; (" + lit_line + ")" in line:
                        print("\n".join(dis[max(0, i - 12):i + 6]))
                        print("---")
