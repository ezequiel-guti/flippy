# SDAD v5 -- $agent liveness wrapper (Windows / PowerShell), I4 / SPEC F5.
# Wraps a `claude --print` delegation with a timeout and an empty-output check,
# so a hung or silent sub-agent fails fast and visibly instead of stalling.
#
# Usage (real delegation):
#   powershell -File .sdad/lib/agent-run.ps1 -Prompt "<system context + task>"
#       [-OutFile .sdad/agent_output.tmp] [-TimeoutSec 600]
#
# Exit codes (surfaced to the caller -- never proceed silently on non-zero):
#   0  success: OutFile written and non-empty
#   1  empty/missing output (agent produced nothing)
#   2  timeout (TimeoutSec elapsed -- process killed)
#   3  claude CLI not found / failed to start
#
# OD-3: default timeout 600s (10 min). The exe is fixed to `claude --print`;
# the SDAD_AGENT_EXE env var overrides it ONLY for the eval scenario, which
# points it at a self-contained stand-in that ignores the extra args. Real
# callers never set it.
# Pure ASCII (L-01).
param(
    [Parameter(Mandatory = $true)][string]$Prompt,
    [string]$OutFile = ".sdad/agent_output.tmp",
    [int]$TimeoutSec = 600
)
$ErrorActionPreference = "Stop"

$Exe = if ($env:SDAD_AGENT_EXE) { $env:SDAD_AGENT_EXE } else { "claude" }

if (($Exe -eq "claude") -and (-not (Get-Command claude -ErrorAction SilentlyContinue))) {
    Write-Host "agent-run: claude CLI not found -- cannot delegate (install it or check PATH)"
    exit 3
}

# Resolve OutFile to an absolute path and ensure its directory exists.
$outDir = Split-Path -Parent $OutFile
if ($outDir -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
if (Test-Path $OutFile) { Remove-Item $OutFile -Force -ErrorAction SilentlyContinue }
$errFile = "$OutFile.err"

$argList = @("--print", $Prompt)
try {
    $p = Start-Process -FilePath $Exe -ArgumentList $argList -NoNewWindow -PassThru `
        -RedirectStandardOutput $OutFile -RedirectStandardError $errFile
} catch {
    Write-Host "agent-run: failed to start '$Exe': $($_.Exception.Message)"
    exit 3
}

if (-not $p.WaitForExit($TimeoutSec * 1000)) {
    try { $p.Kill() } catch {}
    Write-Host "agent-run: TIMEOUT after $TimeoutSec s -- delegation killed, not proceeding silently"
    Remove-Item $errFile -Force -ErrorAction SilentlyContinue
    exit 2
}

$hasOutput = (Test-Path $OutFile) -and ((Get-Item $OutFile).Length -gt 0)
Remove-Item $errFile -Force -ErrorAction SilentlyContinue
if (-not $hasOutput) {
    Write-Host "agent-run: empty/missing output from delegation -- surfacing error, not proceeding"
    exit 1
}
exit 0
