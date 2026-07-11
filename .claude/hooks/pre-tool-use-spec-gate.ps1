# SDAD v5.1 -- PreToolUse spec gate (Windows / PowerShell 5.1).
# Thin adapter: parse the PreToolUse stdin JSON, then delegate the allow/deny
# decision to the shared policy module (checks/spec-gate-policy.ps1) so the local
# gate and the CI gate share one source of truth (SPEC F4). The decision logic
# itself lives in the policy module, not here.
# Registered via run-hook.sh dispatcher: sh run-hook.sh pre-tool-use-spec-gate
# Exit codes: 0 = allow, 2 = deny (stderr message is fed back to the model).
# Fail-open: any internal error allows the action and logs to .sdad/gate.log
# (a broken guard never freezes the developer). L-01: pure ASCII.

$ErrorActionPreference = "Stop"

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $json = $raw | ConvertFrom-Json
    $target = $json.tool_input.file_path
    if (-not $target) { exit 0 }

    $proj = $env:CLAUDE_PROJECT_DIR
    if (-not $proj) { $proj = (Get-Location).Path }

    # Locate the shared policy relative to this hook (.claude/hooks -> repo/checks),
    # not relative to the project dir (eval scenarios run the hook in a temp dir).
    $policy = Join-Path $PSScriptRoot '..\..\checks\spec-gate-policy.ps1'
    if (-not (Test-Path $policy)) { exit 0 }   # policy missing -> fail open

    $ErrorActionPreference = "Continue"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $policy -Path $target -ProjectDir $proj
    $code = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($null -eq $code) { exit 0 }
    exit $code
}
catch {
    # Fail-open path: allow the action, leave a trace
    try {
        $proj2 = $env:CLAUDE_PROJECT_DIR
        if (-not $proj2) { $proj2 = (Get-Location).Path }
        $logDir = Join-Path $proj2 '.sdad'
        if (-not (Test-Path $logDir)) {
            New-Item -ItemType Directory -Path $logDir -Force | Out-Null
        }
        $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        Add-Content -Path (Join-Path $logDir 'gate.log') -Encoding UTF8 -Value "$stamp WARN spec-gate failed open: $($_.Exception.Message)"
    } catch { }
    exit 0
}
