# Verilog 编码风格规则

## 命名规范

### 信号命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 信号 | snake_case | `data_in`, `write_enable` |
| 参数 | UPPER_SNAKE | `DATA_WIDTH`, `FIFO_DEPTH` |
| 模块 | snake_case | `fifo_ctrl`, `rx_hbf_top` |

### 前缀/后缀

| 含义 | 规则 | 示例 |
|------|------|------|
| 时钟 | clk | `clk`, `clk_200m` |
| 复位 | rst | `rst_n` (低有效) |
| 使能 | en | `write_en`, `ce` |
| 有效 | vld | `data_vld` |
| 就绪 | rdy | `fifo_rdy` |
| 寄存器延迟 | _d1, _d2 | `data_d1`, `data_d2` |
| 负逻辑 | _n | `rst_n`, `cs_n` |
| I/Q 通道 | _i, _q | `data_i`, `data_q` |

## 格式规范

### 缩进

- 使用 **4 空格**，禁止 Tab
- 连续语句对齐

### 行长度

- 最大 **100 字符**
- 长语句换行并对齐

### 端口声明

```verilog
module example #(
    parameter DATA_WL = 16
)(
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire [DATA_WL-1:0]      data_in,
    output reg  [DATA_WL-1:0]      data_out
);
```

## 禁止的风格

| 问题 | 说明 |
|------|------|
| 驼峰命名 | 使用 `dataIn` 而非 `data_in` |
| 混合大小写 | 使用 `DataWidth` 而非 `DATA_WIDTH` |
| 单字母信号 | 使用 `a`, `b` 而非描述性名称 |
| 尾随空格 | 行尾有空格 |
