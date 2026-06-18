@echo off
setlocal

if "%~1"=="" (
    echo Usage: open_projector_browser.bat PROJECTOR_URL
    echo.
    echo Example:
    echo   open_projector_browser.bat http://192.168.1.50:8001/ABCD
    echo.
    echo Opens the projector in Chrome or Edge with autoplay enabled so teacher-
    echo triggered audio works without clicking the presenter screen.
    exit /b 1
)

set "URL=%~1"
set "FLAGS=--autoplay-policy=no-user-gesture-required --new-window"

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" %FLAGS% "%URL%"
    exit /b 0
)

if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" %FLAGS% "%URL%"
    exit /b 0
)

if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" %FLAGS% "%URL%"
    exit /b 0
)

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" %FLAGS% "%URL%"
    exit /b 0
)

if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" %FLAGS% "%URL%"
    exit /b 0
)

echo No Chrome or Edge installation found.
echo Install Google Chrome or Microsoft Edge, or create a desktop shortcut with:
echo   --autoplay-policy=no-user-gesture-required
exit /b 1