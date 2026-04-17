---
description: Verilog/SystemVerilog HDL 编码规范。编写、修改、审查 .v / .sv / .svh / .vh 文件时自动加载。涉及 RTL 设计、testbench 编写、HDL 代码风格检查时使用。
---

# HDL 编码规范（Verilog/SystemVerilog）

## 格式

- 缩进：4 空格，禁止 tab
- `begin` 与块语句同行，前加空格，不换行
- `module`、`always`、`assign`、`generate` 等结构之间空一行

```verilog
always @(posedge ahb_gclk or negedge ahb_rstn) begin
    ...
end
```

## 命名规范

| 类别 | 格式 | 示例 |
|------|------|------|
| 时钟 | `xxx_clk` | `ahb_clk` |
| 门控时钟 | `xxx_gclk` | `ahb_gclk` |
| 时钟门控使能 | `xxx_gclken` | `ahb_gclken` |
| 异步复位（低有效） | `xxx_rstn` | `ahb_rstn` |
| 同步复位 | `xxx_rstn_sync` | `ahb_rstn_sync` |
| 组合逻辑输出 | `xxx_d` | `state_d` |
| 寄存器输出 | `xxx_q` | `state_q` |
| 低有效信号 | `xxx_n` | `cs_n` |
| 参数/宏 | 全大写下划线 | `DATA_WIDTH` |
| 模块名 | 小写下划线，与文件名一致 | `ahb_decoder` → `ahb_decoder.v` |

## 可综合性

- RTL 只使用可综合语法，禁止 `#delay`、`initial`、`force`/`release`、`$display`
- 禁止 latch：`if-else` 和 `case` 必须覆盖所有分支，`case` 加 `default`
- 禁止同一 `always` 块中混合阻塞和非阻塞赋值
- 组合逻辑用 `always @(*)` 或 `always_comb`，时序逻辑用 `always @(posedge clk ...)` 或 `always_ff`

## 复位策略

异步复位、同步释放。复位同步器至少两级触发器。

```verilog
always @(posedge xxx_gclk or negedge xxx_rstn) begin
    if (!xxx_rstn) begin
        // 异步复位
    end else begin
        // 正常逻辑
    end
end
```

## 状态机（三段式 FSM）

必须严格使用三段式：状态寄存器 / 次态组合逻辑 / 输出逻辑分离。

```verilog
localparam S_IDLE = 3'd0;
localparam S_WORK = 3'd1;
localparam S_DONE = 3'd2;

reg [2:0] state_q, state_d;

// 第一段：状态寄存器
always @(posedge xxx_gclk or negedge xxx_rstn) begin
    if (!xxx_rstn)
        state_q <= S_IDLE;
    else
        state_q <= state_d;
end

// 第二段：次态组合逻辑
always @(*) begin
    state_d = state_q;
    case (state_q)
        S_IDLE: if (start) state_d = S_WORK;
        S_WORK: if (done)  state_d = S_DONE;
        S_DONE: state_d = S_IDLE;
        default: state_d = S_IDLE;
    endcase
end

// 第三段：输出逻辑
always @(*) begin
    busy = (state_q == S_WORK);
end
```

需要快速生成符合规范的 FSM 模板时，使用 `/hdl-toolkit:new-fsm`。

## 跨时钟域（CDC）

- 单 bit 信号：至少两级同步器
- 多 bit 信号：格雷码 / 异步 FIFO / 握手协议，禁止直接同步
- CDC 路径必须在注释中标注源和目标时钟域
- 新增多时钟域逻辑时，plan.md 中列出所有 CDC 路径并评估安全性

## Testbench

- Testbench 与 RTL 分离，放在 `tb/` 或 `sim/` 目录
- Testbench 可使用不可综合语法
- 激励生成和结果检查逻辑分开
