# 常见问题和修复

## 位宽问题

### 1. 位宽不匹配

```verilog
// 警告: 位宽不匹配
wire [15:0] a;
wire [7:0] b;
assign a = b;  // 8-bit 赋给 16-bit

// 修复: 显式扩展
assign a = {8'b0, b};        // 零扩展
assign a = {{8{b[7]}}, b};   // 符号扩展
```

### 2. 截断警告

```verilog
// 警告: 截断
wire [15:0] sum = a + b;  // 如果 a,b 是 16-bit，和是 17-bit

// 修复: 增加位宽或显式截断
wire [16:0] sum_full = a + b;
wire [15:0] sum = sum_full[15:0];  // 显式截断
```

## 未驱动/未使用信号

### 1. 未驱动信号

```verilog
// 警告: 'unused_sig' 从未被赋值
wire unused_sig;

// 修复: 删除或添加赋值
wire used_sig;
assign used_sig = some_value;
```

### 2. 未使用信号

```verilog
// 警告: 'result' 从未被使用
wire result = a + b;

// 修复: 删除或使用
// 如果故意忽略，添加注释:
// verilator lint_off UNUSEDSIGNAL
wire result = a + b;  // 用于调试
// verilator lint_on UNUSEDSIGNAL
```

## 多驱动

```verilog
// 错误: 多驱动
assign out = a;
assign out = b;  // 冲突!

// 修复: 使用选择逻辑
assign out = sel ? a : b;
```

## 敏感列表问题

### 1. 敏感列表不完整

```verilog
// 警告: 敏感列表不完整
always @(a)
    result = a & b;  // b 不在列表中

// 修复
always @(a or b)  // Verilog-95
always @(*)       // Verilog-2001 (推荐)
```

### 2. 边沿和电平混合

```verilog
// 错误: 混合边沿和电平触发
always @(posedge clk or a)  // 非法
    ...

// 修复: 分开处理
always @(posedge clk)
    if (a) ...
```

## 抑制特定警告

### Verilator

```verilog
// 单行抑制
/* verilator lint_off WIDTH */
assign narrow = wide;
/* verilator lint_on WIDTH */

// 整个模块抑制
// verilator lint_off UNUSED
module my_mod(...);
...
endmodule
// verilator lint_on UNUSED
```

### Icarus Verilog

```verilog
// 使用 `default_nettype none 检测未声明信号
`default_nettype none

module my_mod(...);
    ...
endmodule

`default_nettype wire
```
