---
description: |
  将 MATLAB DSP 算法转换为高性能 Verilog RTL 代码。支持滤波器(FIR/IIR/HBF/CIC)、FFT、混频器(Mixer/NCO/DDS)等常见 DSP 模块。
  当用户提供 MATLAB 代码并要求生成 Verilog/RTL/硬件实现时触发此技能。
  输出包括：(1) 优化的 Verilog 模块 (2) Testbench (3) Python 验证脚本 (4) 量化分析报告
  关键词：MATLAB to Verilog, DSP RTL, 滤波器硬件实现, 定点化, bit-true 验证
---

# MATLAB to Verilog 转换技能

将 MATLAB DSP 算法转换为可综合的高性能 Verilog 代码，确保与 MATLAB bit-true 一致。

## 工作流程

### 1. 分析 MATLAB 代码

读取并分析用户提供的 MATLAB 代码，提取：
- 算法类型（滤波器/FFT/混频器/通用）
- 系数和参数
- 数据流和时序关系

### 2. 确定定点格式

使用 **S(W,F) 格式**（W=总位宽，F=小数位）：

```
S(14,11) = 14位有符号数，11位小数
         = 1符号 + 2整数 + 11小数
范围: [-4, +4), 精度: 2^(-11) ≈ 0.000488
```

位宽计算规则：
| 运算 | 输入 | 输出 |
|------|------|------|
| 加法 | S(W,F) + S(W,F) | S(W+1,F) |
| 乘法 | S(W1,F1) × S(W2,F2) | S(W1+W2, F1+F2) |
| 截断 | S(W,F) → S(W',F') | 右移 F-F' 位 + 饱和 |

### 3. 识别优化机会

根据用户需求选择优化策略：

**面积优化**：
- 系数对称性 → 预加法器（减少乘法器）
- 零值系数 → 跳过计算
- CSD 编码 → 移位替代乘法
- 资源共享 → 时分复用

**速度优化**：
- 流水线寄存器
- 并行展开
- 关键路径平衡

**功耗优化**：
- 时钟门控
- 操作数隔离

### 4. 生成 Verilog 代码

遵循编码规范（详见 [references/verilog_style.md](references/verilog_style.md)）：

```verilog
module <module_name> #(
    // 参数使用 S(W,F) 注释
    parameter DATA_WL  = 14,  // S(14,11)
    parameter DATA_DWL = 11
)(
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    ce,
    input  wire signed [DATA_WL-1:0] data_in,
    input  wire                    vld_in,
    output reg  signed [DATA_WL-1:0] data_out,
    output reg                     vld_out
);
```

### 5. 生成验证代码

- **Testbench**: 自动生成测试激励和黄金模型比对
- **Python 脚本**: 实现与 MATLAB 等效算法，计算量化 SNR

### 6. 输出量化分析

报告内容：
- 量化系数表
- 量化 SNR（信噪比）
- 溢出检测结果

## 模块类型参考

| 类型 | 参考文档 |
|------|----------|
| 滤波器 (FIR/IIR/HBF/CIC) | [references/filter_patterns.md](references/filter_patterns.md) |
| FFT/IFFT | [references/fft_patterns.md](references/fft_patterns.md) |
| 混频器/NCO | [references/mixer_patterns.md](references/mixer_patterns.md) |
| 定点格式详解 | [references/fixpoint_format.md](references/fixpoint_format.md) |
| Verilog 编码规范 | [references/verilog_style.md](references/verilog_style.md) |

## 工具脚本

| 脚本 | 用途 |
|------|------|
| [scripts/quantize_coef.py](scripts/quantize_coef.py) | 系数量化和分析 |

## 示例

用户输入：
> "根据 rxHBF.m 生成 Verilog，数据 S(14,11)，系数 S(14,11)，针对 7nm 优化"

输出：
1. `rx_hbf_top.v` - RTL 模块（利用对称性，2个乘法器+4级流水线）
2. `tb_rx_hbf_top.v` - Testbench
3. `verify_rx_hbf.py` - Python 验证脚本
4. 量化 SNR 报告
