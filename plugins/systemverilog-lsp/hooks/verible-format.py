#!/usr/bin/env python
"""PostToolUse hook: auto-format Verilog/SystemVerilog files after editing.

开关机制：项目中存在 .verible-format 文件且包含 '# hook: on' 时启用。
配置文件同时作为 verible-verilog-format 的 --flagfile 使用。
"""
import json
import subprocess
import sys
import shutil
import os

VERILOG_EXTENSIONS = (".v", ".sv", ".svh", ".vh")
FORMAT_CONFIG_NAME = ".verible-format"


def find_config_upward(file_path, config_name):
    """从文件所在目录向上搜索配置文件，返回路径或 None"""
    directory = os.path.dirname(os.path.abspath(file_path))
    while True:
        config_path = os.path.join(directory, config_name)
        if os.path.isfile(config_path):
            return config_path
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def is_format_hook_enabled(config_path):
    """读取配置文件，检查是否包含 '# hook: on'"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().lower() == "# hook: on":
                    return True
        return False
    except Exception:
        return False


def main():
    try:
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")

        if not file_path or not file_path.lower().endswith(VERILOG_EXTENSIONS):
            print(json.dumps({}))
            return

        fmt_cmd = shutil.which("verible-verilog-format")
        if not fmt_cmd:
            print(json.dumps({}))
            return

        # 搜索 .verible-format 配置文件
        config_path = find_config_upward(file_path, FORMAT_CONFIG_NAME)
        if not config_path or not is_format_hook_enabled(config_path):
            print(json.dumps({}))
            return

        # 执行格式化
        cmd = [fmt_cmd, "--inplace", "--flagfile", config_path, file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        filename = os.path.basename(file_path)
        if result.returncode == 0:
            msg = "[verible-format] {}: 已格式化".format(filename)
        else:
            err = result.stderr.strip()[:100] if result.stderr else "未知错误"
            msg = "[verible-format] {}: 格式化失败 - {}".format(filename, err)

        print(json.dumps({"systemMessage": msg}))

    except Exception as e:
        print(json.dumps({"systemMessage": "[verible-format] 执行出错: {}".format(str(e))}))

    sys.exit(0)


if __name__ == "__main__":
    main()
