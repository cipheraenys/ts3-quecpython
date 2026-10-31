"""Upload files to a QuecPython device through the friendly REPL.

usage: upload.py <port> <local file>=<device path> [...]
"""
import base64
import sys
import time

import serial


def run(s, line):
    s.reset_input_buffer()
    s.write(line.encode() + b"\r\n")
    out = b""
    t = time.time()
    while not out.rstrip().endswith(b">>>") and time.time() - t < 10:
        out += s.read(s.in_waiting or 1)
    text = out.decode(errors="replace")
    if "Traceback" in text or not out.rstrip().endswith(b">>>"):
        raise RuntimeError(text)
    return text.split("\n", 1)[1].rsplit(">>>", 1)[0].strip()


s = serial.Serial(sys.argv[1], 115200, timeout=0.2)
s.write(b"\x02\r\x03\x03")
time.sleep(0.8)
for spec in sys.argv[2:]:
    local, remote = spec.split("=", 1)
    data = open(local, "rb").read()
    run(s, "import ubinascii, uos; f = open(%r, 'wb')" % remote)
    for i in range(0, len(data), 384):
        run(s, "f.write(ubinascii.a2b_base64(%r))" % base64.b64encode(data[i:i + 384]).decode())
    run(s, "f.close()")
    size = run(s, "print(uos.stat(%r)[6])" % remote)
    print("%s -> %s: %s bytes (local %d)" % (local, remote, size, len(data)))
s.close()
