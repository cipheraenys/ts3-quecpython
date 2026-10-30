"""Print the last <n> instructions (default 10) of <func> up to offset <hexoff>.

usage: show_site.py <objdump -d output> <func> <hexoff> [<n>]
"""
import re
import sys

dis, func, off = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
n = int(sys.argv[4]) if len(sys.argv) > 4 else 10
cur, rows = None, []
for line in open(dis):
    m = re.match(r"^[0-9a-f]+ <([^>]+)>:$", line)
    if m:
        cur = m.group(1)
        continue
    if cur == func:
        m = re.match(r"^\s+([0-9a-f]+):\s+(.*)$", line.rstrip())
        if m and "R_ARM" not in line:
            rows.append((int(m.group(1), 16), m.group(2)))
idx = max(i for i, (o, _) in enumerate(rows) if o <= off)
print("--- %s+0x%x" % (func, off))
for o, t in rows[max(0, idx - n):idx + 1]:
    print("  %4x: %s" % (o, t))
