---
description: 格式化 Verilog/SystemVerilog 文件，使用 verible-verilog-format
disable-model-invocation: true
---

# Verible 代码格式化

## 操作步骤

1. 确认要格式化的文件范围（用户指定的文件，或当前目录下的 `.v`/`.sv`/`.svh`/`.vh` 文件）
2. 搜索项目中是否存在 `.verible-format` 配置文件
3. 执行格式化命令

## 格式化命令

### 有 `.verible-format` 配置文件时

```bash
verible-verilog-format --inplace --flagfile <配置文件路径> <文件...>
```

### 无配置文件时

```bash
verible-verilog-format --inplace <文件...>
```

### 用户指定额外参数时

用户参数追加在命令末尾，会覆盖配置文件中的同名参数：

```bash
verible-verilog-format --inplace --flagfile <配置文件路径> --column_limit 80 <文件...>
```

## 常用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--column_limit` | 100 | 目标行宽 |
| `--indentation_spaces` | 2 | 每级缩进空格数 |
| `--wrap_spaces` | 4 | 续行缩进空格数 |
| `--port_declarations_alignment` | infer | 端口声明对齐方式 |
| `--named_port_alignment` | infer | 命名端口连接对齐方式 |
| `--assignment_statement_alignment` | infer | 赋值语句对齐方式 |

对齐参数可选值：`align`（对齐）/ `flush-left`（左对齐）/ `preserve`（保持原样）/ `infer`（自动推断）

## 注意事项

- 格式化前确认文件可正常编译，格式化器不处理语法错误的文件
- 使用 `--verify` 参数可先检查是否需要格式化而不实际修改
- 批量格式化多个文件时直接列出所有文件路径
