@echo off
setlocal EnableExtensions
title ComfyUI AssetSync - Maya Plugin Setup

set "SOURCE_ROOT=%~dp0..\.."
set "SOURCE_CORE=%SOURCE_ROOT%\assetsync"
set "SOURCE_PACKAGE=%~dp0MayaAssetSync"
set "SOURCE_LOADER=%~dp0MayaAssetSync_plugin.py"

if not exist "%SOURCE_CORE%\__init__.py" (
    echo [ERROR] AssetSync core was not found at "%SOURCE_CORE%".
    goto :failed
)
if not exist "%SOURCE_PACKAGE%\__init__.py" (
    echo [ERROR] MayaAssetSync package was not found.
    goto :failed
)

:ask_version
echo.
set "MAYA_VERSION="
set /p "MAYA_VERSION=Enter your Maya version, for example 2025: "
if not defined MAYA_VERSION goto :ask_version
set "INVALID_VERSION="
for /f "delims=0123456789" %%A in ("%MAYA_VERSION%") do set "INVALID_VERSION=%%A"
if defined INVALID_VERSION (
    echo [ERROR] Enter the four-digit Maya version only.
    goto :ask_version
)
if "%MAYA_VERSION:~3,1%"=="" goto :ask_version
if not "%MAYA_VERSION:~4,1%"=="" goto :ask_version

set "MAYA_INSTALL=%ProgramFiles%\Autodesk\Maya%MAYA_VERSION%"
if not exist "%MAYA_INSTALL%\bin\maya.exe" (
    echo Maya %MAYA_VERSION% was not found at "%MAYA_INSTALL%".
    set "MAYA_INSTALL="
    set /p "MAYA_INSTALL=Enter the full Maya installation folder: "
    if not exist "%MAYA_INSTALL%\bin\maya.exe" goto :failed
)

set "DOCUMENTS_DIR="
for /f "usebackq delims=" %%D in (`powershell.exe -NoProfile -Command "[Environment]::GetFolderPath('MyDocuments')"`) do set "DOCUMENTS_DIR=%%D"
if not defined DOCUMENTS_DIR set "DOCUMENTS_DIR=%USERPROFILE%\Documents"

set "MAYA_USER_DIR=%DOCUMENTS_DIR%\maya\%MAYA_VERSION%"
set "TARGET_CORE=%MAYA_USER_DIR%\scripts\assetsync"
set "TARGET_PACKAGE=%MAYA_USER_DIR%\scripts\MayaAssetSync"
set "TARGET_PLUGINS=%MAYA_USER_DIR%\plug-ins"

echo.
echo Installing AssetSync for Maya %MAYA_VERSION%...
if not exist "%TARGET_CORE%" mkdir "%TARGET_CORE%"
if not exist "%TARGET_PACKAGE%" mkdir "%TARGET_PACKAGE%"
if not exist "%TARGET_PLUGINS%" mkdir "%TARGET_PLUGINS%"
xcopy "%SOURCE_CORE%\*" "%TARGET_CORE%\" /E /I /Y /Q >nul
if errorlevel 1 goto :copy_failed
xcopy "%SOURCE_PACKAGE%\*" "%TARGET_PACKAGE%\" /E /I /Y /Q >nul
if errorlevel 1 goto :copy_failed
copy /Y "%SOURCE_LOADER%" "%TARGET_PLUGINS%\MayaAssetSync_plugin.py" >nul
if errorlevel 1 goto :copy_failed

echo [OK] AssetSync was installed successfully.
echo.
echo Finish in Maya:
echo   1. Restart Maya.
echo   2. Open Windows ^> Settings/Preferences ^> Plug-in Manager.
echo   3. Enable Loaded and Auto load for MayaAssetSync_plugin.py.
echo The receiver will then start automatically on port 18952.
echo.
pause
exit /b 0

:copy_failed
echo [ERROR] Files could not be copied. Check folder permissions.
:failed
echo [ERROR] AssetSync Maya installation did not complete.
pause
exit /b 1

