---
name: init
description: 初始化数字 IC 项目的目录结构和 Claude Code 配置
disable-model-invocation: true
allowed-tools: Bash Read Write
---

# IC 项目初始化

在当前目录初始化一个数字 IC 项目。如果用户提供了参数（`$ARGUMENTS`），则在该路径下初始化。

## 执行步骤

1. 运行初始化脚本：

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/init_project.py" $ARGUMENTS
```

如果系统默认 `python` 是 Python 2，尝试 `python3`。

2. 脚本执行完成后，提示用户：
   - 编辑 `CLAUDE.md` 填写项目信息（顶层模块、总线协议、工具链）
   - 运行 `git init && git add -A && git commit -m 'chore: init ic project'`
   - 项目已包含 HDL 编码规范引用、CDC/风格/综合前检查指引

3. 如果用户在初始化时通过 `$ARGUMENTS` 提供了项目名称，将其填入 CLAUDE.md 的项目名称字段。
