@echo off
set "VLOG_DIR=%~dp0"
if "%VLOG_DIR:~0,2%"=="\\" (
    pushd "%VLOG_DIR%" 2>nul
    if errorlevel 1 (
        echo UNC path detected. Mounting temporary drive...
        for %%x in (Z Y X W V U T S R Q P O N M L K J I H G F E D C B A) do (
            if not exist %%x:\ (
                net use %%x: "%VLOG_DIR:~0,-1%" >nul 2>&1
                if not errorlevel 1 (
                    %%x:
                    goto :Run
                )
            )
        )
        echo Failed to mount network drive. Please run from a mapped drive.
        pause
        exit /b 1
    )
) else (
    cd /d "%VLOG_DIR%"
)

:Run
echo Starting VRChat Auto-Diary...
set "UV_PROJECT_ENVIRONMENT=.venv-win"
set "UV_LINK_MODE=copy"
uv run python -m src.main
pause
