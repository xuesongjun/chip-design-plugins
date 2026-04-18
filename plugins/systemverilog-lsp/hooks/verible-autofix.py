#!/usr/bin/env python3
"""PostToolUse hook: auto-fix Verible lint warnings after editing .v/.sv/.svh/.vh files."""
import json
import subprocess
import sys
import shutil
import os

VERILOG_EXTENSIONS = (".v", ".sv", ".svh", ".vh")


def count_warnings(lint_cmd, file_path):
    """运行 lint 检查，返回警告数量"""
    r = subprocess.run(
        [lint_cmd, "--rules_config_search", file_path],
        capture_output=True, text=True, timeout=30
    )
    output = r.stderr.strip()
    if not output:
        return 0
    return len(output.split("\n"))


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        if not file_path or not file_path.lower().endswith(VERILOG_EXTENSIONS):
            print(json.dumps({}))
            return

        lint_cmd = shutil.which("verible-verilog-lint")
        if not lint_cmd:
            print(json.dumps({}))
            return

        # 检测警告数量
        before = count_warnings(lint_cmd, file_path)
        if before == 0:
            print(json.dumps({}))
            return

        # 执行 autofix
        subprocess.run(
            [lint_cmd, "--rules_config_search", "--autofix=inplace", file_path],
            capture_output=True, text=True, timeout=30
        )

        # 再次检测剩余警告
        after = count_warnings(lint_cmd, file_path)
        fixed = before - after
        filename = os.path.basename(file_path)

        if fixed > 0 and after == 0:
            msg = "[verible-autofix] {}: 已自动修复 {} 个 lint 警告".format(filename, fixed)
        elif fixed > 0:
            msg = "[verible-autofix] {}: 已自动修复 {} 个警告，剩余 {} 个需手动处理".format(filename, fixed, after)
        else:
            msg = "[verible-autofix] {}: {} 个警告无法自动修复，需手动处理".format(filename, after)

        print(json.dumps({"systemMessage": msg}))

    except Exception as e:
        print(json.dumps({"systemMessage": "[verible-autofix] 执行出错: {}".format(str(e))}))

    sys.exit(0)


if __name__ == "__main__":
    main()
