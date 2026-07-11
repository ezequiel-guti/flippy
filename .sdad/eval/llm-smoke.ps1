# SDAD $eval -- LLM replay smoke (v5 I3, SPEC F3.2, resolves OD-1).
# Release gate ONLY (run via run-eval.ps1 -Release before tagging) -- never a
# daily gate: LLM output is non-deterministic, so matching is deliberately lax.
# Each scenario copies the methodology CLAUDE.md into a temp fixture, runs
# `claude --print "<prompt>"` there, and requires every regex to match
# (case-insensitive). Exit 0 = all scenarios pass. Pure ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..").Path
$timeoutSec = 300   # per call; generous -- a hung CLI must not hang the gate

# OD-1 resolution: wording + regex set, one row per smoke scenario.
# Audit behavioral scenarios added in v6 (B post-I10).
$scenarios = @(
    @{ name = "spec-language";  prompt = '$spec'
       # Fixture has no PROJECT_LANGUAGE -> the FIRST question must be the language one.
       patterns = @('(language|idioma)', '(English|Spanish|ingl|espa)') }
    @{ name = "build-gate";     prompt = '$build'
       # Fixture has no SPEC.md -> must redirect to $spec / $docfinal, never code.
       patterns = @('\$spec', '\$docfinal') }
    @{ name = "sdad-surface";   prompt = '$sdad'
       # Overview must surface the phase/command spine.
       patterns = @('spec', 'build', 'qa') }
    @{ name = "audit-surface";  prompt = '$audit'
       # $audit must open an evidence acquisition phase and mention dimensions.
       # Fixture has no SPEC.md -- $audit is allowlisted and must NOT be blocked.
       patterns = @('evidence|acqui', 'dimension|five|audit') }
    @{ name = "audit-not-assessable";
       prompt = 'I am running $audit on a Pyplan model. The model owner is not available and cannot provide the business objective. What happens to the business alignment dimension?'
       # Must declare not-assessable for alignment -- never fabricate.
       patterns = @('not assessable|not.{0,10}assess', 'alignment|business') }
    @{ name = "audit-domain-gap";
       prompt = 'I am running $audit on a Pyplan model whose business domain is maritime logistics. There is no domain profile for that domain in SDAD. What happens to the domain correctness dimension?'
       # Must declare not-assessable for domain -- never fabricate a profile.
       patterns = @('not assessable|not.{0,10}assess', 'domain|profile') }
)

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host "FAIL llm-smoke: claude CLI not found -- release gate cannot run"
    exit 1
}

$failed = 0
foreach ($s in $scenarios) {
    $tmp = Join-Path $env:TEMP ("sdad-llm-" + $s.name + "-$PID")
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    try {
        Copy-Item (Join-Path $repo "CLAUDE.md") (Join-Path $tmp "CLAUDE.md")

        # L-10: Start-Process cannot launch an npm CLI shim (.ps1) on Windows.
        # Use Start-Job instead -- child PowerShell process resolves shims natively.
        $job = Start-Job -ScriptBlock {
            param($dir, $prompt)
            Set-Location $dir
            & claude --print $prompt 2>&1
        } -ArgumentList $tmp, $s.prompt

        $finished = Wait-Job $job -Timeout $timeoutSec
        if (-not $finished) {
            Stop-Job $job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue
            Write-Host "FAIL llm:$($s.name) (timeout after $timeoutSec s)"
            $failed++
            continue
        }
        $output = Receive-Job $job
        Remove-Job $job -Force -ErrorAction SilentlyContinue
        $reply = if ($output) { ($output | ForEach-Object { "$_" }) -join "`n" } else { "" }
        $missing = @()
        foreach ($rx in $s.patterns) {
            if ($reply -notmatch "(?i)$rx") { $missing += $rx }
        }
        if ($missing.Count -eq 0) {
            Write-Host "PASS llm:$($s.name)"
        } else {
            Write-Host "FAIL llm:$($s.name) (no match: $($missing -join ', '))"
            $failed++
        }
    }
    finally {
        Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($failed -eq 0) { Write-Host "=== llm smoke: all pass ==="; exit 0 }
Write-Host "=== llm smoke: $failed failed ==="
exit 1
