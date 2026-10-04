@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   СНЯТЬ АВТОЗАПУСК И ОСТАНОВИТЬ БОТА
echo ============================================================
echo.
echo ВАЖНО: сделайте это перед запуском бота в облаке (VPS),
echo иначе два экземпляра будут мешать друг другу.
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python не найден в PATH.
    pause
    exit /b 1
)

python tools\remove_autostart.py
echo.
echo Готово. Запустить снова вручную: run.bat
echo Включить автозапуск снова: install_autostart.bat
pause
