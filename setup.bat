@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo   ENGLISH STARTER - установка за одну минуту
echo ============================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python не найден в PATH.
    echo     Установите Python 3.9+ с https://python.org и запустите файл снова.
    echo     При установке отметьте галочку "Add python.exe to PATH".
    pause
    exit /b 1
)

if exist token.txt (
    echo Найден сохранённый токен в token.txt
    set /p REPLACE=Заменить его? (y/N): 
    if /i not "!REPLACE!"=="y" goto :run
)

echo.
echo Шаг 1. Откройте Telegram и найдите бота @BotFather
echo Шаг 2. Отправьте ему команду /newbot
echo Шаг 3. Придумайте имя (например, My English Starter)
echo Шаг 4. Скопируйте токен вида 8123456789:AAH... и вставьте ниже
echo.
set /p TOKEN=Токен бота: 
if "!TOKEN!"=="" (
    echo [!] Токен не введён - выходим.
    pause
    exit /b 1
)
(echo !TOKEN!)>token.txt
echo.
echo [+] Токен сохранён в token.txt

:run
echo.
echo Проверка бота...
python bot.py --check
if errorlevel 1 (
    echo [!] Проверка контента не прошла - напишите об этом разработчику.
    pause
    exit /b 1
)
echo.
echo Запускаю бота. Не закрывайте это окно, пока хотите, чтобы бот работал.
echo Остановить бота: Ctrl+C
echo.
python bot.py
echo.
echo Бот остановлен.
pause
