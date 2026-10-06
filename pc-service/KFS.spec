# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置 - BAT 任务 Web 控制服务
# 用法（在 pc-service 目录下执行）:
#   py -m PyInstaller KFS.spec
# 产物: dist/KFS.exe（单文件，含控制台以支持子命令交互）

import os

BASE = os.path.abspath('.')

a = Analysis(
    ['app.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        # 打包 templates 目录，运行时解压到 _MEIPASS/templates
        ('templates', 'templates'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KFS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # 保留控制台窗口：install/uninstall/status 子命令需要输出；
    # 服务在计划任务中以 SYSTEM 身份运行时本就无桌面窗口。
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
