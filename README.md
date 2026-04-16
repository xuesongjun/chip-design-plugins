# chip-design-plugins

芯片设计 Claude Code 插件集（marketplace 名：`chip-design`）。覆盖前端设计、验证、DFT、后端、IP 开发等环节。

## 安装

### 第一步：添加 marketplace

在 Claude Code 中：

```
/plugin marketplace add xuesongjun/chip-design-plugins
```

### 第二步：按需安装插件

```
/plugin install hdl-toolkit@chip-design
/plugin install systemverilog-lsp@chip-design
```

## 插件清单

### 已发布

| Plugin | 命令前缀 | 说明 |
|--------|---------|------|
| [hdl-toolkit](plugins/hdl-toolkit/README.md) | `/hdl-toolkit:` | HDL 编码规范、CDC 检查、综合前检查、项目脚手架、文件保护 |
| [systemverilog-lsp](plugins/systemverilog-lsp/README.md) | `/systemverilog-lsp:` | Verible LSP 集成、自动格式化、lint autofix |

### 规划中

详见 [ROADMAP.md](ROADMAP.md)。

## 命令一览

### hdl-toolkit

| 命令 | 说明 |
|------|------|
| `/hdl-toolkit:init` | 初始化新 IC 项目目录结构 |
| `/hdl-toolkit:new-fsm` | 生成三段式 FSM 模板 |
| `/hdl-toolkit:cdc-check` | CDC 路径安全检查 |
| `/hdl-toolkit:style-check` | HDL 编码规范检查 |
| `/hdl-toolkit:pre-syn-check` | 综合前代码质量检查 |

`coding-style` skill 在编辑 `.v`/`.sv` 文件时自动加载，无需手动触发。
文件保护 hook 自动生效，标记 `// CLAUDE-LOCKED` 的文件不允许修改。

### systemverilog-lsp

| 命令 | 说明 |
|------|------|
| `/systemverilog-lsp:format` | 手动格式化 Verilog 文件 |

`autofix` 和 `autoformat` hook 自动生效。详见 plugin README。

## Windows 环境配置

如在 Windows 下使用，可运行一键配置脚本：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/xuesongjun/chip-design-plugins/main/scripts/setup-dev-env.ps1" -OutFile "$env:TEMP\setup-dev-env.ps1"
& "$env:TEMP\setup-dev-env.ps1"
```

详见 [docs/setup-dev-env.md](docs/setup-dev-env.md)。

## 开发原则

1. 按"领域"分 plugin，不按"单功能"分 — 避免 plugin 数量爆炸
2. slash 命令前缀清晰 — 一眼看出归属
3. skills 用于用户主动触发的动作，agents 用于复杂的独立任务
4. hooks 克制使用 — 只用于真正确定性的检查（如文件保护）
5. 依赖最小化 — 优先用 Python 等通用语言写脚本

## 贡献

欢迎提 issue 讨论新插件设计或直接 PR。
