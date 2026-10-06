@echo off
chcp 65001 >nul 2>&1
:: BAT 控制服务 - 卸载脚本
:: 删除开机自启快捷方式并停止服务

echo 正在停止 BAT 控制服务...

:: 停止 pythonw.exe 中运行的服务
taskkill /F /FI "WINDOWTITLE eq BAT*" >nul 2>&1

:: 删除启动文件夹中的快捷方式
set "shortcut_path=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\BAT_Controller.lnk"
if exist "%shortcut_path%" (
    del "%shortcut_path%"
    echo [√] 已删除开机自启快捷方式
) else (
    echo [!] 未找到开机自启快捷方式
)

echo.
echo 卸载完成。
pause
