@echo off
echo ========================================
echo XAMPP MySQL Recovery Script
echo ========================================
echo.

:: Stop MySQL if running
echo [1/5] Stopping MySQL service...
net stop mysql 2>nul
taskkill /F /IM mysqld.exe 2>nul
timeout /t 2 /nobreak >nul

:: Backup current data
echo.
echo [2/5] Backing up current MySQL data...
set BACKUP_DIR=C:\xampp\mysql\backup_%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if exist "C:\xampp\mysql\data\ib_logfile0" (
    echo Backing up log files...
    copy "C:\xampp\mysql\data\ib_logfile0" "%BACKUP_DIR%\" >nul 2>&1
    copy "C:\xampp\mysql\data\ib_logfile1" "%BACKUP_DIR%\" >nul 2>&1
    echo Backup created in: %BACKUP_DIR%
)

:: Remove corrupted log files
echo.
echo [3/5] Removing potentially corrupted log files...
if exist "C:\xampp\mysql\data\ib_logfile0" del /F /Q "C:\xampp\mysql\data\ib_logfile0"
if exist "C:\xampp\mysql\data\ib_logfile1" del /F /Q "C:\xampp\mysql\data\ib_logfile1"
if exist "C:\xampp\mysql\data\ibdata1" (
    echo Note: ibdata1 exists - keeping it
) else (
    echo WARNING: ibdata1 missing!
)

:: Remove lock files
echo.
echo [4/5] Removing lock files...
if exist "C:\xampp\mysql\data\*.err" del /F /Q "C:\xampp\mysql\data\*.err"
if exist "C:\xampp\mysql\data\*.pid" del /F /Q "C:\xampp\mysql\data\*.pid"

:: Start MySQL
echo.
echo [5/5] Starting MySQL...
cd /d C:\xampp\mysql\bin
start "" mysqld.exe --defaults-file=C:\xampp\mysql\bin\my.ini --standalone --console

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Recovery process completed!
echo.
echo Please check XAMPP Control Panel
echo If MySQL shows green, the fix worked!
echo ========================================
echo.
pause
