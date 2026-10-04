@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   ПРОВЕРКА БОТА (контент + полный прогон 84 дней курса)
echo ============================================================
echo.
python bot.py --check
echo.
python tests\simulate.py
echo.
pause
