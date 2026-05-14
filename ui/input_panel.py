from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeyEvent
from ui.theme import (
    MANTLE, SURFACE0, SURFACE1, GREEN, GREEN_DARK, CRUST,
    TEXT, OVERLAY0, FONT_SANS,
)


class InputPanel(QFrame):
    send_message = pyqtSignal(str)
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            InputPanel {{
                background: {MANTLE};
                border-top: 1px solid {SURFACE0};
            }}
        """)
        self._drag_over = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 14, 24, 16)
        outer.setSpacing(6)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        # Input field
        self._input = QTextEdit()
        self._input.setPlaceholderText("输入消息... (Enter 发送 · Shift+Enter 换行)")
        self._input.setFixedHeight(44)
        self._input.setAcceptRichText(False)
        self._input.setAcceptDrops(True)
        self._input.dragEnterEvent = self._on_drag_enter
        self._input.dragLeaveEvent = self._on_drag_leave
        self._input.dropEvent = self._on_drop
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background: {SURFACE0};
                color: {TEXT};
                border: 1px solid {SURFACE1};
                border-radius: 10px;
                padding: 10px 14px;
                font-family: {FONT_SANS};
                font-size: 13px;
                selection-background-color: {GREEN};
                selection-color: {CRUST};
            }}
            QTextEdit:focus {{
                border-color: {GREEN};
            }}
        """)
        self._input.installEventFilter(self)
        row.addWidget(self._input, 1)

        # Send button — Layui green
        self._send_btn = QPushButton("发 送")
        self._send_btn.setFixedSize(72, 44)
        self._send_btn.setEnabled(False)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN};
                color: {CRUST};
                border: none;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {GREEN_DARK};
            }}
            QPushButton:pressed {{
                background: #16a34a;
            }}
            QPushButton:disabled {{
                background: {SURFACE1};
                color: {OVERLAY0};
            }}
        """)
        self._send_btn.clicked.connect(self._on_send)
        row.addWidget(self._send_btn)

        outer.addLayout(row)

        # Hint
        self._hint = QLabel("Enter 发送 · Shift+Enter 换行 · 支持拖放文件到输入框")
        self._hint.setStyleSheet(f"font-size: 10px; color: {OVERLAY0}; background: transparent;")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignRight)
        outer.addWidget(self._hint)

        self._input.textChanged.connect(self._on_text_changed)

    def eventFilter(self, obj, event):
        if obj is self._input and event.type() == event.Type.KeyPress:
            ke = event
            if ke.key() == Qt.Key.Key_Return or ke.key() == Qt.Key.Key_Enter:
                if ke.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    self._input.insertPlainText("\n")
                    return True
                else:
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)

    def _on_text_changed(self):
        self._send_btn.setEnabled(bool(self._input.toPlainText().strip()))
        doc = self._input.document()
        h = int(doc.size().height()) + 20
        self._input.setFixedHeight(min(max(h, 44), 160))

    def _on_send(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
        self.send_message.emit(text)
        self._input.clear()

    def _on_drag_enter(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_over = True
            self._input.setStyleSheet(f"""
                QTextEdit {{
                    background: {SURFACE0};
                    color: {TEXT};
                    border: 2px dashed {GREEN};
                    border-radius: 10px;
                    padding: 10px 14px;
                    font-family: {FONT_SANS};
                    font-size: 13px;
                    selection-background-color: {GREEN};
                    selection-color: {CRUST};
                }}
            """)

    def _on_drag_leave(self, event):
        self._drag_over = False
        self._input.setStyleSheet(f"""
            QTextEdit {{
                background: {SURFACE0};
                color: {TEXT};
                border: 1px solid {SURFACE1};
                border-radius: 10px;
                padding: 10px 14px;
                font-family: {FONT_SANS};
                font-size: 13px;
                selection-background-color: {GREEN};
                selection-color: {CRUST};
            }}
            QTextEdit:focus {{
                border-color: {GREEN};
            }}
        """)

    def _on_drop(self, event: QDropEvent):
        self._on_drag_leave(None)
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            paths = "\n".join(files)
            cur = self._input.toPlainText()
            if cur:
                self._input.setPlainText(cur + "\n" + paths)
            else:
                self._input.setPlainText(paths)
            self.files_dropped.emit(files)
