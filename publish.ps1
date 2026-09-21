# Rebuild the site and publish it. Run from the repo root:
#   .\publish.ps1
#   .\publish.ps1 "Fix the SPF figure caption"
#
# Vercel redeploys on every push to main, so this is the deploy step.

param([string]$Message = "")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Building public/ from content/state.json..." -ForegroundColor Cyan
python build.py
if ($LASTEXITCODE -ne 0) { throw "build.py failed. Nothing was committed." }

Write-Host "Regenerating editor.html..." -ForegroundColor Cyan
python make_editor.py
if ($LASTEXITCODE -ne 0) { throw "make_editor.py failed. Nothing was committed." }

$changes = git status --porcelain
if (-not $changes) {
    Write-Host "Nothing to publish. Working tree is clean." -ForegroundColor Yellow
    $ahead = git log --oneline "origin/main..HEAD"
    if ($ahead) {
        Write-Host "But there are unpushed commits. Pushing those." -ForegroundColor Cyan
        git push
    }
    exit 0
}

Write-Host ""
Write-Host "About to commit:" -ForegroundColor Cyan
git status --short
Write-Host ""

if (-not $Message) { $Message = Read-Host "Commit message" }
if (-not $Message) { throw "No commit message. Nothing was committed." }

git add -A
git commit -m $Message
git push

Write-Host ""
Write-Host "Pushed. Vercel is redeploying from main." -ForegroundColor Green
