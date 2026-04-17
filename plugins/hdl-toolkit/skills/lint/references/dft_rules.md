# 可测性设计 (DFT) 规则

## 目录

1. [DFT 基础](#dft-基础)
2. [扫描设计规则](#扫描设计规则)
3. [时钟和复位处理](#时钟和复位处理)
4. [可观测性设计](#可观测性设计)
5. [检查清单](#检查清单)

---

## DFT 基础

### 为什么需要 DFT？

- **制造测试**: 检测生产缺陷 (stuck-at, bridging, etc.)
- **调试**: 芯片 bring-up 时定位问题
- **在线检测**: 运行时检测故障 (安全关键应用)

### 主要 DFT 技术

| 技术 | 目的 | 覆盖率影响 |
|------|------|------------|
| Scan Chain | 测试组合逻辑 | 高 |
| BIST (内建自测试) | 存储器测试 | 高 |
| JTAG | 边界扫描、调试 | 中 |
| Compression | 减少测试时间 | - |

---

## 扫描设计规则

### 扫描友好的代码

```verilog
// 好: 标准 D 触发器，易于扫描替换
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= 1'b0;
    else
        q <= d;
end

// 差: 组合反馈，不可扫描
always @(*) begin
    q = en ? d : q;  // 形成锁存器
end
```

### 避免的结构

| 结构 | 问题 | 解决方案 |
|------|------|----------|
| 组合环路 | 无法控制/观测 | 插入寄存器打断 |
| 门控时钟 | 扫描时无法控制 | 测试模式旁路 |
| 异步复位 | 扫描时需要控制 | 复位 MUX |
| 双边沿触发 | 非标准 | 使用 DDR 寄存器 |
| 透明锁存 | 测试难度大 | 改用 DFF |

### 扫描模式 MUX

```verilog
// 时钟门控的测试旁路
module clock_gate_with_test (
    input  wire clk,
    input  wire enable,
    input  wire test_mode,     // DFT 控制信号
    output wire gated_clk
);

    wire enable_or_test = enable | test_mode;

    // ... ICG 逻辑
    assign gated_clk = clk & enable_latch;

endmodule
```

```verilog
// 异步复位的测试控制
module dff_with_async_reset (
    input  wire clk,
    input  wire rst_n,
    input  wire scan_mode,     // DFT 控制信号
    input  wire scan_rst_n,    // 扫描模式复位
    input  wire d,
    output reg  q
);

    wire rst_ctrl = scan_mode ? scan_rst_n : rst_n;

    always @(posedge clk or negedge rst_ctrl) begin
        if (!rst_ctrl)
            q <= 1'b0;
        else
            q <= d;
    end

endmodule
```

---

## 时钟和复位处理

### 时钟域切换

```verilog
// 时钟选择器 - 无毛刺切换
module glitch_free_clk_mux (
    input  wire clk_a,
    input  wire clk_b,
    input  wire sel,       // 1=clk_b, 0=clk_a
    input  wire test_mode, // DFT: 强制选择
    input  wire test_sel,  // DFT: 测试时钟选择
    output wire clk_out
);

    wire sel_ctrl = test_mode ? test_sel : sel;

    // 同步和握手逻辑
    reg sel_a_sync, sel_b_sync;

    always @(negedge clk_a)
        sel_a_sync <= ~sel_ctrl & ~sel_b_sync;

    always @(negedge clk_b)
        sel_b_sync <= sel_ctrl & ~sel_a_sync;

    assign clk_out = (clk_a & sel_a_sync) | (clk_b & sel_b_sync);

endmodule
```

### 复位网络

```verilog
// 复位树需要可控
// 测试模式下，复位应可通过扫描链控制

module reset_controller (
    input  wire rst_n_async,
    input  wire scan_mode,
    input  wire scan_rst_n,
    input  wire clk,
    output wire rst_n_sync
);

    // 测试模式使用同步复位
    wire rst_n_in = scan_mode ? scan_rst_n : rst_n_async;

    // 复位同步器
    reg [1:0] rst_sync;
    always @(posedge clk or negedge rst_n_in) begin
        if (!rst_n_in)
            rst_sync <= 2'b00;
        else
            rst_sync <= {rst_sync[0], 1'b1};
    end

    assign rst_n_sync = rst_sync[1];

endmodule
```

---

## 可观测性设计

### 状态引出

```verilog
// 引出关键内部状态用于调试
module processor (
    // 功能接口
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] instr,
    output wire [31:0] result,

    // Debug 接口 - 引出内部状态
    output wire [2:0]  dbg_state,
    output wire [31:0] dbg_pc,
    output wire [31:0] dbg_reg_a,
    output wire        dbg_stall
);

    // 内部信号连接到 debug 端口
    assign dbg_state = fsm_state;
    assign dbg_pc    = program_counter;
    assign dbg_reg_a = reg_file[0];
    assign dbg_stall = pipeline_stall;

endmodule
```

### Debug Bus

```verilog
// 可配置 debug 总线
module debug_mux #(
    parameter NUM_SIGNALS = 8,
    parameter WIDTH = 32
)(
    input  wire [NUM_SIGNALS*WIDTH-1:0] debug_signals,
    input  wire [$clog2(NUM_SIGNALS)-1:0] debug_sel,
    output wire [WIDTH-1:0] debug_out
);

    wire [WIDTH-1:0] signals [0:NUM_SIGNALS-1];

    genvar i;
    generate
        for (i = 0; i < NUM_SIGNALS; i = i + 1) begin : gen_unpack
            assign signals[i] = debug_signals[i*WIDTH +: WIDTH];
        end
    endgenerate

    assign debug_out = signals[debug_sel];

endmodule
```

### 事件计数器

```verilog
// 性能/调试计数器
module event_counter #(
    parameter WIDTH = 32
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             event_in,   // 待计数事件
    input  wire             clear,      // 清零
    output reg  [WIDTH-1:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= '0;
        else if (clear)
            count <= '0;
        else if (event_in && count != {WIDTH{1'b1}})
            count <= count + 1;
    end

endmodule
```

---

## 检查清单

### 扫描设计

- [ ] 无组合环路
- [ ] 无锁存器 (或有测试控制)
- [ ] 门控时钟有测试旁路
- [ ] 异步复位可通过扫描控制
- [ ] 无双边沿触发器

### 时钟/复位

- [ ] 时钟选择器无毛刺
- [ ] 复位网络可控可观测
- [ ] 多时钟域有测试模式

### 可观测性

- [ ] 关键 FSM 状态可引出
- [ ] 内部总线可探测
- [ ] 有错误/异常指示信号
- [ ] 性能计数器可用

### 覆盖率

- [ ] 综合后扫描插入成功
- [ ] ATPG 覆盖率 > 95%
- [ ] 无法测试的点有文档说明
