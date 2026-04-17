# 跨时钟域 (CDC/RDC) 规则

## 目录

1. [CDC 基础](#cdc-基础)
2. [同步器设计](#同步器设计)
3. [多位信号跨域](#多位信号跨域)
4. [复位域交叉 (RDC)](#复位域交叉-rdc)
5. [常见错误模式](#常见错误模式)
6. [检查清单](#检查清单)

---

## CDC 基础

### 为什么 CDC 如此重要？

跨时钟域信号如果处理不当，会导致：
- **亚稳态 (Metastability)**: 触发器输出不确定
- **数据丢失**: 脉冲宽度小于目标时钟周期
- **数据损坏**: 多位信号不同步到达

### CDC 路径类型

| 类型 | 描述 | 风险等级 |
|------|------|----------|
| 单比特控制 | 使能、标志位 | 中 |
| 单比特脉冲 | 握手、中断 | 高 |
| 多比特数据 | 总线、状态 | **极高** |
| 复位信号 | 异步复位跨域 | 高 |

---

## 同步器设计

### 两级同步器 (基本要求)

```verilog
// 标准两级同步器
module sync_2ff #(
    parameter WIDTH = 1,
    parameter RESET_VAL = '0
)(
    input  wire             clk_dst,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_src,
    output wire [WIDTH-1:0] data_dst
);

    (* ASYNC_REG = "TRUE" *)  // Xilinx: 防止优化
    reg [WIDTH-1:0] sync_ff1;

    (* ASYNC_REG = "TRUE" *)
    reg [WIDTH-1:0] sync_ff2;

    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n) begin
            sync_ff1 <= RESET_VAL;
            sync_ff2 <= RESET_VAL;
        end else begin
            sync_ff1 <= data_src;
            sync_ff2 <= sync_ff1;
        end
    end

    assign data_dst = sync_ff2;

endmodule
```

### 三级同步器 (高可靠性)

```verilog
// 三级同步器 - 用于高速或高可靠性场景
module sync_3ff #(parameter WIDTH = 1)(
    input  wire             clk_dst,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_src,
    output wire [WIDTH-1:0] data_dst
);

    (* ASYNC_REG = "TRUE" *)
    reg [WIDTH-1:0] sync_ff1, sync_ff2, sync_ff3;

    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n) begin
            {sync_ff3, sync_ff2, sync_ff1} <= '0;
        end else begin
            sync_ff1 <= data_src;
            sync_ff2 <= sync_ff1;
            sync_ff3 <= sync_ff2;
        end
    end

    assign data_dst = sync_ff3;

endmodule
```

### 脉冲同步器

```verilog
// 源时钟域脉冲 -> 目标时钟域脉冲
module pulse_sync (
    input  wire clk_src,
    input  wire clk_dst,
    input  wire rst_n,
    input  wire pulse_src,
    output wire pulse_dst
);

    // 源域: 脉冲转电平
    reg toggle_src;
    always @(posedge clk_src or negedge rst_n) begin
        if (!rst_n)
            toggle_src <= 1'b0;
        else if (pulse_src)
            toggle_src <= ~toggle_src;
    end

    // 目标域: 同步 + 边沿检测
    reg [2:0] sync_ff;
    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n)
            sync_ff <= 3'b0;
        else
            sync_ff <= {sync_ff[1:0], toggle_src};
    end

    assign pulse_dst = sync_ff[2] ^ sync_ff[1];

endmodule
```

---

## 多位信号跨域

### 方法 1: Gray 码

```verilog
// 计数器跨域 - 使用 Gray 码
module gray_sync #(parameter WIDTH = 4)(
    input  wire             clk_src,
    input  wire             clk_dst,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] bin_src,
    output wire [WIDTH-1:0] bin_dst
);

    // 二进制转 Gray
    wire [WIDTH-1:0] gray_src = bin_src ^ (bin_src >> 1);

    // 同步 Gray 码
    reg [WIDTH-1:0] gray_sync1, gray_sync2;
    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n) begin
            gray_sync1 <= '0;
            gray_sync2 <= '0;
        end else begin
            gray_sync1 <= gray_src;
            gray_sync2 <= gray_sync1;
        end
    end

    // Gray 转二进制
    integer i;
    reg [WIDTH-1:0] bin_tmp;
    always @(*) begin
        bin_tmp[WIDTH-1] = gray_sync2[WIDTH-1];
        for (i = WIDTH-2; i >= 0; i = i-1)
            bin_tmp[i] = bin_tmp[i+1] ^ gray_sync2[i];
    end

    assign bin_dst = bin_tmp;

endmodule
```

### 方法 2: 异步 FIFO

```verilog
// 异步 FIFO 指针同步 (简化版)
// 完整实现需要更多逻辑
module async_fifo_ptr #(parameter ADDR_W = 4)(
    // 写时钟域
    input  wire             wr_clk,
    input  wire             wr_rst_n,
    input  wire             wr_en,
    output wire             full,
    output wire [ADDR_W:0]  wr_ptr,

    // 读时钟域
    input  wire             rd_clk,
    input  wire             rd_rst_n,
    input  wire             rd_en,
    output wire             empty,
    output wire [ADDR_W:0]  rd_ptr
);
    // Gray 码指针 + 同步器
    // ... 完整实现
endmodule
```

### 方法 3: 握手协议

```verilog
// 四阶段握手
module handshake_sync #(parameter WIDTH = 8)(
    // 源时钟域
    input  wire             clk_src,
    input  wire             rst_src_n,
    input  wire             req_src,
    input  wire [WIDTH-1:0] data_src,
    output wire             ack_src,

    // 目标时钟域
    input  wire             clk_dst,
    input  wire             rst_dst_n,
    output wire             req_dst,
    output reg  [WIDTH-1:0] data_dst,
    input  wire             ack_dst
);
    // req 同步到目标域
    // ack 同步回源域
    // 数据在 req 有效期间保持稳定
    // ... 完整实现
endmodule
```

---

## 复位域交叉 (RDC)

### 异步复位同步释放

```verilog
// 标准复位同步器
module reset_synchronizer #(
    parameter SYNC_STAGES = 2,
    parameter RESET_ACTIVE = 1'b0  // 低有效
)(
    input  wire clk,
    input  wire rst_async,
    output wire rst_sync
);

    (* ASYNC_REG = "TRUE" *)
    reg [SYNC_STAGES-1:0] rst_sync_ff;

    always @(posedge clk or negedge rst_async) begin
        if (rst_async == RESET_ACTIVE)
            rst_sync_ff <= {SYNC_STAGES{RESET_ACTIVE}};
        else
            rst_sync_ff <= {rst_sync_ff[SYNC_STAGES-2:0], ~RESET_ACTIVE};
    end

    assign rst_sync = rst_sync_ff[SYNC_STAGES-1];

endmodule
```

### 多时钟域复位顺序

```
复位释放顺序 (推荐):
1. 首先释放最慢的时钟域
2. 然后依次释放更快的时钟域
3. 确保下游模块在上游之后释放
```

---

## 常见错误模式

### 错误 1: 直接跨域

```verilog
// 错误! 没有同步器
always @(posedge clk_b)
    data_b <= data_a;  // data_a 来自 clk_a 域

// 正确
sync_2ff u_sync (.clk_dst(clk_b), .data_src(data_a), .data_dst(data_a_sync));
always @(posedge clk_b)
    data_b <= data_a_sync;
```

### 错误 2: 组合逻辑跨域

```verilog
// 错误! 组合逻辑输出跨域
wire comb_out = a & b | c;  // clk_a 域
always @(posedge clk_b)
    reg_b <= comb_out;  // 直接使用组合输出

// 正确: 先寄存再同步
reg comb_out_reg;
always @(posedge clk_a)
    comb_out_reg <= a & b | c;
// 然后同步 comb_out_reg
```

### 错误 3: 多位信号直接同步

```verilog
// 错误! 多位信号每位独立同步
sync_2ff #(.WIDTH(8)) u_sync (
    .data_src(data_8bit),  // 8位总线
    .data_dst(data_8bit_sync)
);
// 各位可能在不同周期稳定，导致错误数据!

// 正确: 使用 Gray 码或异步 FIFO
```

---

## 检查清单

### 致命级别 (必须修复)

- [ ] 所有跨时钟域单比特信号都有同步器
- [ ] 多位信号使用 Gray 码/FIFO/握手协议
- [ ] 没有组合逻辑直接跨域
- [ ] 异步复位使用复位同步器

### 高优先级

- [ ] 同步器使用 ASYNC_REG 约束
- [ ] 脉冲信号使用脉冲同步器
- [ ] 复位释放顺序正确

### 中优先级

- [ ] 同一模块复位风格一致
- [ ] CDC 路径有充足时序约束
- [ ] 文档记录所有 CDC 路径
