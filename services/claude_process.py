import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment, pyqtSignal, QObject


def find_claude() -> str | None:
    """查找 claude CLI 可执行文件的完整路径。

    优先搜索 PATH，找不到则搜索 npm 全局安装目录。
    返回完整路径则可用 QProcess 直接启动。
    返回 None 表示未安装。
    """
    # 1. 优先在 PATH 中查找
    found = shutil.which("claude")
    if found:
        return found

    if sys.platform == "win32":
        # 2. Windows: 搜索 npm 全局目录
        # 通过 npm config get prefix 获取全局安装前缀
        try:
            result = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True, text=True, timeout=5,
            )
            npm_prefix = result.stdout.strip()
            if npm_prefix:
                candidate = os.path.join(npm_prefix, "claude.cmd")
                if os.path.isfile(candidate):
                    return candidate
        except Exception:
            pass

        # 3. Windows 备用: %APPDATA%\npm
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidate = os.path.join(appdata, "npm", "claude.cmd")
            if os.path.isfile(candidate):
                return candidate
    else:
        # 2. macOS/Linux: 搜索常见 npm 全局 bin 目录
        candidates = [
            os.path.join(str(Path.home()), ".npm-global", "bin", "claude"),
            os.path.join(str(Path.home()), ".local", "bin", "claude"),
            "/usr/local/bin/claude",
            "/opt/homebrew/bin/claude",
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        # 3. macOS/Linux: 通过 npm config get prefix
        try:
            result = subprocess.run(
                ["npm", "config", "get", "prefix"],
                capture_output=True, text=True, timeout=5,
            )
            npm_prefix = result.stdout.strip()
            if npm_prefix:
                candidate = os.path.join(npm_prefix, "bin", "claude")
                if os.path.isfile(candidate):
                    return candidate
        except Exception:
            pass

    return None


def _install_hint() -> str:
    if sys.platform == "win32":
        return (
            "未找到 claude CLI。请先安装：\n"
            "  npm install -g @anthropic-ai/claude-code\n\n"
            "如已安装但仍提示此错误，请将 npm 全局目录添加到 PATH。\n"
            "npm 全局目录通常在：%APPDATA%\\npm"
        )
    else:
        return (
            "未找到 claude CLI。请先安装：\n"
            "  npm install -g @anthropic-ai/claude-code\n\n"
            "如已安装但仍提示此错误，请将 npm 全局 bin 目录添加到 PATH。\n"
            "通常在：~/.local/bin 或 ~/.npm-global/bin"
        )


class ClaudeProcess(QObject):
    output_line = pyqtSignal(str)
    process_error = pyqtSignal(str)
    process_finished = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc: QProcess | None = None
        self._working_dir = ""
        self._buffer = b""

    def start(self, working_dir: str = ""):
        if self._proc is not None:
            self.stop()

        claude_path = find_claude()
        if claude_path is None:
            self.process_error.emit(_install_hint())
            return

        self._working_dir = working_dir or os.getcwd()
        self._proc = QProcess(self)
        self._proc.setWorkingDirectory(self._working_dir)
        self._proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self._proc.setProcessEnvironment(env)

        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_error)

        args = [
            "--print",
            "--verbose",
            "--output-format", "stream-json",
            "--input-format", "stream-json",
            "--include-partial-messages",
            "--permission-mode", "acceptEdits",
            "--permission-prompt-tool", "stdio",
            "--append-system-prompt", "请始终使用简体中文进行思考、对话和工具描述。代码和命令保持原样。",
        ]
        self._proc.start(claude_path, args)

    def send_control_response(self, request_id: str, behavior: str = "allow"):
        if self._proc is None or self._proc.state() != QProcess.ProcessState.Running:
            return
        payload = json.dumps({
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "behavior": behavior,
                    "updatedInput": {},
                },
            },
        })
        self._proc.write((payload + "\n").encode("utf-8"))

    def send_message(self, text: str):
        if self._proc is None or self._proc.state() != QProcess.ProcessState.Running:
            return
        payload = json.dumps({
            "type": "user",
            "message": {"role": "user", "content": text},
        })
        self._proc.write((payload + "\n").encode("utf-8"))

    def is_running(self) -> bool:
        return (
            self._proc is not None
            and self._proc.state() == QProcess.ProcessState.Running
        )

    def stop(self):
        if self._proc is not None:
            self._proc.readyReadStandardOutput.disconnect(self._on_stdout)
            self._proc.readyReadStandardError.disconnect(self._on_stderr)
            self._proc.errorOccurred.disconnect(self._on_error)

            if self._proc.state() != QProcess.ProcessState.NotRunning:
                self._proc.finished.connect(self._on_stop_finished)
                self._proc.terminate()
            else:
                self._proc = None

    def _on_stop_finished(self):
        if self._proc is not None:
            self._proc.deleteLater()
            self._proc = None

    def _on_stdout(self):
        if self._proc is None:
            return
        data = bytes(self._proc.readAllStandardOutput())
        self._buffer += data
        while b"\n" in self._buffer:
            line, self._buffer = self._buffer.split(b"\n", 1)
            try:
                text = line.decode("utf-8", errors="replace")
            except Exception:
                text = str(line)
            if text.strip():
                self.output_line.emit(text)

    def _on_stderr(self):
        if self._proc is None:
            return
        data = bytes(self._proc.readAllStandardError())
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = str(data)
        if text.strip():
            self.process_error.emit(text)

    def _on_finished(self, exit_code: int):
        if self._buffer:
            try:
                text = self._buffer.decode("utf-8", errors="replace")
            except Exception:
                text = str(self._buffer)
            self._buffer = b""
            if text.strip():
                self.output_line.emit(text)
        self.process_finished.emit(exit_code)

    def _on_error(self, error: QProcess.ProcessError):
        err_msgs = {
            QProcess.ProcessError.FailedToStart: (
                "无法启动 claude 进程，请确认 claude 可执行文件完整且未被杀毒软件拦截。\n"
                "可尝试在终端中手动执行 claude 验证是否正常：\n  claude --version"
            ),
            QProcess.ProcessError.Crashed: "claude 进程崩溃",
            QProcess.ProcessError.Timedout: "claude 进程超时",
            QProcess.ProcessError.ReadError: "读取 claude 输出失败",
            QProcess.ProcessError.WriteError: "写入 claude 输入失败",
        }
        msg = err_msgs.get(error, f"claude 进程错误: {error}")
        self.process_error.emit(msg)
