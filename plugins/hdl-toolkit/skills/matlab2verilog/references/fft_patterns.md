# FFT 实现模式

## 目录

1. [基础概念](#基础概念)
2. [Radix-2 DIT FFT](#radix-2-dit-fft)
3. [Radix-4 FFT](#radix-4-fft)
4. [流水线 FFT](#流水线-fft)
5. [位宽管理](#位宽管理)

---

## 基础概念

### FFT 公式

```
X[k] = Σ x[n] * W_N^(nk)  (n=0 to N-1)

W_N = e^(-j*2π/N)  (旋转因子)
```

### 复数乘法

```
(a + jb)(c + jd) = (ac - bd) + j(ad + bc)

需要 4 个实数乘法 + 2 个加法
或 3 个乘法 + 5 个加法 (优化)
```

---

## Radix-2 DIT FFT

### 蝶形运算

```
A' = A + W * B
B' = A - W * B

其中 W = cos(θ) - j*sin(θ)
```

### Verilog 蝶形单元

```verilog
module butterfly #(
    parameter DATA_WL = 16,
    parameter COEF_WL = 16
)(
    input  signed [DATA_WL-1:0] ar, ai,  // A 实部、虚部
    input  signed [DATA_WL-1:0] br, bi,  // B 实部、虚部
    input  signed [COEF_WL-1:0] wr, wi,  // W 实部、虚部
    output signed [DATA_WL:0]   ar_out, ai_out,
    output signed [DATA_WL:0]   br_out, bi_out
);

// W * B = (wr*br - wi*bi) + j(wr*bi + wi*br)
wire signed [DATA_WL+COEF_WL-1:0] wb_r = wr*br - wi*bi;
wire signed [DATA_WL+COEF_WL-1:0] wb_i = wr*bi + wi*br;

// 截断
wire signed [DATA_WL-1:0] wb_r_trunc = wb_r >>> (COEF_WL-1);
wire signed [DATA_WL-1:0] wb_i_trunc = wb_i >>> (COEF_WL-1);

// 蝶形输出
assign ar_out = ar + wb_r_trunc;
assign ai_out = ai + wb_i_trunc;
assign br_out = ar - wb_r_trunc;
assign bi_out = ai - wb_i_trunc;

endmodule
```

---

## Radix-4 FFT

### 优势

- 减少复数乘法次数
- 旋转因子 1, -1, j, -j 无需乘法

### Radix-4 蝶形

```
X0 = A + B + C + D
X1 = (A - jB - C + jD) * W1
X2 = (A - B + C - D) * W2
X3 = (A + jB - C - jD) * W3
```

---

## 流水线 FFT

### SDF (Single-path Delay Feedback)

```
Stage 1: N/2 延迟 + 蝶形
Stage 2: N/4 延迟 + 蝶形
...
Stage log2(N): 1 延迟 + 蝶形
```

### MDF (Multi-path Delay Feedback)

- 多路并行处理
- 更高吞吐量

---

## 位宽管理

### 位宽增长

```
每级 FFT: +1 bit (蝶形加法)

N 点 FFT 总增长: log2(N) bits
1024 点: +10 bits
```

### 缩放策略

**Block Floating Point (推荐)**
```verilog
// 每级检测溢出
if (overflow_detected) begin
    scale_factor <= scale_factor + 1;
    // 右移1位
end
```

**固定缩放**
```verilog
// 每级固定右移1位
stage_out <= stage_in >>> 1;
```

### 旋转因子 ROM

```verilog
// 1024 点 FFT 旋转因子
// 只存储 1/4 周期，利用对称性
reg signed [15:0] twiddle_cos [0:255];
reg signed [15:0] twiddle_sin [0:255];

initial begin
    $readmemh("twiddle_cos.hex", twiddle_cos);
    $readmemh("twiddle_sin.hex", twiddle_sin);
end
```
