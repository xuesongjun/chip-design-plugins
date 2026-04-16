# systemverilog-lsp

Verilog/SystemVerilog 语言服务器集成，基于 [Verible](https://github.com/chipsalliance/verible)。提供诊断、跳转、查找引用、格式化、lint autofix。

## 支持的扩展名

`.v`、`.sv`、`.svh`、`.vh`

## 功能

- **Diagnostics**: 语法错误 + 70+ lint 规则
- **Go to Definition**: 跨文件符号导航（需 `verible.filelist`）
- **Find References**: 跨文件引用查找
- **Formatting**: 全文档/范围格式化
- **Document Symbol**: module/class/function/variable 大纲
- **Code Action**: lint autofix + AUTO 展开（AUTOINST 等）
- **Rename**: 符号重命名

## 命令

| 命令 | 说明 |
|------|------|
| `/systemverilog-lsp:format` | 手动格式化 Verilog 文件 |

## Hooks

| Hook | 触发 | 功能 |
|------|------|------|
| autofix | PostToolUse + Edit/Write/MultiEdit | 编辑后自动运行 `verible-verilog-lint --autofix=inplace` |
| autoformat | PostToolUse + Edit/Write/MultiEdit | 当项目存在 `.verible-format` 且包含 `# hook: on` 时自动格式化 |

## 安装 Verible

### Homebrew (macOS)
```bash
brew install verible
```

### Linux
```bash
wget https://github.com/chipsalliance/verible/releases/latest/download/verible-<version>-linux-static-x86_64.tar.gz
tar xzf verible-*.tar.gz
sudo cp verible-*/bin/* /usr/local/bin/
```

### Windows
从 [Verible Releases](https://github.com/chipsalliance/verible/releases) 下载，将 `bin/` 加入 PATH。

验证：
```bash
verible-verilog-ls --version
```

## 项目配置

### Lint 规则配置

在项目根目录创建 `.rules.verible_lint`：

```
# 无前缀或 + 前缀：启用规则，- 前缀：禁用规则
-no-trailing-spaces
-parameter-name-style
line-length=length:120
```

查看所有规则：`verible-verilog-lint --print_rules_file`

### 跨文件功能

跨文件功能需要项目根目录的 `verible.filelist`：

```
rtl/top.sv
rtl/sub_module.v
inc/defines.svh
```

### 自动格式化开关

在项目根目录创建 `.verible-format`：

```
# hook: on 表示编辑后自动格式化（可选，默认关闭）
# hook: on

--column_limit 120
--indentation_spaces 2
--port_declarations_alignment align
--named_port_alignment align
```

**开关规则：**
- 文件存在且包含 `# hook: on` → 自动格式化启用
- 文件存在但无 `# hook: on` → 自动格式化关闭，`/systemverilog-lsp:format` 仍按配置格式化
- 文件不存在 → 自动格式化关闭，`/systemverilog-lsp:format` 使用默认参数

## 与 hdl-toolkit 的协作

| 工具 | 关注点 |
|------|--------|
| systemverilog-lsp | 自动可修复的格式问题：缩进、行宽、对齐、trailing space、lint warnings |
| hdl-toolkit | 语义和架构问题：CDC、FSM、命名约定、可综合性、综合前检查 |

两者互补，建议同时安装。
