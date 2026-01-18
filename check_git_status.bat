@echo off
REM Pre-Push Checklist for GitHub
REM Run this before pushing to verify everything is clean

echo ================================
echo GITHUB PRE-PUSH CHECKLIST
echo ================================
echo.

REM Check if we're in a git repo
git rev-parse --git-dir >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Not a git repository!
    exit /b 1
)

echo [1/8] Checking git status...
echo.
git status --short
echo.

echo [2/8] Checking for OUTPUT files (should NOT be staged)...
git ls-files | findstr /i "OUTPUT_" >nul
if %errorlevel% equ 0 (
    echo   [WARNING] OUTPUT files are tracked! They should be in .gitignore
    git ls-files | findstr /i "OUTPUT_"
) else (
    echo   [OK] No OUTPUT files tracked
)
echo.

echo [3/8] Checking for chunk folder (should NOT be staged)...
git ls-files | findstr /i "chunk/" >nul
if %errorlevel% equ 0 (
    echo   [WARNING] chunk/ folder is tracked! 9627 files would be committed!
    echo   Run: git rm -r --cached chunk/
) else (
    echo   [OK] chunk/ folder not tracked
)
echo.

echo [4/8] Checking CSV dataset situation...
git ls-files | findstr /E /C:"Disease and symptoms dataset.csv" >nul
if %errorlevel% equ 0 (
    echo   [ERROR] Uncompressed CSV is tracked! This will fail on GitHub (100MB limit)
    echo   Run: git rm --cached "Disease and symptoms dataset.csv"
) else (
    echo   [OK] Uncompressed CSV not tracked
)

git ls-files | findstr /C:"Disease and symptoms dataset.csv.gz" >nul
if %errorlevel% equ 0 (
    echo   [OK] Compressed CSV (.gz) is tracked (1.5MB)
) else (
    echo   [WARNING] Compressed CSV (.gz) is NOT tracked - you should add it!
    echo   Run: git add "Disease and symptoms dataset.csv.gz"
)
echo.

echo [5/8] Checking documentation files...
set DOC_COUNT=0
for %%f in (README.md DEPLOYMENT.md SYMPTOM_MATCHING.md DIAGNOSIS_GENERATION_FLOW.md) do (
    git ls-files | findstr /C:"%%f" >nul
    if %errorlevel% equ 0 (
        set /a DOC_COUNT+=1
    ) else (
        echo   [WARNING] %%f not tracked - should be committed!
    )
)
if %DOC_COUNT% geq 4 (
    echo   [OK] Documentation files tracked
)
echo.

echo [6/8] Checking for .env file (should NOT be staged)...
git ls-files | findstr /E /C:".env" >nul
if %errorlevel% equ 0 (
    echo   [ERROR] .env file is tracked! Contains API keys!
    echo   Run: git rm --cached .env
) else (
    echo   [OK] .env file not tracked
)

git ls-files | findstr /C:".env.example" >nul
if %errorlevel% equ 0 (
    echo   [OK] .env.example is tracked (safe)
) else (
    echo   [WARNING] .env.example not tracked - should be committed as template
)
echo.

echo [7/8] Checking file sizes for GitHub limits...
echo.
echo Files larger than 50MB (GitHub warning threshold):
for /f "delims=" %%f in ('git ls-files') do (
    for %%s in ("%%f") do (
        if %%~zs gtr 52428800 (
            set /a sizeMB=%%~zs/1024/1024
            echo   [WARNING] %%f is %%~zs bytes (^>50MB)
        )
    )
)
echo.

echo [8/8] Repository size summary...
echo.
for /f "tokens=1,2" %%a in ('git count-objects -vH') do (
    if "%%a"=="size:" echo   Repository size: %%b
    if "%%a"=="size-pack:" echo   Packed size: %%b
)
echo.

echo ================================
echo CHECKLIST COMPLETE
echo ================================
echo.
echo Next steps:
echo   1. Review the output above
echo   2. Fix any [ERROR] or [WARNING] issues
echo   3. Run: git add .
echo   4. Run: git commit -m "Your commit message"
echo   5. Run: git push origin main
echo.
echo See DEPLOYMENT.md for Railway deployment after push.
echo.
