# 代码健壮性规则

## 目录

1. [状态机 (FSM) 安全](#状态机-fsm-安全)
2. [边界条件处理](#边界条件处理)
3. [防御性编程](#防御性编程)
4. [检查清单](#检查清单)

---

## 状态机 (FSM) 安全

### FSM 检查项

| 检查 | 严重性 | 说明 |
|------|--------|------|
| 缺少 default | 高 | case 语句必须有 default |
| 非法状态 | 高 | FSM 无法从非法状态恢复 |
| 死锁状态 | 高 | 存在无法退出的状态 |
| 输出不完整 | 中 | 某些状态未定义所有输出 |
| 状态编码 | 低 | 编码方式不当 |

### 三段式 FSM (推荐)

```verilog
// 状态定义
localparam [2:0]
    IDLE  = 3'b001,
    RUN   = 3'b010,
    DONE  = 3'b100;  // One-hot 编码

reg [2:0] state, next_state;

//------------------------------------------
// 第一段: 状态寄存器 (时序逻辑)
//------------------------------------------
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end

//------------------------------------------
// 第二段: 次态逻辑 (组合逻辑)
//------------------------------------------
always @(*) begin
    next_state = state;  // 默认保持当前状态

    case (state)
        IDLE: begin
            if (start)
                next_state = RUN;
        end

        RUN: begin
            if (done)
                next_state = DONE;
            else if (error)
                next_state = IDLE;  // 错误恢复
        end

        DONE: begin
            next_state = IDLE;
        end

        default: begin
            next_state = IDLE;  // 非法状态恢复到安全状态
        end
    endcase
end

//------------------------------------------
// 第三段: 输出逻辑
//------------------------------------------
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        busy <= 1'b0;
        valid <= 1'b0;
    end else begin
        busy  <= (next_state == RUN);
        valid <= (state == DONE);
    end
end
```

### 状态编码方式

| 编码 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| Binary | 面积最小 | 翻转多，组合逻辑复杂 | 状态多，面积敏感 |
| One-hot | 速度快，易调试 | 面积大 | FPGA，高速设计 |
| Gray | 翻转少 | 编码受限 | 顺序状态 |

### SEU 防护 (高可靠性场景)

```verilog
// 使用 Triple Modular Redundancy (TMR)
reg [2:0] state_a, state_b, state_c;
wire [2:0] state_voted;

// 多数投票
assign state_voted = (state_a & state_b) |
                     (state_b & state_c) |
                     (state_a & state_c);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state_a <= IDLE;
        state_b <= IDLE;
        state_c <= IDLE;
    end else begin
        state_a <= next_state;
        state_b <= next_state;
        state_c <= next_state;
    end
end
```

---

## 边界条件处理

### FIFO 满/空处理

```verilog
// FIFO 写入保护
always @(posedge clk) begin
    if (wr_en && !full) begin  // 只在非满时写入
        mem[wr_ptr] <= wr_data;
        wr_ptr <= wr_ptr + 1;
    end
end

// FIFO 读取保护
always @(posedge clk) begin
    if (rd_en && !empty) begin  // 只在非空时读取
        rd_data <= mem[rd_ptr];
        rd_ptr <= rd_ptr + 1;
    end
end

// 可选: 输出溢出/下溢标志
assign overflow  = wr_en && full;
assign underflow = rd_en && empty;
```

### 计数器溢出保护

```verilog
// 方法 1: 饱和计数器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        counter <= '0;
    else if (inc && counter != MAX_VAL)  // 饱和
        counter <= counter + 1;
    else if (dec && counter != '0)       // 下限
        counter <= counter - 1;
end

// 方法 2: 带溢出标志
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= '0;
        overflow <= 1'b0;
    end else if (inc) begin
        {overflow, counter} <= counter + 1;  // 自动检测溢出
    end
end
```

### 数组索引保护

```verilog
// 错误: 索引可能越界
wire [7:0] data = mem[addr];  // addr 可能 >= MEM_DEPTH

// 正确: 范围检查
wire [7:0] data = (addr < MEM_DEPTH) ? mem[addr] : 8'h00;

// 或者使用地址截断 (如果允许回绕)
wire [$clog2(MEM_DEPTH)-1:0] addr_safe = addr[$clog2(MEM_DEPTH)-1:0];
wire [7:0] data = mem[addr_safe];
```

### 除法/取模保护

```verilog
// 防止除以零
wire [15:0] quotient = (divisor != 0) ? dividend / divisor : 16'hFFFF;
```

---

## 防御性编程

### 输入验证

```verilog
// 在模块入口验证输入
module data_processor (
    input  wire [7:0] mode,
    input  wire [15:0] data_in,
    output reg  [15:0] data_out,
    output reg        error
);

always @(posedge clk) begin
    error <= 1'b0;

    case (mode)
        MODE_ADD: data_out <= data_in + offset;
        MODE_SUB: data_out <= data_in - offset;
        MODE_MUL: data_out <= data_in * scale;
        default: begin
            data_out <= 16'h0000;
            error <= 1'b1;  // 报告无效模式
        end
    endcase
end
```

### 超时保护

```verilog
// 防止无限等待
reg [15:0] timeout_cnt;
localparam TIMEOUT_VAL = 16'hFFFF;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        timeout_cnt <= '0;
        timeout_err <= 1'b0;
    end else if (state == WAIT_ACK) begin
        if (ack_received) begin
            timeout_cnt <= '0;
        end else if (timeout_cnt == TIMEOUT_VAL) begin
            timeout_err <= 1'b1;
            // 强制状态转移到错误处理
        end else begin
            timeout_cnt <= timeout_cnt + 1;
        end
    end else begin
        timeout_cnt <= '0;
    end
end
```

### Watchdog 机制

```verilog
// 系统级看门狗
module watchdog #(parameter TIMEOUT = 24'hFFFFFF)(
    input  wire clk,
    input  wire rst_n,
    input  wire kick,      // 喂狗信号
    output reg  wdt_reset  // 复位输出
);

reg [23:0] counter;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        counter <= '0;
        wdt_reset <= 1'b0;
    end else if (kick) begin
        counter <= '0;
        wdt_reset <= 1'b0;
    end else if (counter == TIMEOUT) begin
        wdt_reset <= 1'b1;
    end else begin
        counter <= counter + 1;
    end
end

endmodule
```

---

## 检查清单

### 高优先级

- [ ] 所有 case 语句有 default 分支
- [ ] FSM 能从非法状态恢复
- [ ] FSM 无死锁状态
- [ ] FIFO 满/空边界正确处理
- [ ] 计数器有溢出保护

### 中优先级

- [ ] FSM 使用三段式结构
- [ ] 数组访问有边界检查
- [ ] 关键等待有超时机制
- [ ] 输入参数有有效性检查

### 建议

- [ ] 状态编码适合应用场景
- [ ] 高可靠性场景考虑 TMR
- [ ] 有错误状态指示输出
