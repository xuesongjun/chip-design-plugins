# hdl-toolkit

HDL 开发综合工具。覆盖 Verilog/SystemVerilog 编码规范、CDC 检查、综合前检查、项目脚手架、文件保护。

## 命令

| 命令 | 说明 | 触发方式 |
|------|------|---------|
| `/hdl-toolkit:init [路径]` | 初始化新 IC 项目目录结构 | 手动 |
| `/hdl-toolkit:new-fsm` | 生成三段式 FSM 模板 | 手动 |
| `/hdl-toolkit:cdc-check [文件]` | CDC 路径安全检查 | 手动 |
| `/hdl-toolkit:style-check [文件]` | HDL 编码规范检查 | 手动 |
| `/hdl-toolkit:pre-syn-check [文件]` | 综合前代码质量检查 | 手动 |

## 自动加载的 Skills

| Skill | 触发方式 |
|-------|---------|
| `coding-style` | 编辑 `.v`/`.sv`/`.svh`/`.vh` 文件时自动加载 |

`coding-style` 包含完整的 HDL 编码规范（命名约定、FSM 三段式、CDC 处理、可综合性等）。Claude 编写或修改 HDL 代码时自动应用这些规则。

## Hooks

| Hook | 触发时机 | 功能 |
|------|---------|------|
| `check-locked` | Edit/Write/MultiEdit 之前 | 阻止修改包含 `// CLAUDE-LOCKED` 标记的文件 |

### 使用文件保护

在不希望被 Claude 修改的关键文件（已 release 的 golden RTL、IP 核源码、综合脚本）头部 20 行内任意位置加上注释：

```verilog
// CLAUDE-LOCKED
// Golden RTL, do not modify
module axi_master(
    ...
);
```

之后 Claude 试图 Edit/Write 该文件时会被自动阻止。需要修改时手动移除该标记即可。

## 项目初始化

`/hdl-toolkit:init` 会创建标准 IC 项目结构：

```
your-ic-project/
├── CLAUDE.md           # 项目级配置
├── process.txt         # 变更日志
├── .gitignore
├── rtl/                # RTL 源码
├── tb/                 # Testbench
├── syn/                # 综合脚本和约束
├── sim/                # 仿真脚本
├── doc/                # 设计文档
└── scripts/            # 辅助脚本
```

可指定路径：`/hdl-toolkit:init /path/to/new-project`，不指定则在当前目录初始化。

## 编码规范要点

完整规范见 `skills/coding-style/SKILL.md`，核心约定：

- 缩进 4 空格，`begin` 与块同行
- 时钟 `xxx_clk` / 门控时钟 `xxx_gclk` / 异步复位 `xxx_rstn` / 同步复位 `xxx_rstn_sync`
- 异步复位、同步释放
- FSM 必须三段式
- CDC 路径必须经过同步处理（单 bit 用同步器，多 bit 用握手或异步 FIFO）

## 依赖

无外部工具依赖。所有功能均通过 Python 脚本和 Claude 的代码分析实现。
