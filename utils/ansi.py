import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
OSC_RE = re.compile(r"\x1b\].*?(\x1b\\|\x07)")


def clean_ansi(text: str) -> str:
    """Remove ANSI escape sequences and OSC sequences from text."""
    text = ANSI_RE.sub("", text)
    text = OSC_RE.sub("", text)
    return text
