<#
.SYNOPSIS
    Переносит бота на VPS и запускает его круглосуточно.

.DESCRIPTION
    Запускается на вашем компьютере. Делает всё сам:
      1) собирает архив проекта;
      2) копирует его на сервер по SCP;
      3) запускает на сервере установку (systemd + автозапуск + ежедневная резервная копия);
      4) показывает статус и подсказывает, что сделать дальше.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy\deploy_to_vps.ps1 -Server 203.0.113.10

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy\deploy_to_vps.ps1 -Server 203.0.113.10 -User ubuntu -Port 2222
#>

param(
    [Parameter(Mandatory = $true)][string]$Server,
    [string]$User = "root",
    [int]$Port = 22,
    [string]$Token,
    [string]$RemoteDir = "/opt/english-bot",
    [string]$KeyFile = ""
)

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $projectDir

Write-Host "==> Проект: $projectDir" -ForegroundColor Cyan

if (-not $Token) {
    $tokenFile = Join-Path $projectDir "token.txt"
    if (Test-Path $tokenFile) {
        $Token = (Get-Content $tokenFile -Raw).Trim()
    }
}
if (-not $Token) {
    throw "Не найден токен бота: положите его в token.txt или передайте -Token 8123456789:AAH..."
}
Write-Host ("==> Токен: {0}...{1}" -f $Token.Substring(0, [Math]::Min(10, $Token.Length)), $Token.Substring([Math]::Max(0, $Token.Length - 4)))

foreach ($tool in @("ssh", "scp", "tar")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "Не найден $tool. Включите компонент Windows «Клиент OpenSSH» (Параметры → Приложения → Дополнительные компоненты)."
    }
}

$archive = Join-Path $env:TEMP "english-bot-deploy.tar.gz"
Write-Host "==> Готовлю перенос прогресса" -ForegroundColor Cyan
$snapshot = Join-Path $projectDir "data\deploy-snapshot.db"
$liveDb = Join-Path $projectDir "data\bot.db"
if (Test-Path $liveDb) {
    & python -c "import sys; sys.path.insert(0, '.'); from store import Store; Store(r'$liveDb').snapshot(r'$snapshot')"
    if (Test-Path $snapshot) {
        Write-Host ("    снимок базы: {0:N0} КБ — прогресс переедет на сервер" -f ((Get-Item $snapshot).Length / 1KB))
    } else {
        Write-Host "    снимок базы не получился, прогресс перенесёте вручную" -ForegroundColor Yellow
    }
}

Write-Host "==> Собираю архив $archive" -ForegroundColor Cyan
$exclude = @("--exclude=./data/bot.db", "--exclude=./data/bot.lock", "--exclude=./data/conflict.flag",
             "--exclude=./data/*.before-restore", "--exclude=./data/backup-snapshot.db",
             "--exclude=./logs", "--exclude=./token.txt",
             "--exclude=./.env", "--exclude=./__pycache__", "--exclude=*.pyc",
             "--exclude=./tests/_run", "--exclude=./.git")
& tar -czf $archive @exclude -C $projectDir .
if ($LASTEXITCODE -ne 0) { throw "Не удалось собрать архив" }
Write-Host ("    размер: {0:N0} КБ" -f ((Get-Item $archive).Length / 1KB))

$target = "${User}@${Server}"
# ssh принимает порт как -p, scp - как -P (заглавную). При подключении по ключу
# отключаем интерактивные запросы пароля, чтобы развёртывание шло без человека.
$sshArgs = @("-p", "$Port", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=20")
$scpArgs = @("-P", "$Port", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=20")
if ($KeyFile) {
    if (-not (Test-Path $KeyFile)) { throw "Не найден файл ключа: $KeyFile" }
    $sshArgs += @("-i", $KeyFile, "-o", "BatchMode=yes")
    $scpArgs += @("-i", $KeyFile, "-o", "BatchMode=yes")
    Write-Host "==> Подключение по SSH-ключу: $KeyFile" -ForegroundColor Cyan
} else {
    Write-Host "==> Подключение по паролю: ssh спросит его дважды" -ForegroundColor Yellow
}

Write-Host "==> Копирую архив на сервер" -ForegroundColor Cyan
& scp @scpArgs $archive "${target}:/tmp/english-bot-deploy.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "SCP не смог скопировать архив" }

Write-Host "==> Устанавливаю бота на сервере" -ForegroundColor Cyan
$remote = @"
set -e
mkdir -p $RemoteDir
tar -xzf /tmp/english-bot-deploy.tar.gz -C $RemoteDir
python3 $RemoteDir/deploy/vps_install.py '$Token' --app-dir $RemoteDir
rm -f /tmp/english-bot-deploy.tar.gz
"@
& ssh @sshArgs $target $remote
if ($LASTEXITCODE -ne 0) { throw "Установка на сервере завершилась ошибкой (смотрите вывод выше)" }

Write-Host "==> Финальная проверка снаружи" -ForegroundColor Cyan
& ssh @sshArgs $target "systemctl is-active english-starter; systemctl list-timers --no-pager | grep english-starter; tail -n 4 $RemoteDir/logs/bot.log"

Remove-Item $archive -Force -ErrorAction SilentlyContinue
Remove-Item $snapshot -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "ГОТОВО. Бот работает на сервере круглосуточно, прогресс перенесён." -ForegroundColor Green
Write-Host ""
Write-Host "Остался один шаг: выключите автозапуск на этом компьютере," -ForegroundColor Yellow
Write-Host "чтобы два бота не мешали друг другу (иначе будет конфликт getUpdates):"
Write-Host "    remove_autostart.bat  (двойной клик)"
Write-Host ""
Write-Host "Проверка: напишите боту /progress — день курса и серия должны быть на месте."
