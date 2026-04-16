# ip-toolkit

**Status:** Planned
**Tracking:** See [ROADMAP.md](../../ROADMAP.md)

## 计划功能

- 寄存器自动生成（基于 YAML / SystemRDL / Excel 描述，输出 RTL + 文档 + 头文件）
- IP 接口适配器生成（AXI ↔ APB、AXI ↔ AHB 等总线桥接模板）
- IP 集成检查（端口连接完整性、参数一致性）
- IP 文档模板（接口说明、时序图、寄存器表）
- AMBA 协议合规检查（AXI4 / AHB / APB 信号规范校验）

## 为什么现在不做

寄存器自动生成涉及多种输入格式（YAML / SystemRDL / IP-XACT / Excel），
需要先确定目标格式并实现解析器。IP 集成检查需要理解项目的模块层次，
依赖对项目结构的深入了解。

如有需求或建议，欢迎提 issue。
