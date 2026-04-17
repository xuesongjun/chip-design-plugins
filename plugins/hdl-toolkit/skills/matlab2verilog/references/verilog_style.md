# Verilog 编码规范

## 模块结构

```verilog
//==============================================================================
// Module: <module_name>
// Description: <功能描述>
// Features: <关键特性>
//==============================================================================

module <module_name> #(
    // 参数定义 (使用 S(W,F) 注释)
    parameter DATA_WL  = 14,          // S(14,11) 数据位宽
    parameter DATA_DWL = 11,          // 小数位宽
    parameter COEF_WL  = 14,          // S(14,11) 系数位宽
    parameter COEF_DWL = 11
)(
    // 时钟和复位
    input  wire                    clk,
    input  wire                    rst_n,      // 异步复位，低有效
    input  wire                    ce,         // 时钟使能

    // 数据输入
    input  wire signed [DATA_WL-1:0] data_in,
    input  wire                    vld_in,

    // 数据输出
    output reg  signed [DATA_WL-1:0] data_out,
    output reg                     vld_out,

    // 状态指示
    output reg                     overflow
);
```

## 命名规范

### 信号命名

| 类型 | 前缀/后缀 | 示例 |
|------|-----------|------|
| 时钟 | clk | clk, clk_200m |
| 复位 | rst_n | rst_n (低有效) |
| 使能 | en, ce | ce, data_en |
| 有效 | vld | vld_in, vld_out |
| 就绪 | rdy | data_rdy |
| 延迟 | _d1, _d2 | data_d1, data_d2 |
| I/Q 通道 | _i, _q | data_in_i, data_in_q |
| 溢出 | ovf | ovf_i, ovf_q |

### 参数命名

| 类型 | 命名 | 示例 |
|------|------|------|
| 位宽 | _WL | DATA_WL, COEF_WL |
| 小数位宽 | _DWL | DATA_DWL, COEF_DWL |
| 长度 | _LEN | TAP_LEN, FFT_LEN |
| 数量 | NUM_ | NUM_CHANNELS |

## 复位风格

```verilog
// 异步复位，同步释放
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        data_out <= {DATA_WL{1'b0}};
        vld_out  <= 1'b0;
    end else if (ce) begin
        // 正常逻辑
    end
end
```

## 流水线设计

### 命名约定

```verilog
// Stage 1
reg signed [DATA_WL:0] add_s1;
reg vld_s1;

// Stage 2
reg signed [MULT_WL-1:0] mult_s2;
reg vld_s2;

// Stage 3
reg signed [ACC_WL-1:0] acc_s3;
reg vld_s3;
```

### 流水线模板

```verilog
//==============================================================================
// Stage 1: <阶段描述>
//==============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        add_s1 <= '0;
        vld_s1 <= 1'b0;
    end else if (ce) begin
        add_s1 <= data_a + data_b;
        vld_s1 <= vld_in;
    end
end

//==============================================================================
// Stage 2: <阶段描述>
//==============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        mult_s2 <= '0;
        vld_s2  <= 1'b0;
    end else if (ce) begin
        mult_s2 <= add_s1 * coef;
        vld_s2  <= vld_s1;
    end
end
```

## 饱和截断

```verilog
// 参数化饱和逻辑
localparam signed [OUT_WL-1:0] MAX_VAL = {1'b0, {(OUT_WL-1){1'b1}}};
localparam signed [OUT_WL-1:0] MIN_VAL = {1'b1, {(OUT_WL-1){1'b0}}};

wire ovf_pos = (acc_shifted > MAX_VAL);
wire ovf_neg = (acc_shifted < MIN_VAL);

wire signed [OUT_WL-1:0] saturated = ovf_pos ? MAX_VAL :
                                      ovf_neg ? MIN_VAL :
                                      acc_shifted[OUT_WL-1:0];
```

## 系数定义

```verilog
//==============================================================================
// Coefficient Definition: S(14,11) format
// Quantization: scale = 2^11 = 2048
//==============================================================================
localparam signed [COEF_WL-1:0] COEF_0 = -14'sd65;   // -0.0317
localparam signed [COEF_WL-1:0] COEF_1 =  14'sd577;  //  0.2817
localparam signed [COEF_WL-1:0] COEF_2 =  14'sd1024; //  0.5
```

## 注释规范

```verilog
//==============================================================================
// 大节标题 (模块、主要功能块)
//==============================================================================

// 单行注释: 简短说明

/*
 * 多行注释:
 * 用于复杂的算法说明
 * 或详细的设计说明
 */

// 信号格式注释
reg signed [27:0] mult_out;  // S(28,22) = S(14,11) × S(14,11)
```

## 位宽计算注释

```verilog
// 位宽计算:
// pre_add: S(14,11) + S(14,11) = S(15,11)
// mult:    S(15,11) × S(14,11) = S(29,22)
// acc:     S(29,22) + S(29,22) + S(29,22) = S(31,22)
// output:  S(31,22) >> 11 = S(20,11) → saturate → S(14,11)
```
