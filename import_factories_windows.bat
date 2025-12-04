@echo off
REM ============================================
REM Import All Factories from Windows Directory
REM ============================================

echo.
echo ==========================================
echo   Import All Factory JSON Files
echo ==========================================
echo.

set FACTORIES_DIR=E:\config\factories

if not exist "%FACTORIES_DIR%" (
    echo ERROR: Directory not found: %FACTORIES_DIR%
    pause
    exit /b 1
)

echo Source: %FACTORIES_DIR%
echo.
echo Copying files to Docker container...
docker cp "%FACTORIES_DIR%" uns-kobetsu-backend:/tmp/import_factories

echo.
echo Running import script...
docker exec uns-kobetsu-backend python /app/scripts/import_factories_directory.py --dir /tmp/import_factories

echo.
echo ==========================================
echo   Import Complete!
echo ==========================================
echo.
pause
