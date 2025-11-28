@echo off
echo ========================================
echo XAMPP MySQL COMPLETE FIX
echo ========================================
echo.
echo Fixing Aria log and mysql.plugin issues...
echo.

:: Stop MySQL completely
echo [Step 1] Stopping MySQL...
net stop mysql 2>nul
taskkill /F /IM mysqld.exe 2>nul
timeout /t 3 /nobreak >nul

:: Navigate to MySQL data directory
cd /d C:\xampp\mysql\data

:: Fix Aria log files
echo.
echo [Step 2] Fixing Aria storage engine...
if exist aria_log.00000001 del /F /Q aria_log.00000001
if exist aria_log.00000002 del /F /Q aria_log.00000002
if exist aria_log_control del /F /Q aria_log_control

:: Create new aria log control file
echo. > aria_log_control

:: Fix mysql database
echo.
echo [Step 3] Repairing mysql system database...
cd /d C:\xampp\mysql\bin

:: Start MySQL in recovery mode temporarily
echo Starting MySQL in safe mode...
start /B mysqld.exe --defaults-file=..\bin\my.ini --console --skip-grant-tables --skip-networking
timeout /t 5 /nobreak >nul

:: Run repair
echo Running repair...
mysql -u root --skip-password -e "USE mysql; SET GLOBAL innodb_fast_shutdown = 0;" 2>nul
mysql -u root --skip-password mysql < ..\share\mysql_system_tables_fix.sql 2>nul

:: Stop safe mode MySQL
taskkill /F /IM mysqld.exe 2>nul
timeout /t 2 /nobreak >nul

:: Start MySQL normally
echo.
echo [Step 4] Starting MySQL normally...
start "" mysqld.exe --defaults-file=..\bin\my.ini --standalone --console

timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo DONE! Check XAMPP Control Panel now.
echo If MySQL is green, the fix worked!
echo ========================================
echo.
pause
