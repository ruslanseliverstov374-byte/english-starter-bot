@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo   АВТОЗАПУСК БОТА 24/7 НА ЭТОМ КОМПЬЮТЕРЕ
echo ============================================================
echo.
echo Будет создано две задачи в планировщике Windows:
echo   1) EnglishStarterBot         - запуск бота при входе в систему
echo   2) EnglishStarterBotWatchdog - проверка каждые 5 минут: упал - поднять
echo.
echo Окно консоли не появляется, бот работает в фоне.
echo Бот работает, пока компьютер включён и вы вошли в систему.
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python не найден. Установите Python 3.9+ с https://python.org
    echo     При установке отметьте галочку "Add python.exe to PATH".
    pause
    exit /b 1
)

python tools\install_autostart.py
echo.
pause
