# Eval scenario 20 -- I6 usability sub-protocol: the pyplan-audit skill must
# contain the BR-12 contract text (convention-only path) and the no-app-access
# fixture manifest must declare App Access: false. Static content checks.
# Exit 0 = pass, 1 = fail. ASCII (L-01).
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$skill = Join-Path $repo ".claude\skills\pyplan-audit\SKILL.md"
$manifest = Join-Path $repo ".sdad\audit\_fixtures\no-app-access\manifest.md"

$fails = 0

if (-not (Test-Path $skill)) {
    Write-Host "  skill not found: $skill"; $fails++
} else {
    $text = Get-Content $skill -Raw -Encoding UTF8 | Out-String
    if ($text -notmatch "convention-only") {
        Write-Host "  skill missing 'convention-only' text (BR-12 contract)"; $fails++
    }
    if ($text -notmatch "live walkthrough not performed") {
        Write-Host "  skill missing 'live walkthrough not performed' text (BR-12 contract)"; $fails++
    }
    if ($text -notmatch "App Access") {
        Write-Host "  skill missing 'App Access' manifest field documentation"; $fails++
    }
}

if (-not (Test-Path $manifest)) {
    Write-Host "  fixture manifest not found: $manifest"; $fails++
} else {
    $mtext = Get-Content $manifest -Raw -Encoding UTF8 | Out-String
    if ($mtext -notmatch "App Access.*false") {
        Write-Host "  fixture manifest missing 'App Access: false' field"; $fails++
    }
    if ($mtext -notmatch "convention-only") {
        Write-Host "  fixture manifest missing 'convention-only' declaration"; $fails++
    }
}

if ($fails -eq 0) { Write-Host "PASS 20-audit-usability-no-app"; exit 0 }
Write-Host "FAIL 20-audit-usability-no-app ($fails subcases)"; exit 1
