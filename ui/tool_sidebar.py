from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from ui.theme import (
    MANTLE, SURFACE0, SURFACE1, GREEN, TEXT, SUBTEXT0, OVERLAY0, SURFACE2, FONT_SANS,
)
from models.session import Session


class SessionItem(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, session: Session, active: bool = False, parent=None):
        super().__init__(parent)
        self.session_id = session.id
        self._active = active
        self.setFixedHeight(34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._max_width = 150

        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 0, 10, 0)
        layout.setSpacing(6)

        self._label = QLabel(session.name)
        self._label.setMaximumWidth(self._max_width)
        layout.addWidget(self._label)
        layout.addStretch()

        self._update_style()
        self._label.setText(self._elide(session.name))

    def _elide(self, text: str) -> str:
        metrics = QFontMetrics(self._label.font())
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, self._max_width)

    def _update_style(self):
        color = GREEN if self._active else SUBTEXT0
        bg = SURFACE0 if self._active else "transparent"
        self.setStyleSheet(f"""
            SessionItem {{
                background: {bg};
                border-radius: 6px;
            }}
            SessionItem:hover {{
                background: {SURFACE1};
            }}
        """)
        self._label.setStyleSheet(f"""
            font-size: 12px;
            color: {color};
            background: transparent;
            font-family: {FONT_SANS};
        """)

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def update_name(self, name: str):
        self._label.setText(self._elide(name))

    def mousePressEvent(self, event):
        self.clicked.emit(self.session_id)


class ToolSidebar(QFrame):
    session_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(210)
        self.setStyleSheet(f"""
            ToolSidebar {{
                background: {MANTLE};
                border-right: 1px solid {SURFACE0};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 12)
        layout.setSpacing(0)

        # ── Logo ──
        logo = QHBoxLayout()
        logo.setContentsMargins(6, 22, 6, 16)
        logo.setSpacing(10)

        badge = QLabel("◈")
        badge.setFixedSize(34, 34)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            font-size: 18px;
            color: {GREEN};
            background: {SURFACE0};
            border-radius: 8px;
        """)
        logo.addWidget(badge)

        name = QLabel("工作台")
        name.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {TEXT}; background: transparent;")
        logo.addWidget(name)
        logo.addStretch()
        layout.addLayout(logo)

        # ── Divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {SURFACE0}; margin: 0 6px;")
        layout.addWidget(div)
        layout.addSpacing(10)

        # ── Claude Code expandable header ──
        self._expanded = False
        self._header = QFrame()
        self._header.setFixedHeight(40)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(10)

        self._arrow = QLabel("▸")
        self._arrow.setFixedWidth(16)
        self._arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._arrow.setStyleSheet(f"font-size: 11px; color: {GREEN}; background: transparent;")

        self._header_label = QLabel("Claude Code")
        self._header_label.setStyleSheet(f"""
            font-size: 13px; font-weight: 600; color: {GREEN}; background: transparent;
        """)
        header_layout.addWidget(self._arrow)
        header_layout.addWidget(self._header_label)
        header_layout.addStretch()

        layout.addWidget(self._header)

        # ── Session list container ──
        self._session_container = QVBoxLayout()
        self._session_container.setContentsMargins(0, 4, 0, 0)
        self._session_container.setSpacing(2)

        self._session_items: list[SessionItem] = []
        self._session_list_layout = QVBoxLayout()
        self._session_list_layout.setContentsMargins(0, 0, 0, 0)
        self._session_list_layout.setSpacing(2)
        self._session_container.addLayout(self._session_list_layout)
        layout.addLayout(self._session_container)

        layout.addStretch()

        # ── Footer ──
        foot = QLabel("v0.1.0")
        foot.setStyleSheet(f"""
            font-size: 10px;
            color: {SURFACE2};
            padding: 10px 12px 0;
            border-top: 1px solid {SURFACE0};
            margin: 0 6px;
            background: transparent;
        """)
        layout.addWidget(foot)

        self._header.mousePressEvent = self._on_header_click

    def _on_header_click(self, event):
        self._expanded = not self._expanded
        self._arrow.setText("▾" if self._expanded else "▸")
        for item in self._session_items:
            item.setVisible(self._expanded)

    def set_sessions(self, sessions: list[Session], active_id: int):
        for item in self._session_items:
            item.setParent(None)
            item.deleteLater()
        self._session_items.clear()

        for sess in sessions[:10]:
            item = SessionItem(sess, active=(sess.id == active_id))
            item.clicked.connect(self.session_clicked.emit)
            item.setVisible(self._expanded)
            self._session_items.append(item)
            self._session_list_layout.addWidget(item)

    def set_active(self, active_id: int):
        for item in self._session_items:
            item.set_active(item.session_id == active_id)

    def update_session_name(self, session_id: int, name: str):
        for item in self._session_items:
            if item.session_id == session_id:
                item.update_name(name)
                break

    def remove_session(self, session_id: int):
        for item in self._session_items:
            if item.session_id == session_id:
                item.setParent(None)
                item.deleteLater()
                self._session_items.remove(item)
                break
