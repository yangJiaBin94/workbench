# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

个人工作台 — 将 Claude Code 从 CLI 命令行交互转变为 GUI 对话框交互的桌面应用。

**技术栈:** PyQt6 + SQLite (WAL) + claude CLI (stream-json 多轮对话)

## 运行

```bash
pip install PyQt6>=6.5
python main.py
```

## 架构

```
main.py                      # 入口
models/
  session.py                 # Session, Message dataclass
  project.py                 # ProjectConfig dataclass
services/
  session_store.py           # SQLite CRUD（sessions + messages 两张表）
  claude_process.py          # QProcess 封装 claude 子进程（stream-json 模式）
  output_parser.py           # stream-json 行解析 → ParsedEvent
ui/
  theme.py                   # Catppuccin Mocha 配色常量 + 全局 QSS
  main_window.py             # 主窗口，组装所有组件，连接信号/槽
  tool_sidebar.py            # 左侧工作台工具导航
  session_tabs.py            # 顶部会话标签页栏
  chat_panel.py              # 消息列表（QScrollArea），包含流式渲染
  input_panel.py             # 底部输入框 + 发送 + 文件拖放
  message_widgets.py         # UserBubble / AssistantBubble / ToolCallCard / ThinkingBlock
utils/
  ansi.py                    # ANSI 转义序列清理
```

## 核心数据流

1. `InputPanel.send_message` → `MainWindow._on_user_message()` → `SessionStore.save_message()` + `ChatPanel.add_user_bubble()` + `ClaudeProcess.send_message()` (stream-json stdin)
2. `ClaudeProcess.output_line` → `OutputParser.parse_line()` → `MainWindow._dispatch_event()` → 根据事件类型更新 UI + `SessionStore.save_message()`

## ClaudeProcess 启动参数

```
--print --verbose --output-format stream-json --input-format stream-json --include-partial-messages --permission-mode acceptEdits
```

## Stream-json 事件类型

| type | 处理 |
|------|------|
| `system/subtype=init` | 会话初始化（静默） |
| `system/subtype=status` | 显示 typing 指示器 |
| `stream_event/content_block_start:thinking` | 开始思考块 |
| `stream_event/content_block_start:text` | 开始文本块，展示已累积的思考 |
| `stream_event/content_block_delta:thinking_delta` | 累积思考文本 |
| `stream_event/content_block_delta:text_delta` | 流式追加到 assistant bubble |
| `stream_event/message_delta:end_turn` | 结束当前回复轮次 |
| `result` | 最终确认 |

## stdin 格式

`{"type":"user","message":{"role":"user","content":"..."}}\n`
