# Daily local trigger for wpr-ai-digest (Windows Task Scheduler, 6:47am).
# 1. Refreshes skills-installed.json and commits it if it changed.
# 2. Fires today's edition(s) via `gh workflow run` so they start on time —
#    GitHub's own cron drifts by hours and stays only as a fallback; digest.py
#    skips a second real send on the same day, so a double trigger is harmless.
$ErrorActionPreference = "Continue"
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$logDir = Join-Path $env:LOCALAPPDATA "wpr-ai-digest"
New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir "local-run.log"
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath $log -Append }

Set-Location $repo
Log "start"
git pull --ff-only --quiet 2>&1 | Out-Null

python skills_inventory.py 2>&1 | ForEach-Object { Log $_ }
if (git status --porcelain skills-installed.json) {
    git add skills-installed.json
    git commit -q -m "skills inventory: $(Get-Date -Format yyyy-MM-dd)"
    git push -q
    Log "inventory changed -> committed and pushed"
} else {
    Log "inventory unchanged"
}

$byDay = @{ Monday = "digest-industry.yml"; Tuesday = "digest-ledgers.yml"; Wednesday = "digest-tools.yml";
            Thursday = "digest-skills.yml"; Friday = "digest.yml" }
$today = (Get-Date).DayOfWeek.ToString()
$runs = @()
if ($byDay.ContainsKey($today)) { $runs += $byDay[$today] }
if ((Get-Date).Day -eq 1) { $runs += "digest-grants.yml" }
foreach ($wf in $runs) {
    gh workflow run $wf --repo RowanFlynnPilot/wpr-ai-digest 2>&1 | ForEach-Object { Log $_ }
    Log "dispatched $wf"
}
if (-not $runs) { Log "nothing scheduled today" }
Log "done"
