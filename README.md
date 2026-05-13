# 个人工作台 (Personal Workbench)

将 Claude Code 从命令行交互转变为 GUI 对话框交互的桌面应用。

## 技术栈

- **UI**: PyQt6
- **数据库**: SQLite (WAL)
- **后端**: Claude Code CLI (stream-json)

## 安装与运行

### 环境要求

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

### 安装依赖

```bash
pip install PyQt6>=6.5
```

### 启动

```bash
python main.py
```

## 功能

- 多会话标签页管理
- 流式对话展示（支持 Markdown 渲染）
- 思考过程折叠展示
- 工具调用可视化（读取文件、执行命令、网络搜索等，展示具体操作的文件/URL）
- 文件拖放输入
- 会话历史持久化

## 项目结构

```
main.py                         # 入口
models/
  session.py                    # Session, Message 数据模型
  project.py                    # ProjectConfig
services/
  session_store.py              # SQLite CRUD
  claude_process.py             # QProcess 封装 claude 子进程
  output_parser.py              # stream-json 行解析
ui/
  theme.py                      # Catppuccin Mocha 配色
  main_window.py                # 主窗口，信号/槽连接
  tool_sidebar.py               # 左侧历史会话导航
  session_tabs.py               # 顶部标签页栏
  chat_panel.py                 # 消息列表（滚动区域）
  input_panel.py                # 底部输入框 + 文件拖放
  message_widgets.py            # 消息泡泡 / 工具卡片 / 思考块
utils/
  ansi.py                       # ANSI 转义序列清理
```

## 许可

MIT
