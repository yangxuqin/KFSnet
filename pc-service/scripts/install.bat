@echo off
chcp 65001 >nul 2>&1

title BAT 控制服务 - 一键安装
echo ============================================
echo   BAT 任务 Web 控制服务 - 安装与配置
echo ============================================
echo.

:: 本脚本位于 pc-service\scripts\，服务根目录（含 app.py）为其上一级
for %%i in ("%~dp0..") do set "app_dir=%%~fi\"

:: 检查 Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [√] Python 已安装

:: 检查 pip
where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 pip
    pause
    exit /b 1
)
echo [√] pip 已安装

:: 安装依赖
echo.
echo [*] 正在安装依赖...
pip install -r "%app_dir%requirements.txt" --quiet
if %errorlevel% equ 0 (
    echo [√] 依赖安装成功
) else (
    echo [!] 依赖安装失败，尝试继续...
)

:: 创建示例 BAT 文件
echo.
set "example_bat=%~dp0example_task.bat"
if not exist "%example_bat%" (
    echo @echo off > "%example_bat%"
    echo echo 这是一个示例 BAT 任务 >> "%example_bat%"
    echo echo 按 Ctrl+C 可手动停止 >> "%example_bat%"
    echo timeout /t 3600 >> "%example_bat%"
    echo [√] 已创建示例 BAT 文件: scripts\example_task.bat
    echo     你可以替换为自己的 BAT 脚本
) else (
    echo [√] 示例 BAT 文件已存在
)

:: 提示配置
echo.
echo ============================================
echo   配置说明
echo ============================================
echo.
echo 请编辑 config.json 中的 bat_path，指向你的 BAT 脚本路径。
echo 首次运行 app.py 会自动生成 config.json。
echo 如需使用示例文件，请改为:
echo   "bat_path": "%~dp0example_task.bat"
echo 可选：在 config.json 中设置 "token" 可启用访问令牌认证。
echo.

:: 设置开机自启
echo ============================================
echo   是否设置开机自启？
echo ============================================
echo.
echo [推荐] 计划任务方式（无需用户登录，需管理员权限）:
echo    以管理员身份运行: KFS.exe install
echo.
echo 按 Y 设置「登录后自启」（将启动快捷方式放入启动文件夹）
echo 按其他键跳过
echo.
set /p choice=请选择 [Y/N]: 
if /i "%choice%"=="Y" (
    call :install_autostart
)

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 启动服务（有窗口调试）: python app.py
echo 启动服务（无窗口后台）: scripts\start_service.bat
echo.
pause
exit /b 0

:install_autostart
:: 创建 VBS 启动脚本（完全无窗口）
echo Set WshShell = CreateObject("WScript.Shell") > "%~dp0start_hidden.vbs"
echo WshShell.Run "pythonw.exe """ ^& chr(34) ^& "%app_dir%app.py" ^& chr(34), 0, False >> "%~dp0start_hidden.vbs"

:: 创建快捷方式到启动文件夹
set "startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "shortcut_path=%startup_folder%\BAT_Controller.lnk"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%shortcut_path%'); $sc.TargetPath = '%~dp0start_hidden.vbs'; $sc.WorkingDirectory = '%app_dir%'; $sc.Description = 'BAT Task Controller'; $sc.Save()"

if exist "%shortcut_path%" (
    echo [√] 开机自启已设置
    echo     快捷方式: %shortcut_path%
) else (
    echo [!] 设置开机自启失败，请手动将 start_hidden.vbs 放入启动文件夹
)
exit /b 0
