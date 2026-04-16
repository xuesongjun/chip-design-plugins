# dft-toolkit

**Status:** Planned
**Tracking:** See [ROADMAP.md](../../ROADMAP.md)

## 计划功能

- Scan 链插入辅助（scan-ready 编码检查、违例识别）
- ATPG 向量分析（故障覆盖率报告解读）
- JTAG 接口检查（TAP controller 规范校验）
- DFT 规则检查（clock gating、reset、memory BIST 接口）
- MBIST wrapper 模板生成

## 为什么现在不做

DFT 流程高度依赖 EDA 工具（Synopsys DFT Compiler / Cadence Modus），
纯代码分析能覆盖的范围有限。需要先评估哪些检查可以在 Claude Code 层面有效实现，
哪些应该交给 EDA 工具。

如有需求或建议，欢迎提 issue。
