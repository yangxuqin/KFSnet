# -*- coding: utf-8 -*-
"""
BAT 任务 Web 控制服务
=====================
通过浏览器（局域网内）控制指定 .bat 脚本的启动与停止。

打包后支持子命令：
  KFS.exe              等同于 run（前台运行服务）
  KFS.exe run          前台运行服务
  KFS.exe install      注册为 Windows 计划任务（开机自启，无需用户登录）
  KFS.exe uninstall    移除计划任务
  KFS.exe status       查看计划任务与服务状态

配置文件 config.json 与 exe 同目录（开发时与 app.py 同目录）。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import traceback

# ======================== 路径适配（支持 PyInstaller 打包） ========================
if getattr(sys, 'frozen', False):
    # 打包后：exe 所在目录放 config.json / 日志；资源（templates）在 _MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR

# ======================== 配置区 ========================

# 默认配置（首次运行会据此生成 config.json，之后直接改 config.json 即可）
DEFAULT_CONFIG = {
    # 目标 BAT 脚本的完整路径；默认为仓库自带的示例脚本，请改为你自己的脚本
    "bat_path": os.path.join(os.path.dirname(APP_DIR), "examples", "kfs.bat"),
    "host": "0.0.0.0",                      # 0.0.0.0 允许局域网访问，127.0.0.1 仅本机
    "port": 8010,                           # 服务监听端口
    "token": "",                            # 访问令牌，留空表示不启用认证
    "log_file": "",                         # 日志文件，留空则用 APP_DIR/service.log
    "task_name": "KFSnetService",           # 计划任务名称
}

CONFIG_PATH = os.path.join(APP_DIR, "config.json")


def load_config():
    """加载 config.json，不存在则用默认配置生成一个"""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception as e:
            print("[警告] 读取 config.json 失败，使用默认配置: {}".format(e))
    else:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            print("[初始化] 已生成配置文件: {}".format(CONFIG_PATH))
        except Exception:
            pass
    return config


CONFIG = load_config()
BAT_PATH = CONFIG.get("bat_path", "")
HOST = CONFIG.get("host", "0.0.0.0")
PORT = int(CONFIG.get("port", 8010))
TOKEN = CONFIG.get("token", "") or ""
LOG_FILE = CONFIG.get("log_file") or os.path.join(APP_DIR, "service.log")
TASK_NAME = CONFIG.get("task_name", "KFSnetService")

# ======================== 配置区结束 ========================

# 日志（同时输出到控制台和文件，pythonw/exe 无窗口模式下日志仍会落盘）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("bat-controller")

# Windows 专用导入
if sys.platform == "win32":
    import signal
    signal.signal(signal.SIGBREAK, signal.SIG_IGN)

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    print("[错误] 未安装 Flask，请运行: pip install flask")
    sys.exit(1)

# Flask 模板目录指向资源目录（打包后资源在 _MEIPASS）
app = Flask(__name__, template_folder=os.path.join(RESOURCE_DIR, "templates"))

# 全局状态
_process = None          # subprocess.Popen 对象
_process_lock = threading.Lock()  # 线程锁
_running = False         # 是否正在运行


def get_bat_filename():
    """从完整路径中提取文件名用于日志"""
    try:
        return os.path.basename(BAT_PATH) if BAT_PATH else "task.bat"
    except Exception:
        return "task.bat"


def get_bat_dir():
    """获取 BAT 所在目录"""
    try:
        if BAT_PATH and os.path.exists(BAT_PATH):
            return os.path.dirname(BAT_PATH)
    except Exception:
        pass
    return None


def check_process_alive(proc):
    """检查进程是否仍然存活"""
    if proc is None:
        return False
    try:
        return proc.poll() is None
    except Exception:
        return False


def kill_process_tree(pid):
    """终止指定 PID 及其所有子进程（整个进程树）"""
    try:
        subprocess.call(
            ["taskkill", "/T", "/F", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        log.error("终止进程树失败: %s", e)


def start_bat():
    """启动 BAT 脚本，窗口最小化"""
    global _process, _running

    with _process_lock:
        try:
            if _running and check_process_alive(_process):
                return {"success": False, "message": "BAT 已经在运行中"}

            # 校验 BAT 文件是否存在
            if not BAT_PATH or not os.path.exists(BAT_PATH):
                return {
                    "success": False,
                    "message": "BAT 文件不存在: {}。请修改 config.json 中的 bat_path 配置。".format(BAT_PATH)
                }

            bat_dir = get_bat_dir()

            # Windows 下使用 STARTUPINFO 实现窗口最小化
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 6  # SW_MINIMIZE

            _process = subprocess.Popen(
                [BAT_PATH],
                cwd=bat_dir,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            _running = True
            log.info("[启动] %s 已启动, PID=%s", get_bat_filename(), _process.pid)
            return {"success": True, "message": "{} 已启动".format(get_bat_filename())}
        except Exception as e:
            _process = None
            _running = False
            log.error("启动失败: %s", traceback.format_exc())
            return {"success": False, "message": "启动失败: {}".format(str(e))}


def stop_bat():
    """停止 BAT 脚本及其所有子进程"""
    global _process, _running

    with _process_lock:
        try:
            if not _running or _process is None:
                return {"success": False, "message": "BAT 未在运行"}

            pid = _process.pid
            try:
                kill_process_tree(pid)
                _process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                kill_process_tree(pid)
            except Exception:
                pass

            _process = None
            _running = False
            log.info("[停止] %s (PID=%s) 已停止", get_bat_filename(), pid)
            return {"success": True, "message": "{} 已停止".format(get_bat_filename())}
        except Exception as e:
            log.error("停止失败: %s", traceback.format_exc())
            return {"success": False, "message": "停止失败: {}".format(str(e))}


def get_status():
    """获取当前 BAT 运行状态"""
    global _process, _running

    with _process_lock:
        try:
            if _process is None:
                _running = False
            else:
                alive = check_process_alive(_process)
                if not alive:
                    log.info("[检测] %s 已被外部关闭", get_bat_filename())
                    _running = False
                    _process = None

            pid_val = None
            if _process is not None and _running:
                try:
                    pid_val = _process.pid
                except Exception:
                    pid_val = None

            return {
                "running": _running,
                "bat_name": get_bat_filename(),
                "pid": pid_val
            }
        except Exception as e:
            log.error("获取状态失败: %s", traceback.format_exc())
            return {
                "running": False,
                "bat_name": get_bat_filename(),
                "pid": None,
                "error": str(e)
            }


def check_auth():
    """校验访问令牌；未配置 TOKEN 时直接放行"""
    if not TOKEN:
        return True
    header_token = request.headers.get("X-Auth-Token", "")
    query_token = request.args.get("token", "")
    return header_token == TOKEN or query_token == TOKEN


# ======================== Web 路由 ========================

@app.before_request
def before_request():
    """仅对 API 接口校验令牌，页面本身可访问"""
    if request.path.startswith("/api/") and not check_auth():
        return jsonify({"success": False, "message": "未授权，请检查访问令牌"}), 401


@app.route("/")
def index():
    """主控制面板页面"""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    """获取 BAT 运行状态"""
    try:
        return jsonify(get_status())
    except Exception as e:
        log.error("api/status 异常: %s", traceback.format_exc())
        return jsonify({"running": False, "error": str(e)}), 500


@app.route("/api/start", methods=["POST"])
def api_start():
    """启动 BAT"""
    try:
        return jsonify(start_bat())
    except Exception as e:
        log.error("api/start 异常: %s", traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """停止 BAT"""
    try:
        return jsonify(stop_bat())
    except Exception as e:
        log.error("api/stop 异常: %s", traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 计划任务管理 ========================

def get_exe_path():
    """获取当前可执行文件路径（打包后为 exe，开发时为解释器+脚本）"""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return None  # 开发模式下用 python app.py 形式，由调用方拼装


def build_run_command():
    """构造计划任务要执行的命令行"""
    if getattr(sys, 'frozen', False):
        # exe run
        return '"{}" run'.format(sys.executable)
    else:
        # 开发模式：pythonw app.py run
        return '"{}" "{}" run'.format(sys.executable, os.path.join(APP_DIR, "app.py"))


def task_exists():
    """检查计划任务是否已存在"""
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return r.returncode == 0
    except Exception:
        return False


def install_task():
    """注册为 Windows 计划任务（开机启动，无需用户登录）"""
    if task_exists():
        print("[提示] 计划任务 {} 已存在，先移除再重新创建".format(TASK_NAME))
        subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = build_run_command()
    # /sc ONSTART 系统启动时触发；/ru SYSTEM 以系统账户运行（无需用户登录）；/rl HIGHEST 最高权限
    create_args = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", cmd,
        "/sc", "ONSTART",
        "/rl", "HIGHEST",
        "/ru", "SYSTEM",
        "/f",
    ]
    try:
        r = subprocess.run(create_args, capture_output=True, text=True)
        if r.returncode == 0:
            print("[成功] 计划任务已创建: {}".format(TASK_NAME))
            print("       触发方式: 系统启动时自动运行（无需用户登录）")
            print("       运行账户: SYSTEM（最高权限）")
            print("       命令: {}".format(cmd))
            print("       可用 'KFS.exe status' 查看状态，'KFS.exe uninstall' 移除")
            return True
        else:
            print("[失败] 创建计划任务失败:")
            print(r.stderr or r.stdout)
            print("[提示] 请以管理员身份运行此命令")
            return False
    except Exception as e:
        print("[失败] 创建计划任务异常: {}".format(e))
        return False


def uninstall_task():
    """移除计划任务"""
    if not task_exists():
        print("[提示] 计划任务 {} 不存在".format(TASK_NAME))
        return True
    try:
        r = subprocess.run(
            ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            print("[成功] 计划任务 {} 已移除".format(TASK_NAME))
            return True
        else:
            print("[失败] 移除失败:")
            print(r.stderr or r.stdout)
            return False
    except Exception as e:
        print("[失败] 移除计划任务异常: {}".format(e))
        return False


def task_status():
    """查看计划任务状态"""
    if not task_exists():
        print("[状态] 计划任务 {} 未安装".format(TASK_NAME))
        print("       运行 'KFS.exe install' 可注册为开机自启任务")
        return
    try:
        r = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME, "/v", "/fo", "list"],
            capture_output=True, text=True, encoding="gbk", errors="replace"
        )
        if r.returncode == 0:
            print(r.stdout)
        else:
            print("[失败] 查询失败:")
            print(r.stderr or r.stdout)
    except Exception as e:
        print("[失败] 查询异常: {}".format(e))


# ======================== 运行服务 ========================

def run_service():
    """前台运行 Web 控制服务"""
    # 检查 BAT 文件
    if BAT_PATH and os.path.exists(BAT_PATH):
        log.info("[就绪] BAT 脚本: %s", BAT_PATH)
    else:
        log.warning("[警告] BAT 文件不存在: %s", BAT_PATH)
        log.warning("        请修改 config.json 中的 bat_path 后重启服务。")

    if TOKEN:
        log.info("[安全] 已启用访问令牌认证")
    else:
        log.warning("[提示] 未配置访问令牌，局域网内任何人都可控制任务")

    log.info("[就绪] 控制面板: http://%s:%s", HOST, PORT)
    log.info("[就绪] 按 Ctrl+C 停止服务")

    # 生产环境关闭 debug，避免调试器被局域网访问导致远程代码执行风险
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)


# ======================== 启动入口 ========================

def main():
    parser = argparse.ArgumentParser(
        prog="KFS",
        description="BAT 任务 Web 控制服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  KFS.exe                  前台运行服务（默认）
  KFS.exe run              前台运行服务
  KFS.exe install          注册为计划任务（开机自启，无需登录）*需管理员权限*
  KFS.exe uninstall        移除计划任务
  KFS.exe status           查看计划任务状态

配置: 与 exe 同目录的 config.json
日志: 与 exe 同目录的 service.log
""",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "install", "uninstall", "status"],
        help="子命令: run(运行) / install(注册计划任务) / uninstall(移除) / status(状态)",
    )
    args = parser.parse_args()

    if args.command == "install":
        install_task()
    elif args.command == "uninstall":
        uninstall_task()
    elif args.command == "status":
        task_status()
    else:
        run_service()


if __name__ == "__main__":
    main()
