# chip-design-plugins

芯片设计 Claude Code 插件集（marketplace 名：`chip-design`）。

覆盖 HDL 编码规范、CDC 检查、综合前检查、Verible LSP 集成、MATLAB DSP 转 Verilog 等。未来规划验证、DFT、后端、IP 开发等方向，详见 [ROADMAP.md](ROADMAP.md)。

## 安装

```
/plugin marketplace add xuesongjun/chip-design-plugins
/plugin install hdl-toolkit@chip-design
/plugin install systemverilog-lsp@chip-design
```

`systemverilog-lsp` 需要预装 [Verible](https://github.com/chipsalliance/verible/releases) 并加入 PATH。`hdl-toolkit` 无外部依赖。

## 插件清单

### hdl-toolkit — HDL 开发综合工具

用户主动触发的所有 HDL 相关命令。

| 命令 | 说明 |
|------|------|
| `/hdl-toolkit:init [路径]` | 初始化 IC 项目目录结构（rtl/tb/syn/sim/doc/scripts） |
| `/hdl-toolkit:new-fsm` | 交互式生成三段式 FSM 模板 |
| `/hdl-toolkit:cdc-check [文件]` | 跨时钟域路径安全检查 |
| `/hdl-toolkit:style-check [文件]` | HDL 编码规范检查（命名、格式、赋值、FSM、复位） |
| `/hdl-toolkit:pre-syn-check [文件]` | 综合前代码质量检查（多驱动、位宽、组合环路） |
| `/hdl-toolkit:lint [文件]` | 全面代码审查（CDC + DFT + 低功耗 + 健壮性 + 可综合性） |
| `/hdl-toolkit:matlab2verilog` | MATLAB DSP 算法转可综合 Verilog（滤波器/FFT/混频器） |
| `/hdl-toolkit:format [文件]` | Verible 手动格式化 |

**自动加载：** `coding-style` skill 在编辑 `.v`/`.sv` 文件时自动加载编码规范，无需手动触发。

**文件保护 Hook：** 在文件头部 20 行内加 `// CLAUDE-LOCKED` 标记，可阻止 Claude 修改该文件。

```verilog
// CLAUDE-LOCKED
// Golden RTL, do not modify
module axi_master(...);
```

**编码规范要点：**
- 缩进 4 空格，`begin` 与块同行
- 时钟 `xxx_clk` / 门控时钟 `xxx_gclk` / 异步复位 `xxx_rstn` / 同步复位 `xxx_rstn_sync`
- 异步复位、同步释放
- FSM 必须三段式
- CDC 路径必须经过同步处理

### systemverilog-lsp — Verible LSP 集成

被动的自动化服务，提供代码智能和自动修复。

**LSP 功能：** 诊断、跳转定义、查找引用、格式化、代码大纲、重命名

**自动化 Hooks：**

| Hook | 触发时机 | 功能 |
|------|---------|------|
| verible-autofix | 编辑 `.v`/`.sv` 后 | 自动运行 `verible-verilog-lint --autofix=inplace` |
| verible-format | 编辑 `.v`/`.sv` 后 | 当项目有 `.verible-format` 且含 `# hook: on` 时自动格式化 |

**前提：** 需安装 [Verible](https://github.com/chipsalliance/verible/releases) 并加入 PATH。

详见 [plugins/systemverilog-lsp/README.md](plugins/systemverilog-lsp/README.md)。

### 两者协作

| 关注点 | hdl-toolkit | systemverilog-lsp |
|--------|-------------|-------------------|
| 定位 | 用户主动触发的命令 | 被动的自动化服务 |
| 格式化 | `/hdl-toolkit:format`（手动） | autoformat hook（自动） |
| Lint | `/hdl-toolkit:lint`（全面审查） | autofix hook（自动修可修复的） |
| 编码规范 | 语义级（命名、FSM、CDC） | 格式级（缩进、行宽、对齐） |
| LSP | 无 | Verible 语言服务器 |
| 依赖 | 无（format 除外） | Verible |

建议两个都装，互补使用。

## 规划中的插件

| Plugin | 说明 |
|--------|------|
| verification-toolkit | UVM testbench 模板、coverage 分析、回归脚本 |
| dft-toolkit | Scan 链、ATPG、JTAG 检查 |
| backend-toolkit | 综合脚本模板、SDC 约束、STA 报告分析 |
| ip-toolkit | 寄存器自动生成、IP 接口适配、AMBA 合规检查 |
| eda-scripts | EDA 工具统一接口（VCS/Xcelium/Verilator/DC） |

详见 [ROADMAP.md](ROADMAP.md)。

## 仓库结构

```
chip-design-plugins/
├── .claude-plugin/marketplace.json
├── README.md
├── ROADMAP.md
├── docs/
│   └── setup-dev-env.md
├── scripts/
│   └── setup-dev-env.ps1
└── plugins/
    ├── hdl-toolkit/                       v1.1.0
    │   ├── .claude-plugin/plugin.json
    │   ├── skills/
    │   │   ├── init/                      项目脚手架
    │   │   ├── coding-style/              编码规范（自动加载）
    │   │   ├── new-fsm/                   FSM 模板生成
    │   │   ├── cdc-check/                 CDC 检查
    │   │   ├── style-check/               风格检查
    │   │   ├── pre-syn-check/             综合前检查
    │   │   ├── lint/                      全面代码审查
    │   │   ├── matlab2verilog/            MATLAB → Verilog
    │   │   └── format/                    Verible 格式化
    │   └── hooks/
    │       ├── hooks.json
    │       └── check_locked.py            文件保护
    ├── systemverilog-lsp/                 v1.0.0
    │   ├── .claude-plugin/plugin.json     含 LSP 配置
    │   └── hooks/
    │       ├── hooks.json
    │       ├── verible-autofix.py
    │       └── verible-format.py
    ├── verification-toolkit/              占位
    ├── dft-toolkit/                       占位
    ├── backend-toolkit/                   占位
    ├── ip-toolkit/                        占位
    └── eda-scripts/                       占位
```

## Windows 环境配置

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/xuesongjun/chip-design-plugins/main/scripts/setup-dev-env.ps1" -OutFile "$env:TEMP\setup-dev-env.ps1"
& "$env:TEMP\setup-dev-env.ps1"
```

详见 [docs/setup-dev-env.md](docs/setup-dev-env.md)。

## 更新插件

```bash
# 终端清 cache
rm -rf ~/.claude/plugins/cache/chip-design

# Claude Code 中
/plugin marketplace update
/plugin install hdl-toolkit@chip-design
/plugin install systemverilog-lsp@chip-design
```

## 开发原则

1. 按"领域"分 plugin，不按"单功能"分
2. slash 命令前缀清晰，一眼看出归属
3. skills 用于用户主动触发，hooks 用于自动化（克制使用）
4. SKILL.md 不写 `name` 字段，由目录名 + plugin 前缀自动生成命令
5. 依赖最小化，优先用 Python 写脚本

## 贡献

欢迎提 issue 讨论新插件设计或直接 PR。