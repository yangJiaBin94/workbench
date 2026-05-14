import re
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QTextEdit, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics
from ui.theme import (
    GREEN, GREEN_DARK, SURFACE0, SURFACE1, MANTLE, CRUST, BLUE, TEAL, YELLOW, MAUVE,
    TEXT, SUBTEXT0, SUBTEXT1, OVERLAY0, SURFACE2, PEACH, RED, FONT_MONO,
)

TOOL_NAMES_ZH = {
    "Read": "读取文件",
    "Write": "写入文件",
    "Edit": "编辑文件",
    "Bash": "执行命令",
    "Grep": "搜索内容",
    "Glob": "搜索文件",
    "WebFetch": "获取网页",
    "WebSearch": "网络搜索",
    "Task": "任务管理",
    "Agent": "子代理",
    "AskUserQuestion": "询问用户",
    "EnterPlanMode": "进入规划",
    "ExitPlanMode": "提交规划",
    "CronCreate": "定时任务",
    "CronDelete": "删除定时",
    "CronList": "定时列表",
    "ScheduleWakeup": "计划唤醒",
}

USER_BUBBLE_PAD_H = 32   # 16px left + 16px right
ASST_BUBBLE_PAD_H = 36   # 18px left + 18px right


def _mono_font(size: int = 12) -> QFont:
    f = QFont()
    f.setFamilies([FONT_MONO])
    f.setPixelSize(size)
    return f


class _WrapTextEdit(QTextEdit):
    """QTextEdit that auto-sizes to its document — no scrolling, wraps at any char."""

    def __init__(self, parent=None, style: str = ""):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.document().setDocumentMargin(0)
        if style:
            self.setStyleSheet(style)

    def set_width(self, max_w: int):
        self._max_w = max_w
        self._apply_width()

    def _apply_width(self):
        max_w = getattr(self, '_max_w', 0)
        if max_w <= 0:
            return
        plain = self.toPlainText()
        fm = QFontMetrics(self.font())
        lines = plain.split('\n')
        text_w = max((fm.horizontalAdvance(line) for line in lines), default=0)
        w = text_w + 8 if text_w < max_w else max_w
        self.setFixedWidth(w)
        self.document().setTextWidth(w)
        h = int(self.document().size().height())
        self.setFixedHeight(max(h, 1))

    def setPlainText(self, text: str):
        super().setPlainText(text)
        self._apply_width()

    def setHtml(self, html: str):
        super().setHtml(html)
        self._apply_width()

    def _sync_height(self):
        h = int(self.document().size().height())
        self.setFixedHeight(max(h, 1))


class UserBubble(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(f"""
            UserBubble {{
                background: {GREEN};
                border-radius: 12px;
                border-bottom-right-radius: 4px;
                padding: 10px 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._content = _WrapTextEdit(
            style=f"font-size: 13px; color: {CRUST}; background: transparent; border: none; padding: 0;"
        )
        self._content.setPlainText(text)
        layout.addWidget(self._content)

    def set_content_width(self, max_frame_w: int):
        self._content.set_width(max_frame_w - USER_BUBBLE_PAD_H)


class AssistantBubble(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(f"""
            AssistantBubble {{
                background: {SURFACE0};
                border-radius: 12px;
                border-bottom-left-radius: 4px;
                padding: 12px 18px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._role = QLabel("Claude Code")
        self._role.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEAL}; background: transparent;")
        layout.addWidget(self._role)

        self._content = _WrapTextEdit(
            style=f"color: {TEXT}; font-size: 13px; background: transparent; border: none; padding: 0;"
        )
        layout.addWidget(self._content)

        self._text = ""

    def set_content_width(self, max_frame_w: int):
        self._content.set_width(max_frame_w - ASST_BUBBLE_PAD_H)

    def append_text(self, delta: str):
        self._text += delta
        self._content.setHtml(self._render_markdown(self._text))

    def set_text(self, text: str):
        self._text = text
        self._content.setHtml(self._render_markdown(text))

    def _render_markdown(self, text: str) -> str:
        t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def code_block_repl(m):
            lang = m.group(1) or ""
            code = m.group(2)
            return f'<pre style="background:{MANTLE};border:1px solid {SURFACE1};border-radius:8px;padding:12px 14px;overflow-x:auto;margin:8px 0;"><code style="color:{GREEN};font-size:12px;line-height:1.6;">{code}</code></pre>'

        t = re.sub(r'```(\w*)\n(.*?)```', code_block_repl, t, flags=re.DOTALL)

        t = re.sub(r'^### (.+)$', f'<h3 style="color:{TEAL};font-size:13px;font-weight:700;margin:12px 0 4px;">\\1</h3>', t, flags=re.MULTILINE)
        t = re.sub(r'^## (.+)$', f'<h2 style="color:{TEXT};font-size:14px;font-weight:700;margin:12px 0 4px;">\\1</h2>', t, flags=re.MULTILINE)
        t = re.sub(r'^# (.+)$', f'<h1 style="color:{TEXT};font-size:14px;font-weight:700;margin:12px 0 4px;">\\1</h1>', t, flags=re.MULTILINE)

        t = re.sub(r'^---$', f'<hr style="border:none;border-top:1px solid {SURFACE1};margin:12px 0;">', t, flags=re.MULTILINE)

        t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', t)
        t = re.sub(r'`([^`]+)`', f'<code style="font-size:12px;background:{SURFACE1};padding:1px 6px;border-radius:4px;color:{PEACH};">\\1</code>', t)

        t = re.sub(r'^&gt; (.+)$', f'<blockquote style="border-left:3px solid {GREEN};padding-left:12px;color:{SUBTEXT0};margin:6px 0;">\\1</blockquote>', t, flags=re.MULTILINE)

        t = t.replace("\n\n", "<br><br>")
        t = t.replace("\n", "<br>")

        return t


def _extract_target(tool_name: str, params: dict | None) -> str:
    """Extract the key target (file path, URL, command, etc.) from tool params."""
    if not params:
        return ""
    if tool_name == "Bash":
        return params.get("description", "") or params.get("command", "")
    if tool_name in ("WebFetch", "WebSearch"):
        return params.get("url", "") or params.get("query", "")
    if tool_name in ("Read", "Write", "Edit"):
        return params.get("file_path", "")
    if tool_name in ("Grep", "Glob"):
        parts = []
        if params.get("pattern"):
            parts.append(params["pattern"])
        if params.get("path"):
            parts.append(f"in {params['path']}")
        if params.get("glob"):
            parts.append(f"({params['glob']})")
        return " ".join(parts) if parts else ""
    if tool_name == "Agent":
        return params.get("description", "") or params.get("prompt", "")[:80]
    # Generic fallback: first string value that looks like a path or URL
    for v in params.values():
        if isinstance(v, str) and ("/" in v or "\\" in v or v.startswith("http")):
            return v
    return ""


class ToolCallCard(QFrame):
    expand_requested = pyqtSignal(dict)

    def __init__(self, tool_name: str, params: dict | None = None, description: str = "", parent=None):
        super().__init__(parent)
        self._tool_name = tool_name
        self._params = params
        self.setStyleSheet(f"""
            ToolCallCard {{
                background: {MANTLE};
                border: 1px solid {SURFACE1};
                border-left: 3px solid {YELLOW};
                border-radius: 8px;
                padding: 10px 16px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icon = QLabel("◇")
        icon.setStyleSheet(f"font-size: 14px; color: {YELLOW}; background: transparent;")
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        body = QVBoxLayout()
        body.setSpacing(4)

        # Title row: Chinese name + original name
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        name_zh = TOOL_NAMES_ZH.get(tool_name, tool_name)
        name_lbl = QLabel(name_zh)
        name_lbl.setFont(_mono_font(12))
        name_lbl.setStyleSheet(f"font-weight: 700; color: {YELLOW}; background: transparent;")
        title_row.addWidget(name_lbl)

        if tool_name in TOOL_NAMES_ZH:
            orig = QLabel(tool_name)
            orig.setStyleSheet(f"font-size: 10px; color: {OVERLAY0}; background: transparent;")
            title_row.addWidget(orig)

        title_row.addStretch()
        body.addLayout(title_row)

        # Target detail: file path / URL / command
        target = _extract_target(tool_name, params)
        if target:
            detail = QLabel(target)
            detail.setWordWrap(True)
            detail.setFont(_mono_font(11))
            detail.setStyleSheet(f"""
                font-size: 11px;
                color: {GREEN};
                background: {CRUST};
                padding: 4px 10px;
                border-radius: 4px;
            """)
            body.addWidget(detail)

        if description:
            desc = QLabel(description)
            desc.setWordWrap(True)
            desc.setStyleSheet(f"font-size: 12px; color: {OVERLAY0}; background: transparent;")
            body.addWidget(desc)

        layout.addLayout(body, 1)


class PermissionPrompt(QFrame):
    confirmed = pyqtSignal(str, str)  # request_id, behavior ("allow" | "deny")

    def __init__(self, request_id: str, tool_name: str, tool_input: dict | None = None, parent=None):
        super().__init__(parent)
        self._request_id = request_id
        self._resolved = False

        self.setStyleSheet(f"""
            PermissionPrompt {{
                background: {MANTLE};
                border: 1px solid {SURFACE1};
                border-left: 3px solid {PEACH};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        icon = QLabel("◆")
        icon.setStyleSheet(f"font-size: 14px; color: {PEACH}; background: transparent;")
        header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)

        name_zh = TOOL_NAMES_ZH.get(tool_name, tool_name)
        title = QLabel(f"需要确认 — {name_zh}")
        title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {PEACH}; background: transparent;")
        header_text.addWidget(title)

        subtitle = QLabel(tool_name)
        subtitle.setStyleSheet(f"font-size: 10px; color: {OVERLAY0}; background: transparent;")
        header_text.addWidget(subtitle)

        header_row.addLayout(header_text)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Show target detail
        target = _extract_target(tool_name, tool_input)
        if target:
            detail = QLabel(target)
            detail.setWordWrap(True)
            detail.setFont(_mono_font(11))
            detail.setStyleSheet(f"""
                font-size: 11px;
                color: {GREEN};
                background: {CRUST};
                padding: 6px 10px;
                border-radius: 4px;
            """)
            layout.addWidget(detail)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        deny_btn = QPushButton("拒绝")
        deny_btn.setFixedSize(72, 34)
        deny_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        deny_btn.setStyleSheet(_perm_btn_style(RED, RED))
        deny_btn.clicked.connect(lambda: self._resolve("deny"))
        btn_row.addWidget(deny_btn)

        allow_btn = QPushButton("允许")
        allow_btn.setFixedSize(72, 34)
        allow_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        allow_btn.setStyleSheet(_perm_btn_style(GREEN, GREEN_DARK))
        allow_btn.clicked.connect(lambda: self._resolve("allow"))
        btn_row.addWidget(allow_btn)

        layout.addLayout(btn_row)

    def _resolve(self, behavior: str):
        if self._resolved:
            return
        self._resolved = True
        self.confirmed.emit(self._request_id, behavior)
        self.setEnabled(False)
        label = "已允许" if behavior == "allow" else "已拒绝"
        color = GREEN if behavior == "allow" else RED
        self.setStyleSheet(f"""
            PermissionPrompt {{
                background: {MANTLE};
                border: 1px solid {SURFACE0};
                border-left: 3px solid {color};
                border-radius: 8px;
                padding: 12px 16px;
                opacity: 0.6;
            }}
        """)


def _perm_btn_style(color: str, hover_color: str) -> str:
    return f"""
        QPushButton {{
            background: transparent;
            color: {color};
            border: 1px solid {color};
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: {hover_color};
            color: {CRUST};
            border-color: {hover_color};
        }}
    """


class ThinkingBlock(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._text = text
        self.setStyleSheet(f"""
            ThinkingBlock {{
                background: {MANTLE};
                border: 1px solid {SURFACE0};
                border-radius: 8px;
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._header = QFrame()
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(14, 8, 14, 8)
        header_layout.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {OVERLAY0}; font-size: 10px; background: transparent;")
        header_layout.addWidget(self._dot)

        label = QLabel("思考过程")
        label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {OVERLAY0}; background: transparent;")
        header_layout.addWidget(label)

        header_layout.addStretch()

        self._chevron = QLabel("▾")
        self._chevron.setStyleSheet(f"font-size: 10px; color: {OVERLAY0}; background: transparent;")
        header_layout.addWidget(self._chevron)

        self._header.mousePressEvent = self._toggle
        self._outer.addWidget(self._header)

        self._content = QLabel(text)
        self._content.setWordWrap(True)
        self._content.setStyleSheet(f"""
            font-size: 12px;
            color: {SURFACE2};
            line-height: 1.5;
            font-style: italic;
            padding: 0 14px 12px 14px;
            background: transparent;
        """)
        self._content.setVisible(False)
        self._outer.addWidget(self._content)

    def _toggle(self, event=None):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        if self._expanded:
            self._dot.setStyleSheet(f"color: {MAUVE}; font-size: 10px; background: transparent;")
        else:
            self._dot.setStyleSheet(f"color: {OVERLAY0}; font-size: 10px; background: transparent;")
