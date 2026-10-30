"""For each symbol, list the functions in an ARM archive that call it or take its address.

usage: callers.py <objdump> <archive> <symbol> [<symbol> ...]
"""
import re
import subprocess
import sys

objdump, archive, wanted = sys.argv[1], sys.argv[2], set(sys.argv[3:])
out = subprocess.run([objdump, "-dr", archive], capture_output=True, text=True).stdout
func, hits = None, {}
for line in out.splitlines():
    m = re.match(r"^[0-9a-f]+ <([^>]+)>:$", line)
    if m:
        func = m.group(1)
        continue
    m = re.search(r"R_ARM_(?:THM_CALL|THM_JUMP24|ABS32)\s+(\S+)", line)
    if m and func and m.group(1) in wanted:
        hits.setdefault(m.group(1), set()).add(func)
for callee in sorted(wanted):
    print("%-32s <- %s" % (callee, ", ".join(sorted(hits.get(callee, []))) or "(no caller)"))
