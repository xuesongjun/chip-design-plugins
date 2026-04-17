---
description: 生成符合项目规范的三段式 FSM 模板代码
disable-model-invocation: true
---

# 生成三段式 FSM 模板

## 与用户的交互

如果用户没有提供足够信息，使用 `AskUserQuestion` 工具询问以下内容：

1. **FSM 模块名**（如 `axi_arbiter_fsm`、`spi_master_ctrl`）
2. **状态列表**（如 `IDLE, REQ, GRANT, DONE`）
3. **时钟和复位信号名**（默认 `clk` / `rstn`，可改为项目实际名称如 `ahb_gclk` / `ahb_rstn`）
4. **是否需要输出寄存器化**（默认组合输出）

## 生成的模板结构

严格遵循项目编码规范（见 `coding-style` skill），输出三段式 FSM：

```verilog
//==============================================================================
// Module: <module_name>
// Description: <描述>
//==============================================================================
module <module_name> (
    input  wire        <clk>,
    input  wire        <rstn>,
    // 输入控制信号
    input  wire        start,
    input  wire        done,
    // 输出状态信号
    output wire        busy
);

    // 状态编码
    localparam S_IDLE = 3'd0;
    localparam S_WORK = 3'd1;
    localparam S_DONE = 3'd2;

    reg [2:0] state_q, state_d;

    //--------------------------------------------------------------------------
    // 第一段：状态寄存器（时序逻辑）
    //--------------------------------------------------------------------------
    always @(posedge <clk> or negedge <rstn>) begin
        if (!<rstn>)
            state_q <= S_IDLE;
        else
            state_q <= state_d;
    end

    //--------------------------------------------------------------------------
    // 第二段：次态组合逻辑
    //--------------------------------------------------------------------------
    always @(*) begin
        state_d = state_q;
        case (state_q)
            S_IDLE: begin
                if (start)
                    state_d = S_WORK;
            end
            S_WORK: begin
                if (done)
                    state_d = S_DONE;
            end
            S_DONE: begin
                state_d = S_IDLE;
            end
            default: state_d = S_IDLE;
        endcase
    end

    //--------------------------------------------------------------------------
    // 第三段：输出逻辑（组合输出）
    //--------------------------------------------------------------------------
    assign busy = (state_q == S_WORK);

endmodule
```

## 生成规则

1. **状态编码位宽**：根据状态数量自动计算（N 个状态用 `$clog2(N)` 位宽）
2. **状态命名**：用户提供的状态列表全部加 `S_` 前缀（如 `IDLE` → `S_IDLE`）
3. **时钟/复位**：使用用户提供的名称，默认值符合规范（`xxx_gclk` / `xxx_rstn`）
4. **default 分支**：必须包含，回到 `S_IDLE`
5. **状态寄存器**：必须命名为 `state_q` / `state_d`
6. **如果需要寄存器化输出**：第三段改为时序逻辑块

## 输出后

1. 询问用户文件保存路径（默认建议放在 `rtl/` 下）
2. 询问是否需要生成对应的 testbench 骨架（放在 `tb/` 下）
3. 提示用户后续可用 `/hdl-toolkit:style-check` 验证生成的代码
