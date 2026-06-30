@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未在 PATH 中找到 python，请先安装 Python 或将其加入环境变量。
    pause
    exit /b 1
)

python -m PyInstaller --onefile --windowed --name "OvConverter" --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module matplotlib --exclude-module numpy --exclude-module PIL --exclude-module scipy --exclude-module jinja2 --exclude-module lxml --exclude-module psutil --exclude-module sympy --exclude-module ezdxf main.py
if exist "dist\OvConverter.exe" (
    move /y "dist\OvConverter.exe" "dist\奥维数据格式转换.exe"
)
pause
