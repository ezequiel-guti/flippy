#!/bin/sh
# SDAD v6 -- I7 audit-report-integrity ratchet (POSIX mirror of the .ps1).
# Catch a deliberately weakened audit report over a (report.md + manifest.md) pair.
# Enforces the same three integrity invariants as the .ps1 (see its header):
#   A. Reproducibility stamp (BR-13): SDAD version + exact model string present.
#   B. No fabricated alignment finding (BR-09): manifest "Elicitation: none" =>
#      "Business alignment (5a):" verdict must be "not assessable".
#   C. Evidence-gap surfacing: each not_assessable gap area appears in the report.
# Pure POSIX -- no python, no sed/awk (L-05 sibling). Exit 0 = intact, 1 = at
# least one violation or error (fails closed). L-01: pure ASCII.
# Usage: sh checks/audit-report-integrity.sh path/to/report-dir

dir=$1
[ -n "$dir" ] || { echo "audit-report-integrity: no directory argument"; exit 1; }
report="$dir/report.md"
manifest="$dir/manifest.md"
[ -f "$report" ] || { echo "audit-report-integrity: report.md not found in $dir"; exit 1; }
[ -f "$manifest" ] || { echo "audit-report-integrity: manifest.md not found in $dir"; exit 1; }

fails=0

# Rule A -- reproducibility stamp (BR-13)
if ! grep -qiE 'SDAD v[0-9]' "$report"; then
  echo "  - A: missing SDAD version stamp (BR-13 reproducibility)"
  fails=$((fails + 1))
fi
if ! grep -qiE 'claude-[a-z0-9.-]+' "$report"; then
  echo "  - A: missing exact model string (BR-13 reproducibility)"
  fails=$((fails + 1))
fi

# Rule B -- no fabricated alignment finding when elicitation is absent (BR-09)
# Tolerate markdown around the field ("**Elicitation:** none").
if grep -qiE 'elicitation[^A-Za-z0-9]*none' "$manifest" || grep -qiE 'not.?assessable.*elicitation' "$manifest"; then
  line=$(grep -iE 'business alignment \(5a\):' "$report" | head -n 1)
  if [ -z "$line" ]; then
    echo "  - B: business-alignment (5a) verdict line missing"
    fails=$((fails + 1))
  elif printf '%s' "$line" | grep -qiE 'not assessable'; then
    : # honest: explicitly not assessable -- OK
  elif printf '%s' "$line" | grep -qiE '(CRITICAL|HIGH|MEDIUM|LOW)'; then
    echo "  - B: fabricated 5a finding with no elicitation input (BR-09)"
    fails=$((fails + 1))
  else
    echo "  - B: 5a verdict not declared not-assessable despite no elicitation"
    fails=$((fails + 1))
  fi
fi

# Rule C -- every not_assessable gap area must be surfaced in the report
areas=$(grep -iE '^\|[[:space:]]*[A-Za-z0-9_-]+[[:space:]]*\|.*not_assessable' "$manifest" \
  | while IFS='|' read -r _ a _; do
      a=$(printf '%s' "$a" | tr -d '[:blank:]')   # strip spaces/tabs only -- keep newline separator
      printf '%s\n' "$a"
    done)
for area in $areas; do
  [ -n "$area" ] || continue
  if ! grep -qF "$area" "$report"; then
    echo "  - C: gap area '$area' declared in manifest but not surfaced in report"
    fails=$((fails + 1))
  fi
done

if [ "$fails" -gt 0 ]; then
  echo "audit-report-integrity: $fails violation(s) in $dir"
  exit 1
fi
echo "audit-report-integrity: OK ($dir)"
exit 0
