#!/bin/sh
# SDAD v6 -- I2 MCP tool audit check (POSIX mirror of mcp-tool-audit.ps1).
# Audits @mcp_tool nodes in a Python file via .sdad/audit/lib/mcp_lint.py.
# ASCII (L-01). Requires python3/python; if absent, NOTE-skips with exit 0.
# Usage:  sh checks/mcp-tool-audit.sh path/to/node.py
# Exit 0 = clean (or skipped), 1 = findings present or tool error.
f="$1"
if [ -z "$f" ]; then echo "mcp-tool-audit: no file argument"; exit 1; fi
if [ ! -f "$f" ]; then echo "mcp-tool-audit: file not found: $f"; exit 1; fi

py=""
if command -v python3 >/dev/null 2>&1; then py="python3";
elif command -v python >/dev/null 2>&1; then py="python"; fi
if [ -z "$py" ]; then
  echo "mcp-tool-audit: NOTE python not available -- MCP lint skipped"
  exit 0
fi

dir=$(dirname "$0")
"$py" "$dir/../.sdad/audit/lib/mcp_lint.py" "$f"
exit $?
