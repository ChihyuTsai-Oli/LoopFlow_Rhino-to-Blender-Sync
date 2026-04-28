@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   LoopFlow Rhino-to-Blender Installer
echo ============================================================
echo.

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
set "SRC_PY=%ROOT_DIR%\LoopFlow_Rhino-to-Blender-Sync"
set "DST_ROOT=%APPDATA%\McNeel\Rhinoceros\8.0\scripts\LoopFlow_R2B"
set "DST_PY=%DST_ROOT%\Py"

rem -- Check source folder exists and has files --
if not exist "%SRC_PY%\" (
    echo [ERROR] Cannot find source folder:
    echo         %SRC_PY%\
    echo.
    echo         Expected layout after unzip:
    echo           install_LoopFlow_R2B.bat
    echo           LoopFlow_Rhino-to-Blender-Sync\LiveLink_R2B_*.py
    echo.
    goto :END_FAIL
)

set "SRC_COUNT=0"
for %%F in ("%SRC_PY%\*") do set /a SRC_COUNT+=1
if %SRC_COUNT%==0 (
    echo [ERROR] No files found in:
    echo         %SRC_PY%\
    echo.
    goto :END_FAIL
)

rem -- Check Rhino 8.0 AppData root exists --
if not exist "%APPDATA%\McNeel\Rhinoceros\8.0\" (
    echo [ERROR] Rhino 8.0 settings folder not found:
    echo         %APPDATA%\McNeel\Rhinoceros\8.0\
    echo.
    echo         Please make sure Rhino 8.0 is installed and has been
    echo         launched at least once before running this installer.
    echo.
    goto :END_FAIL
)
echo [1/3] Rhino 8.0 settings folder ... OK

rem -- Remove old version and create fresh target folder --
if exist "%DST_PY%\" (
    echo [2/3] Removing old version...
    rmdir /s /q "%DST_PY%"
)
mkdir "%DST_PY%"
if errorlevel 1 (
    echo [ERROR] Failed to create target folder:
    echo         %DST_PY%
    goto :END_FAIL
)
echo [2/3] Target folder ready: %DST_PY%

rem -- Copy all scripts --
echo [3/3] Copying scripts...
echo.

robocopy "%SRC_PY%" "%DST_PY%" /NJH /NJS /NDL /NP
if errorlevel 8 (
    echo [ERROR] robocopy failed ^(exit code ^>= 8^).
    goto :END_FAIL
)

set "DST_COUNT=0"
for %%F in ("%DST_PY%\*") do set /a DST_COUNT+=1
echo   Source : %SRC_PY%
echo   Target : %DST_PY%
echo   Copied : !DST_COUNT! of !SRC_COUNT! files
echo.

rem -- Locate .rhc in the root folder (same level as this BAT) --
set "RHC_FILE="
for %%F in ("%ROOT_DIR%\*.rhc") do set "RHC_FILE=%%F"

rem -- Success popup --
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('!DST_COUNT! scripts copied to Rhino scripts folder.' + [char]10 + [char]10 + 'NEXT STEP:' + [char]10 + '  1. Open Rhino 8' + [char]10 + '  2. Drag LoopFlow_R2B.rhc (next to this installer) into any Rhino viewport' + [char]10 + '  3. The LoopFlow R2B toolbar will appear', 'LoopFlow R2B Installer', [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)"

echo ============================================================
echo   Installation complete.
echo ============================================================
echo.
pause
exit /b 0

:END_FAIL
echo.
echo ============================================================
echo   Installation failed. See messages above.
echo ============================================================
echo.
pause
exit /b 1
