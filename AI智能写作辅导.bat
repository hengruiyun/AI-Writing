@echo off
cd writing-assistant

chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo AI智能写作辅导软件
echo ========================================
echo.

rem Check if Python 3.10+ is available
echo [1/5] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo  Python not found in PATH
    goto :setup_venv
)

rem Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python version: %PYTHON_VERSION%

rem Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

rem Check if version is 3.10 or higher
if %MAJOR% LSS 3 goto :setup_venv
if %MAJOR% EQU 3 if %MINOR% LSS 10 goto :setup_venv

echo  Python %PYTHON_VERSION% meets requirements (3.10+)
goto :check_venv

:setup_venv
echo [2/5] Setting up Python 3.10 virtual environment...
if not exist "uv.exe" (
    echo  uv.exe not found in current directory
    echo Please ensure uv.exe is available
    pause
    exit /b 1
)

echo Creating virtual environment with Python 3.10...
uv.exe venv --python=3.10
if errorlevel 1 (
    echo  Failed to create virtual environment
    pause
    exit /b 1
)
echo  Virtual environment created successfully
goto :install_deps

:check_venv
echo [2/5] Checking virtual environment...
if exist ".venv" (
    echo  Virtual environment already exists
) else (
    echo Creating virtual environment...
    if not exist "uv.exe" (
        echo  uv.exe not found in current directory
        pause
        exit /b 1
    )
    uv.exe venv --python=3.10
    if errorlevel 1 (
        echo  Failed to create virtual environment
        pause
        exit /b 1
    )
    echo  Virtual environment created successfully
)

:install_deps
echo [3/5] Installing dependencies...
if not exist "requirements.txt" (
    echo  requirements.txt not found
    pause
    exit /b 1
)

echo Installing packages from requirements.txt...
uv.exe pip install -r requirements.txt
if errorlevel 1 (
    echo  Failed to install dependencies
    pause
    exit /b 1
)
echo  Dependencies installed successfully

:rename_pyproject
echo [4/5] Checking pyproject.toml...
if exist "pyproject.toml" (
    echo Renaming pyproject.toml to pyproject-old.toml...
    ren "pyproject.toml" "pyproject-old.toml"
    if errorlevel 1 (
        echo  Failed to rename pyproject.toml
        pause
        exit /b 1
    )
    echo  pyproject.toml renamed to pyproject-old.toml
) else (
    echo   pyproject.toml not found, skipping rename
)



echo Checking Ollama installation...

REM Check if Ollama is in PATH
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo Ollama found in PATH.
    echo Current Ollama location:
    where ollama
    goto :endOllamaSetup
)

echo Ollama not found in PATH.
echo Adding Ollama to PATH...

REM Define Ollama installation path
set "OLLAMA_PATH=%userprofile%\AppData\Local\Programs\Ollama"

REM Check if Ollama directory exists
if not exist "%OLLAMA_PATH%" (
    echo Error: Ollama directory not found at %OLLAMA_PATH%
    echo Please install Ollama first.
    pause
    goto :endOllamaSetup
)

REM Check if Ollama executable exists
if not exist "%OLLAMA_PATH%\ollama.exe" (
    echo Error: ollama.exe not found in %OLLAMA_PATH%
    echo Please check your Ollama installation.
    pause
    goto :endOllamaSetup
)

REM Get current PATH
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"

REM Check if Ollama path is already in PATH
echo %CURRENT_PATH% | findstr /i "%OLLAMA_PATH%" >nul
if %errorlevel% equ 0 (
    echo Ollama path already exists in PATH.
    goto :endOllamaSetup
)

REM Add Ollama to PATH
if defined CURRENT_PATH (
    set "NEW_PATH=%CURRENT_PATH%;%OLLAMA_PATH%"
) else (
    set "NEW_PATH=%OLLAMA_PATH%"
)

Set PATH=%PATH%;%OLLAMA_PATH%

REM Update PATH in registry
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul
if %errorlevel% equ 0 (
    echo Successfully added Ollama to PATH.
    echo New PATH: %NEW_PATH%
    echo Please restart your command prompt or reboot to apply changes.
) else (
    echo Error: Failed to update PATH.
    echo Please run this script as administrator.
)

:endOllamaSetup

uv run check_ollama_env.py qwen3:0.6b


echo [INFO] 正在停止AI 智能写作辅助系统...

:: 终止Python进程
taskkill /f /im python.exe /fi "WINDOWTITLE eq AI 智能写作辅助系统*" >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] 已终止Python进程
) else (
    echo [INFO] 未找到运行中的Python进程
)

:: 终止可能的Flask进程
taskkill /f /im python.exe /fi "IMAGENAME eq python.exe" >nul 2>&1

:: 检查端口是否还被占用
echo [INFO] 检查端口状态...
netstat -an | findstr ":8080" >nul
if %errorLevel% == 0 (
    echo [WARN] 端口8080仍被占用，可能有其他进程在使用
    echo [INFO] 请手动检查并终止相关进程
) else (
    echo [INFO] 端口8080已释放
)


:launch_gui
echo [5/5] Launching GUI application...
if not exist "app.py" (
    echo  app.py not found
    pause
    exit /b 1
)


:: 启动浏览器（延迟5秒）
start /b cmd /c "timeout /t 5 >nul && start http://localhost:8080"


echo Starting AI Stock Analysis Software...
echo.

rem Activate virtual environment and run the GUI
if exist ".venv\Scripts\python.exe" (
    uv run app.py
) else (
    python app.py
)

if errorlevel 1 (
    echo  Application failed to start
    pause
    exit /b 1
)

cd ..
echo.
echo  Application completed successfully
pause