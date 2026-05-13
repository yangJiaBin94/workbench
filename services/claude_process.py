import json
import os
from PyQt6.QtCore import QProcess, QProcessEnvironment, pyqtSignal, QObject


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
            "--append-system-prompt", "请始终使用简体中文进行思考、对话和工具描述。代码和命令保持原样。",
        ]
        self._proc.start("claude", args)

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
            QProcess.ProcessError.FailedToStart: "无法启动 claude，请确认已安装并在 PATH 中",
            QProcess.ProcessError.Crashed: "claude 进程崩溃",
            QProcess.ProcessError.Timedout: "claude 进程超时",
            QProcess.ProcessError.ReadError: "读取 claude 输出失败",
            QProcess.ProcessError.WriteError: "写入 claude 输入失败",
        }
        msg = err_msgs.get(error, f"claude 进程错误: {error}")
        self.process_error.emit(msg)
