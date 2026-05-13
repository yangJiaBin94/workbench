import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedEvent:
    type: str  # "assistant", "user", "system", "tool_use", "tool_result", "error"
    data: dict = field(default_factory=dict)
    partial: bool = False


class OutputParser:
    """Parse claude --output-format stream-json stdout line by line."""

    @staticmethod
    def parse_line(line: str) -> Optional[ParsedEvent]:
        line = line.strip()
        if not line:
            return None
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            return None

        event_type = obj.get("type", "")
        partial = obj.get("is_partial", False)
        data = obj

        return ParsedEvent(type=event_type, data=data, partial=partial)
