from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from ui.theme import (
    MANTLE, BASE, SURFACE0, SURFACE1, SURFACE2, GREEN, RED,
    TEXT, SUBTEXT0, SUBTEXT1, OVERLAY0, OVERLAY1, FONT_SANS,
)
from models.session import Session


class SessionTab(QFrame):
    clicked = pyqtSignal(int)
    close_clicked = pyqtSignal(int)

    def __init__(self, session: Session, active: bool = False, parent=None):
        super().__init__(parent)
        self.session_id = session.id
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = active
        self._hovered = False
        self.setFixedHeight(38)
        self._max_label_width = 160

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 10, 0)
        layout.setSpacing(6)

        self._name = QLabel(session.name)
        self._name.setMaximumWidth(self._max_label_width)
        layout.addWidget(self._name)

        self._close_btn = QLabel("×")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.mousePressEvent = lambda e: self.close_clicked.emit(self.session_id)
        layout.addWidget(self._close_btn)

        self._update_style()
        self._name.setText(self._elide(session.name))

    def _update_style(self):
        if self._active:
            bg = SURFACE0
            name_color = TEXT
            weight = "600"
            bottom_border = GREEN
            close_visible = True
            close_color = OVERLAY0
        elif self._hovered:
            bg = f"rgba(49, 50, 68, 0.6)"
            name_color = SUBTEXT1
            weight = "400"
            bottom_border = "transparent"
            close_visible = True
            close_color = OVERLAY0
        else:
            bg = "transparent"
            name_color = OVERLAY1
            weight = "400"
            bottom_border = "transparent"
            close_visible = False
            close_color = "transparent"

        self.setStyleSheet(f"""
            SessionTab {{
                background: {bg};
                border-bottom: 2px solid {bottom_border};
                border-radius: 8px 8px 0 0;
                margin-right: 2px;
                margin-left: 2px;
                margin-top: 4px;
            }}
        """)
        self._name.setStyleSheet(f"""
            font-size: 12px;
            color: {name_color};
            font-weight: {weight};
            background: transparent;
        """)
        self._close_btn.setVisible(close_visible)
        self._close_btn.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {close_color};
                border-radius: 4px;
                background: transparent;
            }}
            QLabel:hover {{
                background: {SURFACE1};
                color: {RED};
            }}
        """)

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _elide(self, text: str) -> str:
        metrics = QFontMetrics(self._name.font())
        return metrics.elidedText(text, Qt.TextElideMode.ElideRight, self._max_label_width)

    def update_label(self, name: str):
        self._name.setText(self._elide(name))

    def enterEvent(self, event):
        self._hovered = True
        self._update_style()

    def leaveEvent(self, event):
        self._hovered = False
        self._update_style()

    def mousePressEvent(self, event):
        self.clicked.emit(self.session_id)


class SessionTabBar(QFrame):
    tab_clicked = pyqtSignal(int)
    tab_close = pyqtSignal(int)
    new_tab = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            SessionTabBar {{
                background: {MANTLE};
                border-bottom: 1px solid {SURFACE0};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 6, 0)
        layout.setSpacing(0)

        self._tab_container = QHBoxLayout()
        self._tab_container.setContentsMargins(0, 0, 0, 0)
        self._tab_container.setSpacing(0)
        self._tab_container.addStretch()
        layout.addLayout(self._tab_container, 1)

        # Add button
        new_btn = QPushButton("+")
        new_btn.setFixedSize(30, 30)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {OVERLAY0};
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-family: {FONT_SANS};
            }}
            QPushButton:hover {{
                color: {GREEN};
                background: {SURFACE0};
            }}
        """)
        new_btn.clicked.connect(self.new_tab.emit)
        layout.addWidget(new_btn)

        self._tabs: list[SessionTab] = []

    def set_sessions(self, sessions: list[Session], active_id: int):
        for tab in self._tabs:
            tab.setParent(None)
            tab.deleteLater()
        self._tabs.clear()

        for sess in sessions:
            tab = SessionTab(sess, active=(sess.id == active_id))
            tab.clicked.connect(self.tab_clicked.emit)
            tab.close_clicked.connect(self.tab_close.emit)
            self._tabs.append(tab)
            self._tab_container.insertWidget(self._tab_container.count() - 1, tab)

    def update_active(self, active_id: int):
        for tab in self._tabs:
            tab.set_active(tab.session_id == active_id)

    def update_tab_label(self, session_id: int, name: str):
        for tab in self._tabs:
            if tab.session_id == session_id:
                tab.update_label(name)
                break
