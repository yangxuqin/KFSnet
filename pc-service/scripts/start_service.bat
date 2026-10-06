@echo off
chcp 65001 >nul 2>&1
:: BAT 控制服务 - 无窗口启动脚本
:: 使用 pythonw.exe 启动，不显示任何命令行窗口
:: 双击此文件即可静默启动服务
:: 注意：本脚本位于 pc-service\scripts\，服务根目录（含 app.py）为其上一级

for %%i in ("%~dp0..") do set "app_dir=%%~fi\"
start "" pythonw.exe "%app_dir%app.py"
