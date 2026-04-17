---
description: |
  Verilog/SystemVerilog 全面代码审查工具。覆盖 SoC/ASIC 设计中的关键检查项：
  (1) 基础检查：语法、风格、可综合性
  (2) CDC/RDC：跨时钟域、复位同步
  (3) 低功耗：门控时钟、隔离单元
  (4) 健壮性：FSM 安全、边界条件
  (5) DFT：可测性设计
  (6) 可维护性：参数化、宏管理
  当用户要求检查 Verilog 代码、运行 lint、代码审查或检测潜在问题时触发。
  支持工具：Verilator, Icarus Verilog, Verible, Spyglass (商业)
---

# Verilog 代码审查

覆盖 SoC/ASIC 设计全流程的代码质量检查。

## 检查清单概览

| 类别 | 严重性 | 检查项 | 参考文档 |
|------|--------|--------|----------|
| **CDC/RDC** | 高 | 跨时钟域同步、复位一致性 | [cdc_rules.md](references/cdc_rules.md) |
| **健壮性** | 高 | FSM 安全、边界条件 | [robustness_rules.md](references/robustness_rules.md) |
| **可综合性** | 高 | 不可综合构造、Latch | [synthesis_rules.md](references/synthesis_rules.md) |
| **低功耗** | 中 | 门控时钟、隔离单元 | [low_power_rules.md](references/low_power_rules.md) |
| **DFT** | 中 | 扫描链、可观测性 | [dft_rules.md](references/dft_rules.md) |
| **风格** | 低 | 命名规范、格式 | [style_rules.md](references/style_rules.md) |

---

## 1. 跨时钟域 (CDC/RDC) - 最高优先级

**这是 SoC 设计中最容易出 Bug 的地方。**

### 检查项

| 检查 | 说明 | 严重性 |
|------|------|--------|
| 同步器缺失 | 跨时钟域信号未经 2/3 级同步 | **致命** |
| 组合逻辑跨域 | 组合输出直接跨时钟域 | **致命** |
| 多位信号跨域 | 未使用 Gray 码或异步 FIFO | **致命** |
| 复位同步器 | 异步复位未同步释放 | 高 |
| 混合复位 | 同一模块混用同步/异步复位 | 中 |

### 正确的 CDC 同步器

```verilog
// 两级同步器 (最小要求)
module sync_2ff #(parameter WIDTH = 1) (
    input  wire             clk_dst,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_src,
    output reg  [WIDTH-1:0] data_dst
);
    reg [WIDTH-1:0] sync_reg;

    always @(posedge clk_dst or negedge rst_n) begin
        if (!rst_n) begin
            sync_reg <= '0;
            data_dst <= '0;
        end else begin
            sync_reg <= data_src;
            data_dst <= sync_reg;
        end
    end
endmodule
```

### 正确的复位同步器

```verilog
// 异步复位同步释放
module reset_sync (
    input  wire clk,
    input  wire rst_async_n,
    output reg  rst_sync_n
);
    reg rst_d1;

    always @(posedge clk or negedge rst_async_n) begin
        if (!rst_async_n) begin
            rst_d1     <= 1'b0;
            rst_sync_n <= 1'b0;
        end else begin
            rst_d1     <= 1'b1;
            rst_sync_n <= rst_d1;
        end
    end
endmodule
```

详见 [references/cdc_rules.md](references/cdc_rules.md)

---

## 2. 代码健壮性

### FSM 安全检查

| 检查 | 说明 |
|------|------|
| default 分支 | case 语句必须有 default |
| 非法状态恢复 | FSM 能否从非法状态恢复 |
| 状态编码 | 推荐 one-hot 或 gray 编码 |
| 三段式结构 | 现态、次态、输出分离 |

```verilog
// 安全的 FSM 模板
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end

always @(*) begin
    next_state = state;  // 默认保持
    case (state)
        IDLE:   if (start) next_state = RUN;
        RUN:    if (done)  next_state = IDLE;
        default: next_state = IDLE;  // 非法状态恢复
    endcase
end
```

### 边界条件检查

| 检查 | 说明 |
|------|------|
| FIFO 满/空 | 满时写入、空时读取的处理 |
| 计数器溢出 | 是否有溢出保护 |
| 数组越界 | 索引是否可能超出范围 |

详见 [references/robustness_rules.md](references/robustness_rules.md)

---

## 3. 低功耗设计

### 检查项

| 检查 | 说明 |
|------|------|
| 门控时钟 | 是否插入 ICG (Integrated Clock Gating) |
| 隔离单元 | 关断域到常开域的信号隔离 |
| 无用翻转 | 冗余的信号翻转 |
| 多电压域 | Level Shifter 是否正确 |

```verilog
// 手动门控时钟 (不推荐直接用)
// 应使用综合工具自动插入 ICG
wire gated_clk = clk & enable;  // 有毛刺风险!

// 正确做法: 让综合工具处理
always @(posedge clk) begin
    if (enable)
        data_out <= data_in;  // 工具会自动插入门控
end
```

详见 [references/low_power_rules.md](references/low_power_rules.md)

---

## 4. 可测性设计 (DFT)

### 检查项

| 检查 | 说明 |
|------|------|
| 扫描链友好 | 避免不可控的时钟/复位 |
| 可观测性 | 关键状态是否可引出 |
| 异步逻辑 | 是否影响扫描测试 |

详见 [references/dft_rules.md](references/dft_rules.md)

---

## 5. 可维护性

### 检查项

| 检查 | 说明 |
|------|------|
| 硬编码 | 数值应使用 parameter |
| 宏管理 | `ifdef 命名是否清晰 |
| 注释 | 关键逻辑是否有注释 |

---

## 工具脚本

```bash
# 完整检查
python scripts/run_lint.py --file module.v --check all

# 仅 CDC 检查
python scripts/run_lint.py --file module.v --check cdc

# 仅健壮性检查
python scripts/run_lint.py --file module.v --check robust
```

## 参考文档

| 文档 | 说明 |
|------|------|
| [cdc_rules.md](references/cdc_rules.md) | CDC/RDC 规则 |
| [robustness_rules.md](references/robustness_rules.md) | 健壮性规则 |
| [low_power_rules.md](references/low_power_rules.md) | 低功耗规则 |
| [dft_rules.md](references/dft_rules.md) | DFT 规则 |
| [synthesis_rules.md](references/synthesis_rules.md) | 可综合性规则 |
| [style_rules.md](references/style_rules.md) | 风格规则 |
| [common_issues.md](references/common_issues.md) | 常见问题 |
