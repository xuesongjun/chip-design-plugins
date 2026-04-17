---
description: 检查 RTL 代码中的跨时钟域（CDC）路径安全性
disable-model-invocation: true
---

# CDC 路径安全检查

对用户指定的 RTL 文件、目录或当前项目执行跨时钟域路径检查。

## 执行步骤

1. **确定检查范围**
   - 如果用户提供了路径参数 `$ARGUMENTS`，对该路径执行检查
   - 如果没有提供，询问用户：检查整个 `rtl/` 目录还是某个具体文件
   - 使用 Glob 找出所有 `.v` / `.sv` / `.svh` 文件

2. **识别时钟域**
   - 扫描所有 `always @(posedge ...)` 块，提取时钟信号
   - 按命名规范 `xxx_clk` / `xxx_gclk` 区分不同时钟域
   - 列出本次检查涉及的所有时钟域

3. **执行 CDC 检查**

   对每个跨时钟域信号检查以下项目：

   | 检查项 | 风险等级 | 说明 |
   |--------|---------|------|
   | 单 bit 跨域无同步器 | CRITICAL | 必须经过至少两级触发器同步 |
   | 多 bit 跨域直接同步 | CRITICAL | 必须用格雷码/异步 FIFO/握手协议 |
   | 同步器中间信号被使用 | WARNING | 仅最终输出可用 |
   | 复位无同步释放 | CRITICAL | 异步复位必须同步释放 |
   | CDC 路径无注释标注 | INFO | 应注明源/目标时钟域 |
   | 同步器位于组合逻辑路径上 | WARNING | 应紧跟时序逻辑 |

4. **输出报告**

   按文件分组，格式如下：

   ```
   === CDC 检查报告 ===

   涉及时钟域：
   - ahb_gclk (来自 rtl/ahb_top.v)
   - axi_clk  (来自 rtl/axi_master.v)

   ---

   文件: rtl/bridge.v

   [CRITICAL] 第 45 行
     信号 'data_in' 从 axi_clk 域直接进入 ahb_gclk 域，未经同步处理
     建议: 多 bit 数据应通过异步 FIFO 或握手协议传输

   [WARNING] 第 78 行
     同步器中间信号 'sync_meta' 被组合逻辑使用
     建议: 仅使用最终输出 'sync_out'

   [INFO] 第 92 行
     CDC 路径未注释源/目标时钟域
     建议: 添加注释 // CDC: axi_clk -> ahb_gclk

   ---

   总结: 1 CRITICAL / 1 WARNING / 1 INFO
   ```

5. **后续动作**

   - 如果有 CRITICAL 问题，强烈建议用户在 plan.md 中规划修复
   - 询问用户是否需要为某个具体问题给出代码修复建议
   - 如有大量问题，建议先修 CRITICAL，再逐步处理 WARNING 和 INFO
