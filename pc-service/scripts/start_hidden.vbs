' BAT 任务 Web 控制服务 - 静默启动脚本
' 以完全无窗口的方式后台启动服务（pythonw.exe）
' 可双击运行，也可将其快捷方式放入系统「启动」文件夹实现登录自启
Option Explicit

Dim fso, shell, scriptDir, appPath

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' 本脚本位于 pc-service\scripts\，服务根目录（含 app.py）为其上一级
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
appPath = fso.GetAbsolutePathName(fso.BuildPath(scriptDir, "..\app.py"))

If Not fso.FileExists(appPath) Then
    MsgBox "未找到 app.py: " & appPath, 16, "BAT 控制服务"
    WScript.Quit 1
End If

shell.Run "pythonw.exe """ & appPath & """", 0, False
