#!/bin/bash
# Fetch HeliosSDK and its 7 submodules from Gitee with fetch_gitee.py. Resumable: rerun until
# every FINAL line shows fail=0 (451 content-filtered files excepted).
# usage: fetch_all.sh [<seconds budget>] [<dest>]
# Gitee allows 60 unauthenticated API calls per hour; each repo needs one for its tree listing.
BUDGET=${1:-540}
D=${2:-~/helios_src/HeliosSDK}
HERE=$(cd "$(dirname "$0")" && pwd)
TREES=${TREES:-~/helios_tools}
END=$(( $(date +%s) + BUDGET ))
mkdir -p "$TREES"

# name ref dest; submodule refs are the ones HeliosSDK 9d145cc points to
SUBS="
mbedtls      b5db751efbcbf509ff96b392399676e36d7e21c2 system/mbedtls
quecsdk      523fd7aa21880623b024fb5f2161347b6366c982 components/quecsdk
lvgl         9384e7da139f6b89d8d07fe8a1ef7346dba1d27a components/lvgl
jpeg         738e7680562ed1f1cfadd9bbd68c3a77ef2ec144 components/jpeg
ZBar         f1a6efe6f3e1689d85b24b224eea1637c8b55389 components/ZBar
rtmpdump     b801932b8ed33b3981f031d5709f7d23fc2933c0 components/rtmpdump
microPython  e7c4b19d14737a2a8742028030408ef25e565fa5 services/microPython
HeliosSDK    9d145cc43eeef7bcba5eb7b35d68b672c57430ee .
"

echo "$SUBS" | while read -r repo ref dest; do
  [ -z "$repo" ] && continue
  left=$(( END - $(date +%s) ))
  [ "$left" -lt 20 ] && { echo "budget used up, stopping before $repo"; break; }
  tree="$TREES/tree_$repo.json"
  [ -s "$tree" ] || curl -s -o "$tree" "https://gitee.com/api/v5/repos/quecpython/$repo/git/trees/$ref?recursive=1"
  echo "=== $repo (${left}s left) ==="
  timeout "$left" python3 -I "$HERE/fetch_gitee.py" quecpython "$repo" "$ref" "$D/$dest" "$tree" 12 2>&1 \
    | grep -E "todo=|FINAL|FAIL" | grep -v "HTTP Error 451"
done
