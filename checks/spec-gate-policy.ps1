# SDAD v5.1 -- shared spec-gate decision policy (Windows / PowerShell engine).
# Single source of truth for the spec gate; mirror of checks/spec-gate-policy.sh.
# Consumed by the local PreToolUse hook and (via pwsh) by CI. See the .sh header.
# Usage: powershell -File checks/spec-gate-policy.ps1 -Path <path> [-ProjectDir <dir>]
# Exit 0 = allow, 2 = deny (reason on stderr). Deterministic; does not fail open.
# L-01: pure ASCII.
param(
    [string]$Path,
    [string]$ProjectDir
)
$ErrorActionPreference = "Stop"

if (-not $Path) { exit 0 }
if (-not $ProjectDir) {
    if ($env:CLAUDE_PROJECT_DIR) { $ProjectDir = $env:CLAUDE_PROJECT_DIR }
    else { $ProjectDir = (Get-Location).Path }
}

$proj = ($ProjectDir -replace '\\', '/').TrimEnd('/')
$t = $Path -replace '\\', '/'
$rel = $t
if ($rel.ToLower().StartsWith($proj.ToLower())) {
    $rel = $rel.Substring($proj.Length).TrimStart('/')
}
$relLow = $rel.ToLower()
$name = [System.IO.Path]::GetFileName($relLow)
$ext  = [System.IO.Path]::GetExtension($relLow)

# R1 allowlist
$allowNames = @('spec.md', 'spec_retroactive.md', 'decisions.md',
                'lesson_library.md', 'changelog.md', 'readme.md')
if ($allowNames -contains $name) { exit 0 }
if ($ext -eq '.md') { exit 0 }
foreach ($prefix in @('docs/', '.sdad/', '.claude/', 'hub/')) {
    if ($relLow.StartsWith($prefix)) { exit 0 }
}

# $docfinal sentinel
if (Test-Path (Join-Path $proj '.sdad/DOCFINAL_ACTIVE')) { exit 0 }

# $audit sentinel -- $audit runs without an approved Spec, same as $docfinal (BR-14)
if (Test-Path (Join-Path $proj '.sdad/AUDIT_ACTIVE')) { exit 0 }

# R2 code-file denylist; unknown extensions default to allow
$codeExt = @('.py', '.js', '.ts', '.jsx', '.tsx', '.ps1', '.psm1', '.sh',
             '.bat', '.cmd', '.sql', '.html', '.css', '.json', '.yaml',
             '.yml', '.toml', '.ini', '.cs', '.java', '.go', '.rs',
             '.rb', '.php')
if ($codeExt -notcontains $ext) { exit 0 }

# The gate
$specPath = Join-Path $proj 'SPEC.md'
if (-not (Test-Path $specPath)) {
    [Console]::Error.WriteLine("SDAD gate: no SPEC.md in this project -- code writes are blocked until a Spec is approved. Run `$spec (or `$docfinal for retroactive documentation).")
    exit 2
}
$spec = Get-Content $specPath -Raw -Encoding UTF8
if ($spec -notmatch 'SPEC STATUS: APPROVED') {
    [Console]::Error.WriteLine("SDAD gate: SPEC.md is not approved (missing 'SPEC STATUS: APPROVED' marker). Get developer approval before writing code.")
    exit 2
}
exit 0
