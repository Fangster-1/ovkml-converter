@echo off
cd /d "%~dp0"
D:\GD\arcgispro_clone\python.exe -m PyInstaller --onefile --windowed --name "奥维数据格式转换" --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module matplotlib --exclude-module numpy --exclude-module PIL --exclude-module scipy --exclude-module jinja2 --exclude-module lxml --exclude-module psutil --exclude-module sympy --exclude-module ezdxf main.py
pause
