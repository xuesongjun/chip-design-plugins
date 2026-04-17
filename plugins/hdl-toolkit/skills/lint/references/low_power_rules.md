# 低功耗设计规则

## 目录

1. [功耗来源](#功耗来源)
2. [门控时钟 (Clock Gating)](#门控时钟-clock-gating)
3. [多电压域设计](#多电压域设计)
4. [数据通路优化](#数据通路优化)
5. [检查清单](#检查清单)

---

## 功耗来源

### CMOS 功耗公式

```
P_total = P_dynamic + P_static

P_dynamic = α × C × V² × f
    α = 翻转率 (switching activity)
    C = 负载电容
    V = 供电电压
    f = 时钟频率

P_static = I_leak × V
    I_leak = 漏电流 (随工艺缩小而增加)
```

### 优化策略

| 目标 | 技术 | 效果 |
|------|------|------|
| 降低 α | 门控时钟、操作数隔离 | 减少动态功耗 |
| 降低 f | 局部时钟门控 | 减少动态功耗 |
| 降低 V | 多电压域 | 显著减少功耗 |
| 降低 I_leak | 电源门控 | 减少静态功耗 |

---

## 门控时钟 (Clock Gating)

### ICG (Integrated Clock Gating Cell)

```verilog
// 标准 ICG 单元 - 由综合工具自动插入
// RTL 代码应写成如下风格，让工具识别

// 推荐: 让工具自动插入 ICG
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        data_reg <= '0;
    else if (enable)           // 条件使能
        data_reg <= data_in;   // 工具会自动插入门控
end

// 不推荐: 手动门控 (有毛刺风险)
wire gated_clk = clk & enable;  // 危险!
always @(posedge gated_clk)
    data_reg <= data_in;
```

### 正确的手动 ICG (如果必须)

```verilog
// 锁存器消除毛刺
module icg_cell (
    input  wire clk,
    input  wire enable,
    input  wire test_mode,  // DFT: 测试模式旁路门控
    output wire gated_clk
);

    reg enable_latch;

    // 负沿锁存 enable 信号
    always @(*) begin
        if (!clk)
            enable_latch <= enable | test_mode;
    end

    assign gated_clk = clk & enable_latch;

endmodule
```

### 门控粒度

| 粒度 | 门控对象 | 效果 | 复杂度 |
|------|----------|------|--------|
| 模块级 | 整个子模块 | 高 | 低 |
| 寄存器组 | 功能相关的寄存器 | 中 | 中 |
| 单寄存器 | 单个寄存器 | 低 | 高 (面积开销) |

---

## 多电压域设计

### 电压域边界处理

```
高电压域 ──────► Level Shifter ──────► 低电压域
   │                                      │
   │         信号从高到低需要 LS          │
   │                                      │
低电压域 ──────► Level Shifter ──────► 高电压域
                信号从低到高需要 LS
```

### 隔离单元 (Isolation Cell)

```verilog
// 当关断域断电时，输出到常开域的信号需要隔离
// 防止浮空输入导致短路电流

// RTL 中声明隔离属性 (工具相关)
(* isolation = "true", isolation_value = "1'b0" *)
output wire data_out;

// 或使用 UPF/CPF 描述
// set_isolation iso_rule -domain PD_OFF \
//     -isolation_power_net VDD_ON \
//     -isolation_ground_net VSS \
//     -clamp_value 0
```

### 电源门控 (Power Gating)

```verilog
// 电源域状态机
localparam [1:0]
    PWR_OFF     = 2'b00,
    PWR_UP      = 2'b01,
    PWR_ON      = 2'b10,
    PWR_DOWN    = 2'b11;

// 上电/下电序列
// 1. 隔离使能
// 2. 复位断言
// 3. 电源切换
// 4. 等待稳定
// 5. 复位释放
// 6. 隔离禁用
```

### Retention 寄存器

```verilog
// 保持寄存器 - 断电时保存状态
// RTL 中标记需要保持的寄存器
(* retention = "true" *)
reg [31:0] critical_state;

// 保存/恢复序列
// 断电前: save_en = 1, 将主寄存器值存入影子寄存器
// 上电后: restore_en = 1, 从影子寄存器恢复
```

---

## 数据通路优化

### 操作数隔离 (Operand Isolation)

```verilog
// 未优化: 乘法器每周期都在计算
wire [31:0] product = a * b;
always @(posedge clk)
    if (valid)
        result <= product;

// 优化: 无效时隔离输入，减少翻转
wire [15:0] a_gated = valid ? a : '0;  // 或保持上次值
wire [15:0] b_gated = valid ? b : '0;
wire [31:0] product = a_gated * b_gated;
always @(posedge clk)
    if (valid)
        result <= product;
```

### 减少翻转活动

```verilog
// 避免不必要的翻转
// 差: data_out 每周期都可能翻转
always @(posedge clk)
    data_out <= mux_sel ? data_a : data_b;

// 好: 只在选择变化或数据变化时更新
always @(posedge clk)
    if (data_changed || sel_changed)
        data_out <= mux_sel ? data_a : data_b;
```

### 编码优化

```verilog
// 总线使用 Gray 码减少翻转
// Binary: 7->8 = 0111->1000 (4 bits flip)
// Gray:   7->8 = 0100->1100 (1 bit flip)

function [3:0] bin2gray;
    input [3:0] bin;
    bin2gray = bin ^ (bin >> 1);
endfunction
```

---

## 检查清单

### 门控时钟

- [ ] 写成条件使能风格，让工具自动插入 ICG
- [ ] 避免手动门控时钟
- [ ] DFT 模式下门控可旁路
- [ ] 门控粒度适当 (不要过细)

### 多电压域

- [ ] 跨电压域信号有 Level Shifter
- [ ] 关断域输出有隔离单元
- [ ] 关键状态使用 Retention 寄存器
- [ ] 电源控制序列正确

### 数据通路

- [ ] 空闲时隔离大型运算单元输入
- [ ] 避免不必要的信号翻转
- [ ] 高翻转率总线考虑 Gray 编码

### 工具检查

- [ ] 综合报告中检查自动插入的 ICG 数量
- [ ] 功耗分析报告确认热点
- [ ] 后仿功耗与预期一致
