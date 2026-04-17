# 滤波器实现模式

## 目录

1. [FIR 滤波器](#fir-滤波器)
2. [半带滤波器 (HBF)](#半带滤波器-hbf)
3. [IIR 滤波器](#iir-滤波器)
4. [CIC 滤波器](#cic-滤波器)
5. [优化技术](#优化技术)

---

## FIR 滤波器

### 直接型结构

```
y[n] = Σ h[k] * x[n-k]  (k=0 to N-1)
```

```verilog
// N-tap FIR 直接型
always @(posedge clk) begin
    if (ce) begin
        // 延迟线
        for (i = N-1; i > 0; i = i-1)
            dly[i] <= dly[i-1];
        dly[0] <= data_in;

        // 乘加
        acc = 0;
        for (i = 0; i < N; i = i+1)
            acc = acc + dly[i] * coef[i];

        data_out <= acc >>> SHIFT;
    end
end
```

### 转置型结构 (推荐高速设计)

```verilog
// 转置型 FIR - 关键路径短
always @(posedge clk) begin
    if (ce) begin
        mult[0] <= data_in * coef[0];
        for (i = 1; i < N; i = i+1) begin
            mult[i] <= data_in * coef[i];
            acc[i]  <= acc[i-1] + mult[i-1];
        end
        acc[0] <= mult[N-1];
        data_out <= acc[N-1];
    end
end
```

---

## 半带滤波器 (HBF)

### 特点

- 系数一半为零 (偶数位置)
- 中心系数为 0.5
- 系数对称

### 优化方法

```
原始: y = c0*x0 + 0*x1 + c2*x2 + 0.5*x3 + c4*x4 + 0*x5 + c6*x6

利用对称性 (c0=c6, c2=c4):
y = c0*(x0+x6) + c2*(x2+x4) + 0.5*x3

乘法器数量: 7 → 2 (减少 71%)
```

### Verilog 实现

```verilog
// Stage 1: 预加法器
pre_add_0 <= data[0] + data[6];  // 利用对称性
pre_add_2 <= data[2] + data[4];
center    <= data[3];

// Stage 2: 乘法器 (只需2个)
mult_0 <= pre_add_0 * COEF_0;
mult_2 <= pre_add_2 * COEF_2;
shift_3 <= {center, {(COEF_DWL-1){1'b0}}};  // 0.5 用移位实现

// Stage 3: 累加
acc <= mult_0 + mult_2 + shift_3;

// Stage 4: 截断 + 抽取
if (dec_phase == 0) begin
    data_out <= saturate(acc >>> COEF_DWL);
    vld_out  <= 1'b1;
end
```

---

## IIR 滤波器

### Direct Form I

```
y[n] = Σ b[k]*x[n-k] - Σ a[k]*y[n-k]
```

### Direct Form II (推荐)

```verilog
// 中间变量
w[n] = x[n] - a1*w[n-1] - a2*w[n-2]
y[n] = b0*w[n] + b1*w[n-1] + b2*w[n-2]

always @(posedge clk) begin
    w <= data_in - a1*w_d1 - a2*w_d2;
    data_out <= b0*w + b1*w_d1 + b2*w_d2;
    w_d2 <= w_d1;
    w_d1 <= w;
end
```

### 注意事项

- IIR 对系数量化敏感
- 需要仔细分析极点位置
- 建议使用级联二阶节 (SOS)

---

## CIC 滤波器

### 结构

```
CIC = Integrator^N → Decimator → Comb^N
```

### 积分器

```verilog
always @(posedge clk) begin
    if (ce) begin
        integ <= integ + data_in;  // 无饱和，依赖位宽增长
    end
end
```

### 梳状滤波器

```verilog
always @(posedge clk) begin
    if (ce && dec_vld) begin
        comb_out <= integ_out - comb_dly;
        comb_dly <= integ_out;
    end
end
```

### 位宽计算

```
CIC 位宽增长 = N * log2(R*M)

N = 阶数
R = 抽取率
M = 差分延迟 (通常为1)

示例: N=4, R=8, M=1
位宽增长 = 4 * log2(8) = 12 位
```

---

## 优化技术

### 1. 系数对称性利用

```
对称 FIR: h[k] = h[N-1-k]
使用预加法器: x[k] + x[N-1-k]
乘法器减半
```

### 2. CSD 编码

```
将系数转换为 Canonical Signed Digit
用移位和加法替代乘法

示例: 0.2817 ≈ 2^(-2) + 2^(-5) = 0.25 + 0.03125
```

### 3. 多相分解

```
用于抽取/插值滤波器
将滤波器分解为 R 个子滤波器
每个子滤波器以 1/R 速率运行
```

### 4. 资源共享

```
时分复用乘法器
适用于低速率、多通道场景
```
