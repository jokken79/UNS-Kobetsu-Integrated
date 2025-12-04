@echo off
chcp 65001 >nul
echo ========================================
echo Import ALL Employees from Excel
echo ========================================
echo.

REM Find the Excel file in D:\
set "EXCEL_FILE="
for %%f in (D:\*.xlsm) do (
    set "EXCEL_FILE=%%f"
    echo Found Excel file: %%f
    goto :found
)

:found
if "%EXCEL_FILE%"=="" (
    echo ERROR: No Excel file found in D:\
    pause
    exit /b 1
)

echo.
echo Step 1: Copying Excel file to Docker container...
docker cp "%EXCEL_FILE%" uns-kobetsu-backend:/tmp/all_employees.xlsm
if errorlevel 1 (
    echo ERROR: Failed to copy file to container
    pause
    exit /b 1
)
echo ✓ File copied successfully

echo.
echo Step 2: Importing ALL employees...
echo.
docker exec uns-kobetsu-backend python scripts/import_all_employees.py --file /tmp/all_employees.xlsm --sheet DBGenzaiX

echo.
echo ========================================
echo Import Complete!
echo ========================================
echo.
echo Check the output above for summary.
echo You can also check: http://localhost:3010/employees
echo.
pause
