#!/bin/sh
# SDAD v6 -- I4 circular-deps ratchet (POSIX mirror of the .ps1).
# Detects a dependency cycle in a node-graph.json (each node's `dependencies`
# lists the node ids it reads). ASCII (L-01). Requires python3; if absent,
# NOTE-skips with exit 0 (the PS engine is authoritative on the developer's
# Windows machine; this mirror covers POSIX CI when python3 exists).
# Exit 0 = no cycle (or skipped), 1 = a cycle was found or error.
f="$1"
if [ -z "$f" ]; then echo "circular-deps: no file argument"; exit 1; fi
if [ ! -f "$f" ]; then echo "circular-deps: file not found: $f"; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "circular-deps: NOTE python3 not available -- POSIX check skipped"
  exit 0
fi
python3 - "$f" <<'PY'
import json, sys
f = sys.argv[1]
try:
    with open(f) as fh:
        j = json.load(fh)
except Exception as e:
    print("circular-deps: invalid JSON: %s" % e); sys.exit(1)
nodes = j.get("nodes") if isinstance(j, dict) else None
if not isinstance(nodes, list):
    nodes = []
adj = {}
for n in nodes:
    if not isinstance(n, dict) or "id" not in n:
        continue
    deps = n.get("dependencies")
    if not isinstance(deps, list):
        deps = []
    adj[str(n["id"])] = [str(d) for d in deps]

WHITE, GRAY, BLACK = 0, 1, 2
color = {k: WHITE for k in adj}
cycle = [None]

def visit(node, stack):
    color[node] = GRAY
    stack.append(node)
    for dep in adj.get(node, []):
        if dep not in adj:
            continue
        if color[dep] == GRAY:
            idx = stack.index(dep)
            cycle[0] = " -> ".join(stack[idx:] + [dep])
            return True
        if color[dep] == WHITE and visit(dep, stack):
            return True
    color[node] = BLACK
    stack.pop()
    return False

for start in list(adj.keys()):
    if color[start] == WHITE and visit(start, []):
        break

if cycle[0]:
    print("circular-deps: cycle detected in %s" % f)
    print("  - %s" % cycle[0])
    sys.exit(1)
print("circular-deps: OK (%s)" % f)
sys.exit(0)
PY
