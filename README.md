# KFSnet · BAT 任务 Web 控制服务

> 在局域网内通过浏览器或手机 App 远程启动 / 停止 Windows 上的 BAT 脚本。
> 支持打包为**单文件 EXE**，并可注册为**计划任务开机自启（无需用户登录）**。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB.svg)

---

## 特性

- **网页控制台** — 深色主题控制面板，实时轮询任务状态，显示运行 PID
- **手机 App** — 安卓 WebView 壳应用，可配置服务器地址与访问令牌
- **进程树管理** — 停止任务时用 `taskkill /T` 结束整个进程树，不留残余子进程
- **单文件 EXE** — PyInstaller 打包，目标机器无需安装 Python，已内嵌 Flask 与页面模板
- **命令行子命令** — `run` / `install` / `uninstall` / `status`
- **免登录自启** — 注册为计划任务，以 `SYSTEM` 账户在系统启动时运行
- **配置外置** — 所有参数集中在 `config.json`，无需修改源码
- **可选令牌认证** — 设置 `token` 后 API 需携带 `X-Auth-Token`，防止局域网内任意控制
- **日志落盘** — 无窗口运行时的日志仍完整写入 `service.log`

---

## 目录结构

```
KFSnet/
├── pc-service/                  # 电脑端 Flask 服务
│   ├── app.py                   # 主程序（含 run/install/uninstall/status 子命令）
│   ├── KFS.spec                 # PyInstaller 打包配置
│   ├── requirements.txt         # Python 依赖
│   ├── config.example.json      # 配置模板（config.json 首次运行自动生成）
│   ├── templates/
│   │   └── index.html           # 网页控制面板
│   └── scripts/                 # Windows 辅助脚本
│       ├── install.bat          # 一键安装（装依赖 / 建示例 / 设自启）
│       ├── uninstall.bat        # 卸载（删除自启快捷方式）
│       ├── start_service.bat    # 无窗口启动
│       ├── start_hidden.vbs     # VBS 静默启动（可放入启动文件夹）
│       └── example_task.bat     # 生成的示例任务
│
├── android-app/                 # 安卓控制 App（Gradle 工程）
│   ├── app/src/main/java/com/batcontroller/MainActivity.java
│   ├── app/src/main/res/layout/activity_main.xml
│   ├── app/src/main/AndroidManifest.xml
│   ├── app/build.gradle
│   ├── build.gradle
│   ├── settings.gradle
│   └── gradle.properties
│
├── examples/
│   └── kfs.bat                  # 示例目标任务脚本
│
├── LICENSE                      # MIT
├── README.md
└── AGENTS.md                    # 面向 AI 协作者的项目说明
```

---

## 快速开始

### 方式一：源码运行

```bash
cd pc-service

# 1. 安装依赖
pip install -r requirements.txt

# 2. 首次运行，自动生成 config.json
python app.py
```

编辑 `pc-service/config.json`，把 `bat_path` 指向你的 BAT 脚本：

```json
{
    "bat_path": "D:\\your\\path\\task.bat"
}
```

重新启动后用浏览器访问 `http://电脑IP:8010` 即可。

> 想先试跑？把 `bat_path` 指向仓库自带的 `examples/kfs.bat`。

### 方式二：单文件 EXE（推荐）

```bash
cd pc-service
pip install pyinstaller
py -m PyInstaller KFS.spec --noconfirm
```

产物为 `pc-service/dist/KFS.exe`（约 11 MB，单文件）。
把它拷到任意目录，**目标机器无需安装 Python**，首次运行会在同目录生成 `config.json`。

---

## 配置文件 config.json

与 `app.py`（源码方式）或 `KFS.exe`（打包方式）**同目录**，首次运行自动生成。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `bat_path` | string | `examples/kfs.bat` | 目标 BAT 脚本完整路径，**必改** |
| `host` | string | `0.0.0.0` | 监听地址，`0.0.0.0` 允许局域网访问，`127.0.0.1` 仅本机 |
| `port` | int | `8010` | 服务端口 |
| `token` | string | `""` | 访问令牌，留空则不启用认证 |
| `log_file` | string | `""` | 日志路径，留空则用同目录 `service.log` |
| `task_name` | string | `KFSnetService` | 注册的计划任务名称 |

> `config.json` 含本机路径，已被 `.gitignore` 排除，不会提交到仓库。

---

## EXE 子命令

| 命令 | 说明 |
|------|------|
| `KFS.exe` / `KFS.exe run` | 前台运行服务 |
| `KFS.exe install` | 注册为计划任务（开机自启，**无需用户登录**）· 需管理员权限 |
| `KFS.exe uninstall` | 移除计划任务 |
| `KFS.exe status` | 查看计划任务状态 |
| `KFS.exe --help` | 查看帮助 |

```bash
KFS.exe                 # 前台运行服务
KFS.exe run             # 同上
KFS.exe install         # 注册开机自启（管理员）
KFS.exe status          # 查询计划任务
KFS.exe uninstall       # 移除计划任务
```

---

## 开机自启

### 方式一：计划任务（推荐，支持未登录自启）

```bash
# 以管理员身份打开命令提示符
KFS.exe install
```

原理：`schtasks /create /sc ONSTART /ru SYSTEM /rl HIGHEST`
→ 系统启动时以 `SYSTEM` 账户运行，**无需用户登录**，开机即可用手机连接控制。

### 方式二：启动文件夹（登录后自启）

- 运行 `pc-service/scripts/install.bat`，按 `Y` 将 `start_hidden.vbs` 的快捷方式放入启动文件夹
- 或手动：`Win + R` → `shell:startup` → 放入 `start_hidden.vbs` 快捷方式

### 卸载

```bash
KFS.exe uninstall                    # 移除计划任务（管理员）
pc-service\scripts\uninstall.bat     # 删除启动文件夹快捷方式
```

---

## HTTP API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 网页控制面板 |
| `/api/status` | GET | 获取任务运行状态 |
| `/api/start` | POST | 启动任务 |
| `/api/stop` | POST | 停止任务 |

**状态返回示例**

```json
{ "running": true, "bat_name": "kfs.bat", "pid": 12345 }
```

**认证**：若 `config.json` 中配置了 `token`，所有 `/api/*` 请求需携带
请求头 `X-Auth-Token: 你的令牌`（或 URL 参数 `?token=你的令牌`），否则返回 `401`。
网页控制面板会自动弹出输入框提示令牌。

---

## 安卓 App

用 Android Studio 打开 `android-app` 目录，Build → Build APK(s)。
产物位于 `android-app/app/build/outputs/apk/release/app-release.apk`。

> ⚠️ 当前仓库**未包含 Gradle Wrapper**（`gradlew` / `gradle/wrapper/`）。
> 请在 Android Studio 中同步一次（会自动生成），或执行 `gradle wrapper --gradle-version 7.5.1`。

**App 使用**

1. 安装 APK 到手机，与电脑处于**同一局域网**
2. 打开 App，点右上角设置，填入 `电脑IP:8010`
3. 若服务端配置了 `token`，在同一对话框填入令牌
4. 即可远程启动 / 停止任务

**注意事项**
- 电脑防火墙需放行 8010 端口
- App 已启用 `usesCleartextTraffic`，支持局域网 HTTP 明文连接

---

## 安全提示

- 服务默认**无认证**，局域网内任何人都能控制任务。建议在 `config.json` 中设置 `token`。
- 服务**默认关闭 Flask debug 模式**（`debug=False`）。请勿在局域网暴露的地址上开启 debug，
  Werkzeug 调试器可被远程利用执行任意代码。
- 建议仅在受信任的内网使用，不要直接映射到公网。

---

## 常见问题

| 现象 | 排查 |
|------|------|
| 网页显示「连接失败」 | 确认服务已启动、电脑防火墙放行 8010、手机与电脑同一网段 |
| 点启动提示「BAT 文件不存在」 | 检查 `config.json` 的 `bat_path` 是否为绝对路径且文件存在 |
| 点停止后子进程仍在 | 确认服务以有权限的账户运行；`taskkill /T` 需要相同或更高权限 |
| `KFS.exe install` 失败 | 需**以管理员身份**运行命令行（创建 `SYSTEM` 账户计划任务） |
| 日志为空 | 打包 EXE 运行时日志写在 exe 同目录的 `service.log`，检查该文件 |

---

## 开发

```bash
# 源码运行（带控制台输出）
cd pc-service
python app.py run

# 生成 EXE
py -m PyInstaller KFS.spec --noconfirm
```

技术栈：Python 3.6+ / Flask · 原生 Android WebView（无第三方依赖）

---

## 许可证

本项目采用 [MIT License](LICENSE) 开源。
