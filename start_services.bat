@echo off
REM ============================================================
REM  TRG - the two local services the original-game recorder needs.
REM
REM   8765  receive.py    sink / OUT - the injected script POSTs to
REM                       this; the bytes land in Data\ and never
REM                       travel through the AI's context.
REM   8766  http.server   files / IN - serves _tools\ so the executor
REM                       can HttpGet the recorder and the watcher.
REM
REM  Two windows on purpose: each keeps its own log, and closing one
REM  does not take the other down.
REM ============================================================

setlocal
REM %~dp0 is this file's own folder, so double-clicking works from
REM anywhere and --directory _tools still resolves.
cd /d "%~dp0"

REM The py launcher is the portable name; plain python is the fallback
REM on a machine that never installed it.
set "PY=py -3"
where py >nul 2>&1 || set "PY=python"

REM A second copy of a service does not fail loudly - the port is
REM already held, so the new window binds nothing and dies. Say so
REM before starting one, so a dead window is never mistaken for a
REM service that is up.
netstat -ano | findstr /r /c:":8765 .*LISTENING" >nul 2>&1 && (
    echo [warn] port 8765 is already LISTENING - a sink is probably up.
)
netstat -ano | findstr /r /c:":8766 .*LISTENING" >nul 2>&1 && (
    echo [warn] port 8766 is already LISTENING - a file server is probably up.
)

echo.
echo   sink  8765  =  http://127.0.0.1:8765/    writes into  Data\
echo   files 8766  =  http://127.0.0.1:8766/    serves      _tools\
echo.
echo   In the executor, with both windows up:
echo.
echo     loadstring(game:HttpGet('http://127.0.0.1:8766/TRG_original_recorder.luau'))()
echo.
echo   recorder hotkey  RightShift   = seal and end the run
echo   watcher hotkeys  RightAlt     = push the files now
echo                    RightControl = stop
echo.
echo   Close the two service windows to stop them. Closing THIS window
echo   leaves both of them running.
echo.

start "TRG sink 8765" cmd /k %PY% "%~dp0_tools\receive.py" --port 8765 --dir "%~dp0Data"
start "TRG files 8766" cmd /k %PY% -m http.server 8766 --bind 127.0.0.1 --directory "%~dp0_tools"

endlocal
