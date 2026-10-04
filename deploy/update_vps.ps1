<#
.SYNOPSIS
    Обновляет бота на сервере (после правок кода или контента).

.DESCRIPTION
    Делает то же, что и первая установка, но безопасно: прогресс учеников не трогается,
    база остаётся на месте, сервис просто перезапускается с новым кодом.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy\update_vps.ps1 -Server 203.0.113.10
#>

param(
    [Parameter(Mandatory = $true)][string]$Server,
    [string]$User = "root",
    [int]$Port = 22,
    [string]$RemoteDir = "/opt/english-bot"
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $projectDir

$tokenFile = Join-Path $projectDir "token.txt"
if (-not (Test-Path $tokenFile)) { throw "Нет token.txt — нечего отправлять." }
$Token = (Get-Content $tokenFile -Raw).Trim()

$archive = Join-Path $env:TEMP "english-bot-update.tar.gz"
Write-Host "==> Собираю обновление" -ForegroundColor Cyan
$exclude = @("--exclude=./data", "--exclude=./logs", "--exclude=./token.txt",
             "--exclude=./.env", "--exclude=./__pycache__", "--exclude=*.pyc",
             "--exclude=./tests/_run", "--exclude=./.git")
& tar -czf $archive @exclude -C $projectDir .
if ($LASTEXITCODE -ne 0) { throw "Не удалось собрать архив" }

$target = "${User}@${Server}"
$sshArgs = @("-p", "$Port", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=20")

Write-Host "==> Копирую на сервер (спросит пароль)" -ForegroundColor Cyan
& scp @sshArgs $archive "${target}:/tmp/english-bot-update.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "SCP не смог скопировать архив" }

Write-Host "==> Устанавливаю обновление и перезапускаю" -ForegroundColor Cyan
$remote = @"
set -e
tar -xzf /tmp/english-bot-update.tar.gz -C $RemoteDir
python3 $RemoteDir/deploy/vps_install.py '$Token' --app-dir $RemoteDir
rm -f /tmp/english-bot-update.tar.gz
"@
& ssh @sshArgs $target $remote
if ($LASTEXITCODE -ne 0) { throw "Обновление завершилось ошибкой" }

Remove-Item $archive -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "ГОТОВО: код обновлён, бот перезапущен, прогресс не тронут." -ForegroundColor Green
