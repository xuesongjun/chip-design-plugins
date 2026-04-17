# 可综合性规则

## 不可综合的构造

| 构造 | 说明 | 替代方案 |
|------|------|----------|
| `#delay` | 延迟语句 | 使用时钟周期计数 |
| `$display` | 仿真打印 | 仅用于 Testbench |
| `$finish` | 仿真终止 | 仅用于 Testbench |
| `$time` | 仿真时间 | 仅用于 Testbench |
| `$random` | 随机数 | 使用 LFSR |
| `forever` | 无限循环 | 使用 always 块 |
| `wait` | 等待事件 | 使用同步逻辑 |
| `force/release` | 强制赋值 | 仅用于调试 |

## 有条件可综合

| 构造 | FPGA | ASIC | 说明 |
|------|------|------|------|
| `initial` | ✓ | ✗ | FPGA 可用于初始化 |
| RAM 初始化 | ✓ | ✗ | FPGA 支持 $readmemh |
| 三态 | 部分 | ✓ | FPGA 内部通常不支持 |

## 常见可综合性问题

### 1. 不完整的敏感列表

```verilog
// 错误
always @(a or b)
    result = a + b + c;  // c 不在敏感列表

// 正确
always @(a or b or c)
    result = a + b + c;

// 推荐 (Verilog-2001)
always @(*)
    result = a + b + c;
```

### 2. Latch 推断

```verilog
// 会产生 latch (缺少 else)
always @(*)
    if (sel)
        out = a;

// 正确 (有 else)
always @(*)
    if (sel)
        out = a;
    else
        out = b;
```

### 3. 组合逻辑环路

```verilog
// 错误 - 组合逻辑环
always @(*)
    a = b;
always @(*)
    b = a;  // 环路!

// 应该使用寄存器打断环路
```

## 时钟和复位

### 推荐的复位风格

```verilog
// 异步复位，同步释放
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= 1'b0;
    else
        q <= d;
end
```

### 避免的模式

- 双边沿时钟 (posedge + negedge)
- 门控时钟 (直接在时钟路径加逻辑)
- 异步设计 (多时钟域无同步)
