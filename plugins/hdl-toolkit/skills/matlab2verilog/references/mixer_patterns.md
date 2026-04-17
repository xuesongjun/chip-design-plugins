# 混频器/NCO 实现模式

## 目录

1. [数字混频器](#数字混频器)
2. [NCO (数控振荡器)](#nco-数控振荡器)
3. [DDS (直接数字合成)](#dds-直接数字合成)
4. [CORDIC](#cordic)

---

## 数字混频器

### 基本原理

```
复数混频:
y(t) = x(t) * e^(j*2π*fc*t)

实现:
y_i = x_i * cos(θ) - x_q * sin(θ)
y_q = x_i * sin(θ) + x_q * cos(θ)
```

### Verilog 实现

```verilog
module mixer #(
    parameter DATA_WL = 14,
    parameter COEF_WL = 16
)(
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire signed [DATA_WL-1:0] data_i,
    input  wire signed [DATA_WL-1:0] data_q,
    input  wire signed [COEF_WL-1:0] cos_val,
    input  wire signed [COEF_WL-1:0] sin_val,
    output reg  signed [DATA_WL-1:0] out_i,
    output reg  signed [DATA_WL-1:0] out_q
);

localparam MULT_WL = DATA_WL + COEF_WL;

wire signed [MULT_WL-1:0] mult_i_cos = data_i * cos_val;
wire signed [MULT_WL-1:0] mult_q_sin = data_q * sin_val;
wire signed [MULT_WL-1:0] mult_i_sin = data_i * sin_val;
wire signed [MULT_WL-1:0] mult_q_cos = data_q * cos_val;

wire signed [MULT_WL:0] sum_i = mult_i_cos - mult_q_sin;
wire signed [MULT_WL:0] sum_q = mult_i_sin + mult_q_cos;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        out_i <= '0;
        out_q <= '0;
    end else begin
        out_i <= sum_i >>> (COEF_WL - 1);
        out_q <= sum_q >>> (COEF_WL - 1);
    end
end

endmodule
```

---

## NCO (数控振荡器)

### 相位累加器结构

```
phase[n] = phase[n-1] + freq_word

freq_word = (fc / fs) * 2^PHASE_WL
```

### Verilog NCO

```verilog
module nco #(
    parameter PHASE_WL = 32,
    parameter LUT_ADDR = 10,
    parameter OUT_WL   = 16
)(
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire [PHASE_WL-1:0]      freq_word,
    output reg  signed [OUT_WL-1:0] cos_out,
    output reg  signed [OUT_WL-1:0] sin_out
);

reg [PHASE_WL-1:0] phase_acc;

// 相位累加
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        phase_acc <= '0;
    else
        phase_acc <= phase_acc + freq_word;
end

// LUT 地址 (取高位)
wire [LUT_ADDR-1:0] lut_addr = phase_acc[PHASE_WL-1 -: LUT_ADDR];

// Sin/Cos LUT
reg signed [OUT_WL-1:0] cos_lut [0:(1<<LUT_ADDR)-1];
reg signed [OUT_WL-1:0] sin_lut [0:(1<<LUT_ADDR)-1];

always @(posedge clk) begin
    cos_out <= cos_lut[lut_addr];
    sin_out <= sin_lut[lut_addr];
end

endmodule
```

### 频率分辨率

```
频率分辨率 = fs / 2^PHASE_WL

示例:
fs = 100 MHz, PHASE_WL = 32
分辨率 = 100e6 / 2^32 ≈ 0.023 Hz
```

---

## DDS (直接数字合成)

### 完整 DDS 结构

```
频率字 → 相位累加器 → 相位调制 → Sin/Cos LUT → DAC
```

### 相位抖动 (Phase Dithering)

```verilog
// 减少杂散
wire [LUT_ADDR-1:0] addr_dithered =
    phase_acc[PHASE_WL-1 -: LUT_ADDR] +
    (phase_acc[PHASE_WL-LUT_ADDR-1] ? 1 : 0);  // 四舍五入
```

### LUT 优化

**1/4 周期对称性**
```
sin(θ)       = sin_lut[addr]           // 第一象限
sin(π-θ)     = sin_lut[N-1-addr]       // 第二象限
sin(π+θ)     = -sin_lut[addr]          // 第三象限
sin(2π-θ)    = -sin_lut[N-1-addr]      // 第四象限
```

---

## CORDIC

### 原理

通过迭代旋转计算 sin/cos，无需乘法器。

### Verilog CORDIC

```verilog
module cordic #(
    parameter ITER = 16,
    parameter WL   = 16
)(
    input  wire                  clk,
    input  wire [WL-1:0]         angle,
    output reg  signed [WL-1:0]  cos_out,
    output reg  signed [WL-1:0]  sin_out
);

// 预计算的 arctan 表
wire signed [WL-1:0] atan_table [0:ITER-1];
assign atan_table[0]  = 16'd8192;   // atan(2^0)  = 45°
assign atan_table[1]  = 16'd4836;   // atan(2^-1) = 26.57°
assign atan_table[2]  = 16'd2555;   // atan(2^-2) = 14.04°
// ... 更多迭代

// CORDIC 迭代
reg signed [WL+1:0] x [0:ITER];
reg signed [WL+1:0] y [0:ITER];
reg signed [WL+1:0] z [0:ITER];

always @(*) begin
    // 初始化
    x[0] = CORDIC_GAIN;  // ≈ 0.6073
    y[0] = 0;
    z[0] = angle;

    for (i = 0; i < ITER; i = i+1) begin
        if (z[i] >= 0) begin
            x[i+1] = x[i] - (y[i] >>> i);
            y[i+1] = y[i] + (x[i] >>> i);
            z[i+1] = z[i] - atan_table[i];
        end else begin
            x[i+1] = x[i] + (y[i] >>> i);
            y[i+1] = y[i] - (x[i] >>> i);
            z[i+1] = z[i] + atan_table[i];
        end
    end
end

assign cos_out = x[ITER];
assign sin_out = y[ITER];

endmodule
```

### CORDIC vs LUT

| 方面 | CORDIC | LUT |
|------|--------|-----|
| 面积 | 小 (移位+加法) | 大 (存储器) |
| 延迟 | 高 (多次迭代) | 低 (1-2 周期) |
| 精度 | 迭代次数决定 | LUT 大小决定 |
| 适用 | 面积受限 | 速度优先 |
