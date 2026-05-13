from dataclasses import dataclass
import json
from PyQt6.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QShortcut, QKeySequence
from models.session import Session, Message
from models.project import ProjectConfig
from services.session_store import SessionStore
from services.claude_process import ClaudeProcess
from services.output_parser import OutputParser, ParsedEvent
from ui.tool_sidebar import ToolSidebar
from ui.chat_panel import ChatPanel
from ui.session_tabs import SessionTabBar
from ui.input_panel import InputPanel
from ui.theme import GLOBAL_STYLE


@dataclass
class _StreamState:
    streaming_msg_id: int | None = None
    streaming_text: str = ""
    thinking_text: str = ""
    current_block_type: str = ""
    tool_name: str = ""
    tool_input_json: str = ""


class MainWindow(QMainWindow):
    def __init__(self, config: ProjectConfig):
        super().__init__()
        self.setWindowTitle("个人工作台")
        self.resize(1100, 750)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(GLOBAL_STYLE)

        self.config = config
        self.store = SessionStore(config.data_dir)
        self.parser = OutputParser()

        self._active_session: Session | None = None
        self._processes: dict[int, ClaudeProcess] = {}
        self._states: dict[int, _StreamState] = {}
        self._open_ids: set[int] = set()

        self._build_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._restore_sessions()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = ToolSidebar()
        root.addWidget(self.sidebar)

        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = SessionTabBar()
        main_layout.addWidget(self.tabs)

        self.chat = ChatPanel()
        main_layout.addWidget(self.chat, 1)

        self.input_panel = InputPanel()
        main_layout.addWidget(self.input_panel)

        root.addWidget(main_area, 1)

    def _connect_signals(self):
        self.tabs.tab_clicked.connect(self._on_tab_clicked)
        self.tabs.tab_close.connect(self._on_tab_close)
        self.tabs.new_tab.connect(self._on_new_tab)
        self.input_panel.send_message.connect(self._on_user_message)
        self.sidebar.session_clicked.connect(self._on_sidebar_session_clicked)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._on_new_tab)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(
            lambda: self._on_tab_close(self._active_session.id) if self._active_session else None
        )

    # ---- per-session process management ----

    def _state(self, sid: int) -> _StreamState:
        if sid not in self._states:
            self._states[sid] = _StreamState()
        return self._states[sid]

    def _get_or_start_process(self, session_id: int, working_dir: str) -> ClaudeProcess:
        if session_id in self._processes:
            proc = self._processes[session_id]
            if proc.is_running():
                return proc
            # Process died, remove and recreate
            proc.deleteLater()
            del self._processes[session_id]

        proc = ClaudeProcess(self)
        proc.session_id = session_id
        proc.output_line.connect(self._on_claude_output)
        proc.process_error.connect(self._on_claude_error)
        proc.process_finished.connect(self._on_claude_finished)
        proc.start(working_dir=working_dir)
        self._processes[session_id] = proc
        return proc

    def _stop_session_process(self, session_id: int):
        proc = self._processes.pop(session_id, None)
        if proc:
            proc.output_line.disconnect(self._on_claude_output)
            proc.process_error.disconnect(self._on_claude_error)
            proc.process_finished.disconnect(self._on_claude_finished)
            proc.stop()

    # ---- session management ----

    def _restore_sessions(self):
        sessions = self.store.list_sessions()
        if sessions:
            recent = self.store.get_recent_sessions(10)
            self._open_ids = {recent[0].id}
            self._refresh_tabs()
            self._refresh_sidebar()
            self._switch_session(recent[0])
        else:
            sess = self.store.create_session()
            self._active_session = sess
            self._open_ids = {sess.id}
            self._refresh_tabs()
            self._refresh_sidebar()
            self.chat.show_empty_state()

    def _refresh_tabs(self):
        all_sessions = {s.id: s for s in self.store.list_sessions()}
        open_sessions = [all_sessions[sid] for sid in self._open_ids if sid in all_sessions]
        active_id = self._active_session.id if self._active_session else None
        self.tabs.set_sessions(open_sessions, active_id)

    @pyqtSlot(int)
    def _on_tab_clicked(self, session_id: int):
        if self._active_session and self._active_session.id == session_id:
            return
        sess = self.store.get_session(session_id)
        if sess:
            self._switch_session(sess)

    @pyqtSlot(int)
    def _on_tab_close(self, session_id: int):
        if len(self._open_ids) <= 1:
            return
        self._open_ids.discard(session_id)
        self._stop_session_process(session_id)
        self._states.pop(session_id, None)

        if self._active_session and self._active_session.id == session_id:
            all_sessions = {s.id: s for s in self.store.list_sessions()}
            remaining = [all_sessions[sid] for sid in self._open_ids if sid in all_sessions]
            if remaining:
                self._switch_session(remaining[0])
            else:
                sess = self.store.create_session()
                self._open_ids.add(sess.id)
                self._switch_session(sess)
        else:
            self._refresh_tabs()
        self._refresh_sidebar()

    @pyqtSlot()
    def _on_new_tab(self):
        sess = self.store.create_session()
        self._open_ids.add(sess.id)
        self._switch_session(sess)
        self._refresh_sidebar()

    def _switch_session(self, session: Session):
        # Don't stop the old process — keep it running in background
        self._active_session = session
        self._refresh_tabs()
        self.sidebar.set_active(session.id)

        messages = self.store.get_messages(session.id)
        if messages:
            self.chat.restore_messages(messages)
            # If this session has an active streaming state, show the partial bubble
            state = self._state(session.id)
            if state.streaming_msg_id is not None and state.streaming_text:
                self.chat.add_or_update_assistant_bubble(state.streaming_msg_id)
                bubble = self.chat._bubble_map.get(state.streaming_msg_id)
                if bubble:
                    bubble.append_text(state.streaming_text)
        else:
            self.chat.show_empty_state()

    def _refresh_sidebar(self):
        sessions = self.store.get_recent_sessions(10)
        active_id = self._active_session.id if self._active_session else None
        self.sidebar.set_sessions(sessions, active_id)

    @pyqtSlot(int)
    def _on_sidebar_session_clicked(self, session_id: int):
        if self._active_session and self._active_session.id == session_id:
            return
        sess = self.store.get_session(session_id)
        if sess:
            self._open_ids.add(session_id)
            self._switch_session(sess)

    # ---- user input ----

    @pyqtSlot(str)
    def _on_user_message(self, text: str):
        if not self._active_session:
            return

        sid = self._active_session.id

        # Rename session on first user message
        if self._active_session.name == "新会话":
            first_line = text.split("\n")[0].strip()
            if len(first_line) > 50:
                first_line = first_line[:50] + "..."
            self._active_session.name = first_line
            self.store.update_session_name(sid, first_line)
            self.tabs.update_tab_label(sid, first_line)
            self.sidebar.update_session_name(sid, first_line)

        state = self._state(sid)
        state.streaming_msg_id = None
        state.streaming_text = ""

        proc = self._get_or_start_process(sid, self._active_session.working_dir)

        msg = Message(session_id=sid, role="user", content=text, event_type="text")
        self.store.save_message(msg)
        self.chat.add_user_bubble(text)
        proc.send_message(text)

    # ---- claude output (routed by session_id) ----

    @pyqtSlot(str)
    def _on_claude_output(self, line: str):
        proc = self.sender()
        if not isinstance(proc, ClaudeProcess):
            return
        sid = getattr(proc, "session_id", None)
        if sid is None:
            return

        event = self.parser.parse_line(line)
        if event is None:
            return
        self._dispatch_event(sid, event)

    def _dispatch_event(self, sid: int, event: ParsedEvent):
        etype = event.type
        data = event.data
        state = self._state(sid)
        is_active = self._active_session and self._active_session.id == sid

        if etype == "system":
            subtype = data.get("subtype", "")
            if subtype == "status" and data.get("status") == "requesting":
                if is_active:
                    self.chat.show_typing()

        elif etype == "stream_event":
            inner = data.get("event", {})
            inner_type = inner.get("type", "")

            if inner_type == "message_start":
                state.streaming_msg_id = None
                state.streaming_text = ""
                state.thinking_text = ""
                state.current_block_type = ""

            elif inner_type == "content_block_start":
                block = inner.get("content_block", {})
                block_type = block.get("type", "")
                state.current_block_type = block_type

                if block_type == "thinking":
                    state.thinking_text = ""
                elif block_type == "text":
                    state.streaming_text = ""
                    if is_active and state.thinking_text:
                        self.chat.add_thinking(state.thinking_text)
                        self.store.save_message(Message(
                            session_id=sid, role="assistant",
                            content=state.thinking_text, event_type="thinking",
                        ))
                    state.thinking_text = ""
                elif block_type == "tool_use":
                    state.streaming_text = ""
                    state.tool_name = block.get("name", "")
                    state.tool_input_json = ""

            elif inner_type == "content_block_delta":
                delta = inner.get("delta", {})
                delta_type = delta.get("type", "")

                if delta_type == "thinking_delta":
                    state.thinking_text += delta.get("thinking", "")

                elif delta_type == "input_json_delta":
                    state.tool_input_json += delta.get("partial_json", "")

                elif delta_type == "text_delta":
                    text = delta.get("text", "")
                    state.streaming_text += text
                    if state.streaming_msg_id is None:
                        msg = Message(
                            session_id=sid, role="assistant",
                            content="", event_type="text",
                        )
                        state.streaming_msg_id = self.store.save_message(msg)
                        if is_active:
                            self.chat.add_or_update_assistant_bubble(state.streaming_msg_id)
                    if is_active:
                        bubble = self.chat._bubble_map.get(state.streaming_msg_id)
                        if bubble:
                            bubble.append_text(text)

            elif inner_type == "content_block_stop":
                if state.current_block_type == "text":
                    self._finalize_text_state(sid)
                elif state.current_block_type == "tool_use" and state.tool_name:
                    params = {}
                    if state.tool_input_json:
                        try:
                            params = json.loads(state.tool_input_json)
                        except json.JSONDecodeError:
                            pass
                    if is_active:
                        self.chat.add_tool_card(state.tool_name, params=params)
                        self.store.save_message(Message(
                            session_id=sid, role="assistant",
                            content=json.dumps({"name": state.tool_name, "params": params}, ensure_ascii=False),
                            event_type="tool_call",
                        ))
                    state.tool_name = ""
                    state.tool_input_json = ""
                state.current_block_type = ""

            elif inner_type in ("message_delta", "message_stop"):
                self._finalize_text_state(sid)

        elif etype == "result":
            self._finalize_text_state(sid)

        if is_active:
            self.chat._scroll_bottom()

    def _finalize_text_state(self, sid: int):
        state = self._state(sid)
        is_active = self._active_session and self._active_session.id == sid
        if state.streaming_msg_id is not None and state.streaming_text.strip():
            self.store.update_message(
                Message(id=state.streaming_msg_id, content=state.streaming_text)
            )
            if is_active:
                self.chat.finish_assistant_bubble(state.streaming_msg_id, state.streaming_text)
            state.streaming_msg_id = None
        state.streaming_text = ""

    @pyqtSlot(str)
    def _on_claude_error(self, error: str):
        proc = self.sender()
        sid = getattr(proc, "session_id", None) if isinstance(proc, ClaudeProcess) else None
        is_active = sid and self._active_session and self._active_session.id == sid
        if is_active and error.strip():
            self.chat.add_assistant_bubble(f"⚠️ {error.strip()}")

    @pyqtSlot(int)
    def _on_claude_finished(self, exit_code: int):
        proc = self.sender()
        if isinstance(proc, ClaudeProcess):
            sid = getattr(proc, "session_id", None)
            if sid:
                self._finalize_text_state(sid)
                # Remove dead process so it gets recreated on next message
                if sid in self._processes:
                    self._processes[sid].deleteLater()
                    del self._processes[sid]

    def closeEvent(self, event):
        self.hide()
        for proc in list(self._processes.values()):
            proc.stop()
        self._processes.clear()
        self.store.close()
        super().closeEvent(event)
