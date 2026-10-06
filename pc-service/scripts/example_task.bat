@echo off
chcp 65001 >nul 2>&1
:: 这是示例 BAT 任务文件
:: 你可以替换为自己的 BAT 脚本
:: 然后修改 app.py 中的 BAT_PATH 指向你的脚本

echo ====================================
echo   示例 BAT 任务正在运行...
echo   按 Ctrl+C 可手动停止
echo ====================================
echo.

:: 模拟一个长时间运行的任务
:: 替换为你自己的命令
for /l %%i in (1,100) do (
    echo [%%i/100] 任务执行中... %date% %time%
    timeout /t 30 >nul
)

echo.
echo 任务完成！
pause
