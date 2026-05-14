# 个人工作台 (Personal Workbench)

将 Claude Code 从命令行交互转变为 GUI 对话框交互的桌面应用。

## 技术栈

- **UI**: PyQt6
- **数据库**: SQLite (WAL)
- **后端**: Claude Code CLI (stream-json)

## 安装与运行

### 环境要求

- **Python** 3.10+
- **Node.js** 18+（Claude Code CLI 运行所需）
- **Claude Code CLI**（需预先安装并确保 `claude` 命令可在终端中直接调用）

---

### 1. 安装 Python

**Windows**

从 [python.org](https://www.python.org/downloads/) 下载安装包，安装时**勾选 "Add Python to PATH"**。

安装完成后验证：

```powershell
python --version
```

**macOS**

```bash
# 通过 Homebrew 安装
brew install python@3.12
```

**Linux (Ubuntu/Debian)**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

### 2. 安装 Node.js

Claude Code CLI 基于 Node.js 运行，需先安装 Node.js 18+。

**Windows**

从 [nodejs.org](https://nodejs.org/) 下载 LTS 版本安装包（安装时勾选 "Automatically install the necessary tools"）。

安装完成后验证：

```powershell
node --version
npm --version
```

**macOS**

```bash
brew install node
```

**Linux (Ubuntu/Debian)**

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

### 3. 安装 Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

安装完成后验证：

```bash
claude --version
```

首次使用需完成登录认证，按照终端提示操作即可。

---

### 4. 克隆项目并安装 Python 依赖

```bash
git clone <项目地址> workbench
cd workbench
pip install PyQt6>=6.5
```

---

### 5. 启动

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
