#!/bin/sh
# SDAD v6 -- I4 missing-result-assign ratchet (POSIX mirror of the .ps1).
# Flags calculation nodes (type data|function) in a node-graph.json that lack
# result= (has_result_assigned == false). ASCII (L-01). Requires python3; if
# absent, NOTE-skips with exit 0 (the PS engine is authoritative on the
# developer's Windows machine; this mirror covers POSIX CI when python3 exists).
# Exit 0 = no offending nodes (or skipped), 1 = at least one offender or error.
f="$1"
if [ -z "$f" ]; then echo "missing-result-assign: no file argument"; exit 1; fi
if [ ! -f "$f" ]; then echo "missing-result-assign: file not found: $f"; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "missing-result-assign: NOTE python3 not available -- POSIX check skipped"
  exit 0
fi
python3 - "$f" <<'PY'
import json, sys
f = sys.argv[1]
try:
    with open(f) as fh:
        j = json.load(fh)
except Exception as e:
    print("missing-result-assign: invalid JSON: %s" % e); sys.exit(1)
nodes = j.get("nodes") if isinstance(j, dict) else None
if not isinstance(nodes, list):
    nodes = []
offenders = []
for n in nodes:
    if not isinstance(n, dict):
        continue
    t = n.get("type", "")
    if t not in ("data", "function"):
        continue
    if not bool(n.get("has_result_assigned", False)):
        offenders.append("%s (%s)" % (n.get("id", "<no-id>"), t))
if offenders:
    print("missing-result-assign: %d node(s) without result= in %s" % (len(offenders), f))
    for o in offenders:
        print("  - %s" % o)
    sys.exit(1)
print("missing-result-assign: OK (%s)" % f)
sys.exit(0)
PY
