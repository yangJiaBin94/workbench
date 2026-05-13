# Catppuccin Mocha palette (refined)
CRUST  = "#11111b"
MANTLE = "#181825"
BASE   = "#1e1e2e"
SURFACE0 = "#313244"
SURFACE1 = "#45475a"
SURFACE2 = "#585b70"
OVERLAY0 = "#6c7086"
OVERLAY1 = "#7f849c"
OVERLAY2 = "#9399b2"
SUBTEXT0 = "#a6adc8"
SUBTEXT1 = "#bac2de"
TEXT     = "#cdd6f4"

# Accent — Layui-inspired green primary
GREEN  = "#4ade80"
GREEN_DARK = "#22c55e"
BLUE   = "#89b4fa"
TEAL   = "#94e2d5"
YELLOW = "#f9e2af"
RED    = "#f38ba8"
PEACH  = "#fab387"
MAUVE  = "#cba6f7"
PINK   = "#f5c2e7"

FONT_SANS  = '"Segoe UI", "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif'
FONT_MONO  = '"Cascadia Code", "JetBrains Mono", "SF Mono", "Fira Code", "Consolas", monospace'

# ── global stylesheet ──────────────────────────────────────────────
GLOBAL_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BASE};
    color: {TEXT};
    font-family: {FONT_SANS};
    font-size: 13px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

/* ── scrollbar ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE1};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {SURFACE2};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    height: 0;
}}

/* ── tool-tip ── */
QToolTip {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""
