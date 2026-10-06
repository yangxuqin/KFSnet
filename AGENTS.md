# AGENTS.md

本文件面向在本仓库工作的 AI 编码助手。人类贡献者也可参考其中的构建与约定说明。

## 项目概览

**KFSnet** 是一个 Windows 平台上的「BAT 任务远程控制」工具，由两部分组成：

1. **`pc-service/`** — Python + Flask 编写的服务端。对外提供网页控制面板和 HTTP API，
   用于启动 / 停止一个指定的 `.bat` 脚本，并可打包成单文件 `KFS.exe`。
2. **`android-app/`** — 安卓 App，本质是一个 WebView 壳，加载服务端的控制面板页面，
   额外提供服务器地址与访问令牌的设置入口。

运行环境：Windows 10/11。服务端需要 Python 3.6+（打包后不需要）。

## 仓库结构

```
pc-service/
  app.py                 # 唯一服务端源文件：配置加载 + 进程管理 + Flask 路由 + CLI 子命令
  KFS.spec               # PyInstaller 打包配置（必须声明 templates 为 datas）
  requirements.txt       # 仅 flask
  config.example.json    # 配置模板
  templates/index.html   # 网页控制面板（单文件，内联 CSS/JS）
  scripts/               # Windows 辅助脚本
    install.bat          # 安装依赖 / 建示例 / 可选设置登录自启
    uninstall.bat        # 删除启动文件夹快捷方式
    start_service.bat    # pythonw 无窗口启动
    start_hidden.vbs     # VBS 静默启动
    example_task.bat     # 生成的示例任务
android-app/             # Gradle 工程，无第三方依赖，仅用系统 WebView
examples/kfs.bat         # 示例目标任务脚本
```

## 常用命令

```bash
# 运行服务（源码方式，带控制台输出）
cd pc-service && python app.py run

# 查看 CLI 帮助
python app.py --help

# 打包单文件 EXE
cd pc-service && py -m PyInstaller KFS.spec --noconfirm
# 产物：pc-service/dist/KFS.exe

# 计划任务相关（需管理员权限）
KFS.exe install | uninstall | status
```

改动服务端后的最小验证方式：启动服务，访问 `http://127.0.0.1:8010/api/status`，
确认返回 `{"running": false, "bat_name": "...", "pid": null}`；再访问 `/` 确认页面能渲染。

## 架构要点

### `pc-service/app.py`

单文件结构，自上而下分为：

1. **路径适配** — `APP_DIR` / `RESOURCE_DIR` 在打包（`sys.frozen`）与源码两种模式下取值不同：
   - 源码：两者都是 `app.py` 所在目录
   - 打包：`APP_DIR` = exe 所在目录（放 `config.json`、`service.log`），
     `RESOURCE_DIR` = `sys._MEIPASS`（放 `templates`）
2. **配置加载** — `load_config()` 读取 `APP_DIR/config.json`，缺失则用 `DEFAULT_CONFIG` 生成
3. **日志** — `logging` 同时输出到文件与标准输出，保证无窗口模式下日志可追溯
4. **进程管理** — 模块级全局变量 `_process` / `_running`，由 `_process_lock`（`threading.Lock`）保护。
   所有读写都在锁内进行，因为 Flask 以 `threaded=True` 运行
5. **Flask 路由** — `/` 与 `/api/{status,start,stop}`；`before_request` 对所有 `/api/*` 做令牌校验
6. **计划任务管理** — 通过 `schtasks` 子命令注册 / 移除 / 查询
7. **CLI 入口** — `argparse` 子命令 `run` / `install` / `uninstall` / `status`，默认 `run`

### 关键实现约定

- **停止任务必须杀进程树**：BAT 脚本常会拉起子进程，`stop_bat()` 使用
  `taskkill /T /F /PID`，不要退化成 `terminate()`。
- **状态检测是惰性的**：`get_status()` 在发现进程已退出时会顺带把 `_running` / `_process` 置空，
  外部手动关闭 BAT 窗口后状态能自愈。
- **配置默认值在 `DEFAULT_CONFIG`**：新增配置项时同时更新它、`config.example.json` 和 README 的表格。
- **页面的令牌逻辑在 `templates/index.html`**：`apiFetch()` 统一附加 `X-Auth-Token`，
  遇到 401 会 `prompt` 用户输入并存入 `localStorage` 后重试。

## 务必遵守的约束

1. **不要启用 Flask debug 模式**。服务监听 `0.0.0.0`，Werkzeug 调试器暴露在局域网会导致远程代码执行。
   必须保持 `app.run(..., debug=False, use_reloader=False)`。
2. **不要提交 `config.json` 与 `service.log`**。它们含本机绝对路径，已在 `.gitignore` 中排除；
   配置模板改动请改 `config.example.json`。
3. **打包时 `templates` 必须存在**。改动页面后确认 `KFS.spec` 的 `datas` 仍包含
   `('templates', 'templates')`，且 `app.py` 用 `RESOURCE_DIR` 作为 `template_folder`。
4. **`pc-service/scripts/` 下的脚本用 `%~dp0..` 定位服务根目录**。
   移动或新增脚本时同步调整，否则会找不到 `app.py`。
5. **`schtasks` 注册 `SYSTEM` 账户任务需要管理员权限**。不要为了「让它能跑」而改成普通用户，
   那会破坏「无需登录即可自启」这一核心需求。
6. **安卓端不要引入第三方依赖**。`android-app` 刻意只用系统原生 API（WebView + SharedPreferences），
   保持零依赖可离线构建。

## 代码风格

- 服务端为 Python 3，使用 `str.format()` 而非 f-string（保持对 3.6 的兼容）
- 注释、日志、界面文案、提交信息统一使用**中文**
- 面向用户的一律是中文输出，代码标识符用英文
- `android-app` 使用 Java（非 Kotlin），缩进 4 空格；XML 资源 4 空格
- 提交信息采用约定式前缀：`feat:` / `fix:` / `refactor:` / `docs:` / `chore:`

## 测试

仓库当前**没有自动化测试**。改动后请手动验证：

1. `python app.py --help` — CLI 子命令可用
2. `python app.py run` → 访问 `/api/status` 与 `/` — 服务与模板正常
3. 配置 `token` 后：无令牌请求返回 `401`，带 `X-Auth-Token` 返回 `200`
4. 打包后重复步骤 2、3 — 验证 `_MEIPASS` 资源路径正确
