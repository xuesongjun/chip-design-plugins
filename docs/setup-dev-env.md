# Windows 开发环境自动配置指南

本文档说明如何使用 `setup-dev-env.ps1` 在新 Windows 机器上一键配置 Claude Code 芯片开发环境。

## 配置内容

脚本自动完成以下操作：

| 步骤 | 内容 | 说明 |
|------|------|------|
| 1 | 安装 MSYS2 | 通过 winget 安装，默认路径 `C:\msys64` |
| 2 | 安装 MSYS2 包 | `verilator`（ucrt64 版本） |
| 3 | 配置用户 PATH | 将 `C:\msys64\usr\bin` 和 `C:\msys64\ucrt64\bin` 加入用户 PATH |
| 4 | 配置 Claude Code | 修改 `settings.json`，切换 Shell 为 MSYS2 bash |
| 5 | 创建 `~/.bashrc` | 重定向 HOME 到 Windows 用户目录 |

脚本具备**幂等性**：重复执行不会覆盖已有配置。

## 快速开始

### 方式一：直接运行（推荐）

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/xuesongjun/chip-design-plugins/main/scripts/setup-dev-env.ps1" -OutFile "$env:TEMP\setup-dev-env.ps1"
& "$env:TEMP\setup-dev-env.ps1"
```

### 方式二：克隆仓库后运行

```powershell
git clone https://github.com/xuesongjun/chip-design-plugins.git
cd chip-design-plugins
.\scripts\setup-dev-env.ps1
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-Msys2Path` | string | `C:\msys64` | MSYS2 安装路径 |
| `-SkipMsys2Install` | switch | - | 跳过 MSYS2 安装 |
| `-SkipPackages` | switch | - | 跳过 pacman 包安装 |
| `-SkipClaudeConfig` | switch | - | 跳过 Claude Code 配置 |

### 使用示例

```powershell
# 仅配置 Claude Code（MSYS2 和工具已手动安装好）
.\setup-dev-env.ps1 -SkipMsys2Install -SkipPackages

# MSYS2 安装在非默认路径
.\setup-dev-env.ps1 -Msys2Path "D:\msys64"
```

## 脚本完成后的手动步骤

### 1. 安装 Verible（LSP 支持）

1. 访问 [Verible Releases](https://github.com/chipsalliance/verible/releases) 下载 Windows 预编译包
2. 解压到 `C:\tools\verible\`
3. 将 `C:\tools\verible` 加入系统用户 PATH

验证：`verible-verilog-ls --version`

### 2. 重启 Claude Code

**必须完全重启**（关闭所有 Claude Code 窗口后重新打开），配置才能生效。

### 3. 安装 Claude Code 插件

```
/plugin marketplace add xuesongjun/chip-design-plugins
/plugin install hdl-toolkit@chip-design
/plugin install systemverilog-lsp@chip-design
```

## 验证环境

重启 Claude Code 后验证：

```bash
echo $SHELL          # 应输出 /usr/bin/bash（MSYS2）
echo $HOME           # 应输出 /c/Users/<用户名>
which git            # 应找到 git
which verilator      # 应找到 verilator
which verible-verilog-ls  # 应找到 verible（如已安装）
```

## 常见问题

### Q：winget 安装 MSYS2 失败

手动从 [msys2.org](https://www.msys2.org/) 下载安装包，安装到 `C:\msys64`，然后：

```powershell
.\setup-dev-env.ps1 -SkipMsys2Install
```

### Q：settings.json 已有其他配置，会被覆盖吗？

不会。脚本只追加/更新 `SHELL`、`BASH_ENV`、`MSYS2_PATH_TYPE` 三项，其他配置保持不变。运行前自动备份原文件。

## 参考文档

- [Verible 官方文档](https://chipsalliance.github.io/verible/)
- [MSYS2 官网](https://www.msys2.org/)
