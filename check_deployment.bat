@echo off
REM Deployment Pre-Flight Check
REM Verifies dataset files are configured correctly for GitHub/Railway deployment

echo ================================
echo DEPLOYMENT PRE-FLIGHT CHECK
echo ================================
echo.

REM Check if files exist
echo [1/4] Checking if dataset files exist...
if exist "Disease and symptoms dataset.csv" (
    echo   [OK] Disease and symptoms dataset.csv exists
) else (
    echo   [ERROR] Disease and symptoms dataset.csv NOT FOUND
    echo   Run scripts\decompress_csv.py first!
    exit /b 1
)

if exist "Disease and symptoms dataset.csv.gz" (
    echo   [OK] Disease and symptoms dataset.csv.gz exists
) else (
    echo   [ERROR] Disease and symptoms dataset.csv.gz NOT FOUND
    echo   Run scripts\compress_csv.py first!
    exit /b 1
)
echo.

REM Check .gitignore
echo [2/4] Checking .gitignore configuration...
findstr /C:"Disease and symptoms dataset.csv" .gitignore >nul
if %errorlevel% equ 0 (
    echo   [OK] .gitignore configured to exclude uncompressed CSV
) else (
    echo   [WARNING] .gitignore may not exclude uncompressed CSV
)
echo.

REM Check git tracking status
echo [3/4] Checking git tracking status...
git ls-files | findstr /C:"Disease and symptoms dataset.csv.gz" >nul
if %errorlevel% equ 0 (
    echo   [OK] Compressed CSV (.gz) is tracked by git
) else (
    echo   [INFO] Compressed CSV is NOT yet tracked (will be on first commit)
)

git ls-files | findstr /E /C:"Disease and symptoms dataset.csv" >nul
if %errorlevel% equ 0 (
    echo   [ERROR] Uncompressed CSV (.csv) is tracked by git - THIS WILL FAIL!
    echo   Fix: git rm --cached "Disease and symptoms dataset.csv"
) else (
    echo   [OK] Uncompressed CSV is NOT tracked (correct)
)
echo.

REM Check file sizes
echo [4/4] Checking file sizes...
for %%A in ("Disease and symptoms dataset.csv") do (
    set size=%%~zA
    set /a sizeMB=%%~zA/1024/1024
    echo   Uncompressed: %%~zA bytes ^(~!sizeMB!MB^)
    if %%~zA GTR 104857600 (
        echo   [CRITICAL] Exceeds GitHub's 100MB limit - MUST NOT be committed!
    )
)

for %%A in ("Disease and symptoms dataset.csv.gz") do (
    set size=%%~zA
    set /a sizeMB=%%~zA/1024/1024
    echo   Compressed: %%~zA bytes ^(~!sizeMB!MB^)
    if %%~zA LSS 10485760 (
        echo   [OK] Under GitHub's 100MB limit
    )
)
echo.

echo ================================
echo DEPLOYMENT READY!
echo ================================
echo.
echo Next steps:
echo   1. git add .
echo   2. git commit -m "Add compressed dataset for Railway"
echo   3. git push origin main
echo   4. Deploy to Railway.io
echo.
echo On Railway startup, the CSV will be automatically decompressed.
echo See DEPLOYMENT.md for details.
echo.
