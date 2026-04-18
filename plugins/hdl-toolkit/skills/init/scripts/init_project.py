#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IC 项目初始化脚本
用法：python init_project.py [项目路径]
不指定路径时在当前目录初始化
兼容 Windows / Linux / macOS / Python 2.7+ / Python 3
"""

from __future__ import print_function
import os
import sys
from datetime import datetime

# 兼容 Python 2/3
try:
    from pathlib import Path
except ImportError:
    print("[ERR] 需要 Python 3.4+ 或安装 pathlib (pip install pathlib)")
    sys.exit(1)

# ===== 目录结构 =====
PROJECT_DIRS = [
    "rtl",
    "tb",
    "syn",
    "sim",
    "doc",
    "scripts",
]

# ===== 内嵌模板 =====

CLAUDE_MD = """\
<!-- chip-design-plugins / hdl-toolkit v1.0.0 | {date} -->

# 项目信息

- 项目名称：{project_name}
- 顶层模块：（填写顶层模块名）
- 主要总线协议：（如 AXI4, AHB, APB）
- 综合工具：（如 DC, Vivado, Genus）
- 仿真工具：（如 VCS, Xcelium, ModelSim, Verilator）

# 目录结构

- `rtl/` — RTL 源码
- `tb/` — Testbench
- `syn/` — 综合脚本和约束
- `sim/` — 仿真脚本和波形配置
- `doc/` — 设计文档
- `scripts/` — 辅助脚本

# 常用命令

```bash
# 仿真（填写实际命令）
# make sim TOP=xxx_top

# 综合（填写实际命令）
# make syn

# lint 检查（填写实际命令）
# make lint
```

# 项目特有规则

- （在此补充本项目特有的约定）

# Claude Code 工具

本项目使用 hdl-toolkit 插件提供的功能：
- `/hdl-toolkit:new-fsm` — 生成三段式 FSM 模板
- `/hdl-toolkit:cdc-check` — CDC 路径检查
- `/hdl-toolkit:style-check` — 编码规范检查
- `/hdl-toolkit:pre-syn-check` — 综合前检查

文件保护：在文件头部 20 行内加 `// CLAUDE-LOCKED` 标记，可阻止 Claude 修改该文件。
"""

GITIGNORE = """\
# Claude Code
CLAUDE.local.md
.claude/

# 仿真输出
*.vcd
*.fsdb
*.vpd
*.log
*.wlf
work/
csrc/
simv*
DVEfiles/
AN.DB/
xcelium.d/
xrun.history

# 综合输出
*.ddc
*.sdf
*.sdc
alib-52/
command.log

# 编辑器
*.swp
*.swo
*~
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
Desktop.ini
"""


def print_msg(level, msg):
    print("  [{:4s}] {}".format(level, msg))


def write_if_not_exists(path, content):
    if path.exists():
        print_msg("SKIP", "已存在: {}".format(path.name))
        return False
    if not path.parent.exists():
        path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    print_msg(" OK ", "已创建: {}".format(path.name))
    return True


def main():
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path.cwd()

    project_name = project_root.name

    print("\n" + "=" * 50)
    print("  IC 项目初始化")
    print("  项目路径: {}".format(project_root))
    print("  Plugin:   hdl-toolkit v1.0.0")
    print("=" * 50 + "\n")

    print_msg("INFO", "创建目录结构...")
    for d in PROJECT_DIRS:
        (project_root / d).mkdir(parents=True, exist_ok=True)
    print_msg(" OK ", "目录结构已创建")

    print_msg("INFO", "写入模板文件...")

    write_if_not_exists(
        project_root / "CLAUDE.md",
        CLAUDE_MD.format(
            project_name=project_name,
            date=datetime.now().strftime("%Y-%m-%d"),
        ),
    )

    write_if_not_exists(project_root / ".gitignore", GITIGNORE)

    process_content = (
        "# 变更日志\n"
        "# 格式：[YYYY-MM-DD HH:MM] <类型> <简述>\n"
        "# 类型：feat / fix / refactor / docs / test / chore\n\n"
        "[{}] chore 项目初始化\n"
        "- 改动文件：项目结构、CLAUDE.md\n"
        "- 改动说明：使用 hdl-toolkit 插件初始化项目\n"
    ).format(datetime.now().strftime("%Y-%m-%d %H:%M"))
    write_if_not_exists(project_root / "process.txt", process_content)

    for d in PROJECT_DIRS:
        dir_path = project_root / d
        if dir_path.exists():
            entries = list(dir_path.iterdir())
            non_keep = [f for f in entries if f.name != ".gitkeep"]
            if not non_keep:
                gitkeep = dir_path / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.touch()

    print("\n" + "=" * 50)
    print("  初始化完成!")
    print("")
    print("  后续步骤:")
    print("  1. 编辑 CLAUDE.md 填写项目信息")
    print("  2. git init && git add -A && git commit -m 'chore: init project'")
    print("  3. 开始使用 Claude Code 开发")
    print("")
    print("  可用命令:")
    print("    /hdl-toolkit:new-fsm        生成三段式 FSM 模板")
    print("    /hdl-toolkit:cdc-check      CDC 路径检查")
    print("    /hdl-toolkit:style-check    编码规范检查")
    print("    /hdl-toolkit:pre-syn-check  综合前检查")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
