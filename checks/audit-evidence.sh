#!/bin/sh
# SDAD v6 -- I1 audit-evidence ratchet (POSIX mirror of audit-evidence.ps1).
# Validates a node-graph.json against the evidence schema (.sdad/audit/SCHEMA.md).
# ASCII (L-01). Requires python3; if absent, NOTE-skips with exit 0 (the PS engine
# is authoritative on the developer's Windows machine; this mirror covers POSIX CI
# when python3 exists). Exit 0 = valid (or skipped), 1 = invalid or error.
f="$1"
if [ -z "$f" ]; then echo "audit-evidence: no file argument"; exit 1; fi
if [ ! -f "$f" ]; then echo "audit-evidence: file not found: $f"; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "audit-evidence: NOTE python3 not available -- POSIX validation skipped"
  exit 0
fi
python3 - "$f" <<'PY'
import json, sys
f = sys.argv[1]
errs = []
try:
    with open(f) as fh:
        j = json.load(fh)
except Exception as e:
    print("audit-evidence: invalid JSON: %s" % e); sys.exit(1)
if not isinstance(j, dict):
    print("audit-evidence: top-level JSON is not an object"); sys.exit(1)
for k in ("project","acquired_at","acquisition_path","pyplan_version","nodes","gaps"):
    if k not in j:
        errs.append("missing top-level key: %s" % k)
ap = j.get("acquisition_path")
if "acquisition_path" in j and ap not in ("ppl-export","mcp-read","manual"):
    errs.append("acquisition_path not one of ppl-export|mcp-read|manual: %r" % ap)
types = ("data","function","interface","input")
nodes = j.get("nodes")
if not isinstance(nodes, list):
    nodes = []
for i, n in enumerate(nodes):
    if not isinstance(n, dict):
        errs.append("node[%d] is not an object" % i); continue
    for k in ("id","type","has_result_assigned","dependencies","code_snippet","mcp_decorated"):
        if k not in n:
            errs.append("node[%d] missing key: %s" % (i, k))
    if "type" in n and n["type"] not in types:
        errs.append("node[%d] type not one of data|function|interface|input: %r" % (i, n["type"]))
    if "has_result_assigned" in n and not isinstance(n["has_result_assigned"], bool):
        errs.append("node[%d] has_result_assigned not boolean" % i)
    if "id" in n and not str(n["id"]).strip():
        errs.append("node[%d] id empty" % i)
gaps = j.get("gaps")
if not isinstance(gaps, list):
    gaps = []
for g, gap in enumerate(gaps):
    if not isinstance(gap, dict):
        errs.append("gap[%d] is not an object" % g); continue
    for k in ("area","reason","status"):
        if k not in gap:
            errs.append("gap[%d] missing key: %s" % (g, k))
    if "status" in gap and gap["status"] != "not_assessable":
        errs.append("gap[%d] status not 'not_assessable': %r" % (g, gap["status"]))
if errs:
    print("audit-evidence: %d violation(s) in %s" % (len(errs), f))
    for e in errs:
        print("  - %s" % e)
    sys.exit(1)
print("audit-evidence: OK (%s)" % f)
sys.exit(0)
PY
