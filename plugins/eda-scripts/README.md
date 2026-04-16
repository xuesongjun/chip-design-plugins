# eda-scripts

**Status:** Planned
**Tracking:** See [ROADMAP.md](../../ROADMAP.md)

## 计划功能

- 仿真器统一接口（VCS / Xcelium / ModelSim / Verilator 统一命令封装）
- 综合工具统一接口（DC / Genus 常用操作封装）
- 波形查看辅助（自动生成 do/tcl 脚本打开关键信号）
- Makefile / flow 脚本模板（仿真 + 综合 + lint 一体化）
- CI/CD 集成模板（GitLab CI / GitHub Actions 的芯片设计 pipeline）
- 日志分析（从 EDA 工具日志中提取 error/warning 摘要）

## 为什么现在不做

EDA 工具种类多、版本差异大、License 管理复杂，
需要先调研目标用户的主要工具组合（Synopsys / Cadence / Siemens / 开源），
再决定抽象层的设计。
Verilator 相关的功能可能最先实现，因为它是开源工具，无 License 限制。

如有需求或建议，欢迎提 issue。
