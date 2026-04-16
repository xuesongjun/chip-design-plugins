# Chip Design Plugins Roadmap

## 项目愿景

为芯片设计全流程提供 Claude Code 插件支持，覆盖前端设计、验证、DFT、后端、IP 开发等环节。

## 当前状态

| Plugin | 状态 | 版本 | 说明 |
|--------|------|------|------|
| hdl-toolkit | 已发布 | v1.0.0 | RTL 编码规范、CDC 检查、综合前检查、项目脚手架、文件保护 |
| systemverilog-lsp | 已发布 | v1.0.0 | Verible LSP 集成、自动格式化、lint autofix |

## 规划中

### 验证

| Plugin | 优先级 | 计划功能 |
|--------|--------|---------|
| verification-toolkit | 高 | UVM testbench 模板生成、coverage 分析助手、回归脚本生成 |

### DFT 与后端

| Plugin | 优先级 | 计划功能 |
|--------|--------|---------|
| dft-toolkit | 中 | Scan 链插入辅助、ATPG 向量分析、JTAG 接口检查 |
| backend-toolkit | 中 | 综合脚本模板（DC/Genus）、PnR 约束生成、STA 报告分析、寄生提取 |

### 生态扩展

| Plugin | 优先级 | 计划功能 |
|--------|--------|---------|
| ip-toolkit | 低 | 寄存器自动生成（基于 YAML/SystemRDL）、IP 接口适配 |
| eda-scripts | 低 | 各家 EDA 工具的脚本助手（VCS/Xcelium/Verilator/DC/Innovus 统一接口） |

## 设计原则

1. **按领域分 plugin，不按单功能分** — 避免 plugin 数量爆炸
2. **slash 命令前缀清晰** — 一眼看出归属
3. **文档与功能同步** — 每个 plugin 有自己的 README
4. **依赖最小化** — 优先用 Python 等通用语言写脚本
5. **占位 plugin 必须有 README** — 说明计划和当前不做的原因

## 贡献

如果你有兴趣实现某个 plugin，欢迎提 issue 讨论设计或直接 PR。
每个 plugin 应当遵循：
- 一个 plugin 一个明确的功能领域
- skills 用于用户主动触发的动作
- agents 用于复杂的独立任务
- hooks 用于自动化检查（克制使用）

## 历史变更

- 2026-04: 项目启动，发布 v1.0.0（hdl-toolkit + systemverilog-lsp）
