"""Download one Gitee repo at a ref, file by file, from its git tree listing. Resumable.

Large clones and ZIP downloads from gitee.com drop mid-transfer; single files do not. Files
already present with the right size are skipped. Raw URLs that return 403 are fetched through
the blob API. Gitee answers 451 for some files (content filter); they are reported and skipped.

usage: fetch_gitee.py <owner> <repo> <ref> <dest dir> <tree.json> [<workers>]
tree.json: GET https://gitee.com/api/v5/repos/<owner>/<repo>/git/trees/<ref>?recursive=1
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

OWNER, REPO, REF, DEST, TREE = sys.argv[1:6]
WORKERS = int(sys.argv[6]) if len(sys.argv) > 6 else 12
API = "https://gitee.com/api/v5/repos/%s/%s" % (OWNER, REPO)
RAW = "https://gitee.com/%s/%s/raw/%s/" % (OWNER, REPO, REF)
UA = {"User-Agent": "curl/8"}


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 451):
                raise
            last = e
        except Exception as e:
            last = e
        time.sleep(1 + i)
    raise last


def fetch(path, entry):
    out = os.path.join(DEST, path)
    try:
        data = get(RAW + urllib.request.quote(path))
    except urllib.error.HTTPError as e:
        if e.code != 403:
            raise
        data = base64.b64decode(json.loads(get("%s/git/blobs/%s" % (API, entry["sha"])))["content"])
    if len(data) != entry["size"]:
        raise IOError("size %d != %d" % (len(data), entry["size"]))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out + ".part", "wb") as f:
        f.write(data)
    os.replace(out + ".part", out)


def order(item):
    """Files the ASR build does not need go last, so a timeout cuts those first."""
    p, e = item
    cold = any(k in p for k in ("/win32", "Unisoc", "/RDA", "Qualcomm")) \
        or (p.startswith("ports/") and not p.startswith("ports/quectel")) \
        or p.startswith(("tests/", "docs/", "examples/"))
    return (cold, e["size"] > 4_000_000, p)


def have(e):
    p = os.path.join(DEST, e["path"])
    return os.path.exists(p) and os.path.getsize(p) == e["size"]


todo = sorted(((e["path"], e) for e in json.load(open(TREE))["tree"]
               if e["type"] == "blob" and not have(e)), key=order)
print("todo=%d workers=%d" % (len(todo), WORKERS), flush=True)
ok = fail = 0
t0 = time.time()
with ThreadPoolExecutor(WORKERS) as ex:
    futs = {ex.submit(fetch, p, e): p for p, e in todo}
    for f in as_completed(futs):
        try:
            f.result()
            ok += 1
        except Exception as x:
            fail += 1
            print("FAIL %s: %s" % (futs[f], x), flush=True)
        if (ok + fail) % 100 == 0:
            print("progress ok=%d fail=%d / %d  %.0fs" % (ok, fail, len(todo), time.time() - t0), flush=True)
print("FINAL ok=%d fail=%d / %d" % (ok, fail, len(todo)), flush=True)
