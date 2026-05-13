from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    id: Optional[int] = None
    name: str = ""
    working_dir: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Message:
    id: Optional[int] = None
    session_id: Optional[int] = None
    role: str = ""  # "user" | "assistant" | "system"
    content: str = ""
    event_type: Optional[str] = None  # "text" | "tool_call" | "tool_result" | "thinking"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
