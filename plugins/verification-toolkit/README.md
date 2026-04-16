# verification-toolkit

**Status:** Planned
**Tracking:** See [ROADMAP.md](../../ROADMAP.md)

## 计划功能

- UVM testbench 模板生成（agent/sequence/scoreboard 骨架）
- Coverage 分析助手（功能覆盖率/代码覆盖率报告解读）
- 回归脚本生成（VCS/Xcelium 通用）
- Lint warning 抑制管理
- Assertion 模板（SVA 常用 pattern）

## 为什么现在不做

需要先充分验证 hdl-toolkit 的 skill 设计模式，确保 CDC 检查、风格检查等 skill 在实际项目中有效。
验证领域的工具链差异大（UVM vs OSVVM vs cocotb），需要先调研目标用户的主要工作流。

如有需求或建议，欢迎提 issue。
