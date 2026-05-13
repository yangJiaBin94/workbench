from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from ui.theme import (
    BASE, OVERLAY0, SUBTEXT0, SURFACE0, SURFACE1, GREEN, TEAL, BLUE, FONT_SANS,
)
from ui.message_widgets import UserBubble, AssistantBubble, ToolCallCard, ThinkingBlock
from models.session import Message


class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            TypingIndicator {{
                background: {SURFACE0};
                border-radius: 12px;
                border-bottom-left-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(6)

        self._dots: list[QLabel] = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"font-size: 5px; color: {OVERLAY0}; background: transparent;")
            layout.addWidget(dot)
            self._dots.append(dot)

        label = QLabel("Claude 正在思考...")
        label.setStyleSheet(f"font-size: 12px; color: {SUBTEXT0}; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()

        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)

    def _animate(self):
        self._step = (self._step + 1) % 3
        for i, dot in enumerate(self._dots):
            if i == self._step:
                dot.setStyleSheet(f"font-size: 5px; color: {GREEN}; background: transparent;")
            else:
                dot.setStyleSheet(f"font-size: 5px; color: {OVERLAY0}; background: transparent;")

    def stop(self):
        self._timer.stop()

    def deleteLater(self):
        self._timer.stop()
        super().deleteLater()


class ChatPanel(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: {BASE};
            }}
        """)

        self._container = QWidget()
        self._container.setStyleSheet(f"background: {BASE};")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 24, 0, 24)
        self._layout.setSpacing(8)

        self._inner = QVBoxLayout()
        self._inner.setContentsMargins(32, 0, 32, 0)
        self._inner.setSpacing(10)

        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addLayout(self._inner, 1)
        wrap.addStretch()
        self._layout.addLayout(wrap)
        self._layout.addStretch()

        self.setWidget(self._container)

        self._bubble_map: dict[int, AssistantBubble] = {}
        self._typing: TypingIndicator | None = None
        self._bubble_widgets: list[QFrame] = []

    def _max_bubble_width(self) -> int:
        available = self.viewport().width() - 64
        return max(int(available * 0.6), 200)

    def _track_bubble(self, widget: QFrame):
        w = self._max_bubble_width()
        widget.setMaximumWidth(w)
        if hasattr(widget, 'set_content_width'):
            widget.set_content_width(w)
        self._bubble_widgets.append(widget)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self._max_bubble_width()
        for bubble in self._bubble_widgets:
            try:
                bubble.setMaximumWidth(w)
                if hasattr(bubble, 'set_content_width'):
                    bubble.set_content_width(w)
            except RuntimeError:
                pass

    def clear(self):
        while self._inner.count():
            item = self._inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
        self._bubble_map.clear()
        self._bubble_widgets.clear()
        self._remove_typing()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def show_empty_state(self):
        self.clear()
        empty = QVBoxLayout()
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.addStretch()

        icon = QLabel("◈")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"font-size: 40px; color: {GREEN}; background: transparent;")
        empty.addWidget(icon)
        empty.addSpacing(8)

        title = QLabel("开始新对话")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {SUBTEXT0}; background: transparent;")
        empty.addWidget(title)
        empty.addSpacing(4)

        hint = QLabel("在下方输入消息，开始协作")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"font-size: 12px; color: {OVERLAY0}; background: transparent;")
        empty.addWidget(hint)

        empty.addStretch()
        self._inner.addLayout(empty)

    def add_user_bubble(self, text: str):
        self._remove_typing()
        row = QHBoxLayout()
        row.addStretch()
        bubble = UserBubble(text)
        self._track_bubble(bubble)
        row.addWidget(bubble)
        self._inner.addLayout(row)
        self._scroll_bottom()

    def show_typing(self):
        self._remove_typing()
        row = QHBoxLayout()
        self._typing = TypingIndicator()
        self._typing.setMaximumWidth(self._max_bubble_width())
        row.addWidget(self._typing)
        row.addStretch()
        self._inner.addLayout(row)
        self._scroll_bottom()

    def _remove_typing(self):
        if self._typing:
            self._typing.deleteLater()
            self._typing = None

    def add_thinking(self, text: str):
        self._remove_typing()
        row = QHBoxLayout()
        block = ThinkingBlock(text)
        self._track_bubble(block)
        row.addWidget(block)
        row.addStretch()
        self._inner.addLayout(row)
        self._scroll_bottom()

    def add_tool_card(self, tool_name: str, description: str = "", params: dict | None = None):
        self._remove_typing()
        row = QHBoxLayout()
        card = ToolCallCard(tool_name, params, description)
        self._track_bubble(card)
        row.addWidget(card)
        row.addStretch()
        self._inner.addLayout(row)
        self._scroll_bottom()

    def add_or_update_assistant_bubble(self, msg_id: int) -> AssistantBubble:
        self._remove_typing()
        if msg_id in self._bubble_map:
            return self._bubble_map[msg_id]

        row = QHBoxLayout()
        bubble = AssistantBubble()
        self._track_bubble(bubble)
        row.addWidget(bubble)
        row.addStretch()
        self._inner.addLayout(row)

        self._bubble_map[msg_id] = bubble
        return bubble

    def finish_assistant_bubble(self, msg_id: int, text: str):
        bubble = self._bubble_map.pop(msg_id, None)
        if bubble:
            bubble.set_text(text)

    def add_assistant_bubble(self, text: str):
        self._remove_typing()
        row = QHBoxLayout()
        bubble = AssistantBubble()
        bubble.set_text(text)
        self._track_bubble(bubble)
        row.addWidget(bubble)
        row.addStretch()
        self._inner.addLayout(row)
        self._scroll_bottom()

    def restore_messages(self, messages: list[Message]):
        self.clear()
        for msg in messages:
            if msg.role == "user":
                self.add_user_bubble(msg.content)
            elif msg.role == "assistant":
                if msg.event_type == "tool_call":
                    import json
                    try:
                        info = json.loads(msg.content)
                        self.add_tool_card(info.get("name", msg.content), params=info.get("params"))
                    except (json.JSONDecodeError, TypeError):
                        self.add_tool_card(msg.content)
                elif msg.event_type == "thinking":
                    self.add_thinking(msg.content)
                elif msg.content.strip():
                    self.add_assistant_bubble(msg.content)
        self._scroll_bottom()

    def _scroll_bottom(self):
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))
