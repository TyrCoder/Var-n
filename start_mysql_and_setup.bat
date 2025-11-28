@echo off
REM MySQL Server startup script for Windows

echo Checking for MySQL service...

REM Try common MySQL service names
for %%S in (MySQL80 MySQL57 MySQL56 MySQL MySQL8 MariaDB) do (
    sc query %%S >nul 2>&1
    if !errorlevel! equ 0 (
        echo Found service: %%S
        echo Starting %%S...
        net start %%S
        if !errorlevel! equ 0 (
            echo ✓ Service %%S started successfully
            timeout /t 3
            python setup_database.py
            exit /b 0
        )
    )
)

echo.
echo ERROR: MySQL service not found or could not be started
echo.
echo Please ensure MySQL Server is installed. To install MySQL:
echo 1. Download MySQL installer from https://dev.mysql.com/downloads/mysql/
echo 2. Run the installer
echo 3. Configure MySQL to run as a service
echo 4. Run this script again
echo.
pause
