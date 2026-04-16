# backend-toolkit

**Status:** Planned
**Tracking:** See [ROADMAP.md](../../ROADMAP.md)

## 计划功能

- 综合脚本模板（DC / Genus 常用 flow）
- SDC 约束生成与检查（时钟定义、IO 约束、false path / multicycle path）
- PnR 约束生成（floorplan 辅助、placement 约束）
- STA 报告分析（timing violation 解读、critical path 定位）
- 寄生提取结果检查（RC 异常值识别）
- Power 分析报告解读

## 为什么现在不做

后端流程强依赖 EDA 工具的输出格式（DC/ICC2/Innovus/Genus/Tempus），
需要先收集实际项目的报告样本，定义解析规则。
SDC 约束检查是最有可能先实现的功能，因为 SDC 是文本格式且规则明确。

如有需求或建议，欢迎提 issue。
