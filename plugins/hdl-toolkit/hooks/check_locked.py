#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LOCKED 文件保护 hook
检查 Claude 试图修改的文件是否包含 // CLAUDE-LOCKED 标记，
若有则阻止操作。
触发：PreToolUse, matcher = Edit|Write|MultiEdit
兼容 Python 2.7+ / Python 3
"""

from __future__ import print_function
import json
import sys
import os

LOCK_MARKER = "CLAUDE-LOCKED"
SCAN_LINES = 20


def is_locked(file_path):
    """检查文件头部是否包含 LOCK_MARKER"""
    try:
        if not os.path.isfile(file_path):
            return False
        # 兼容 Python 2/3 的文件读取
        try:
            f = open(file_path, "r", encoding="utf-8", errors="ignore")
        except TypeError:
            # Python 2 不支持 encoding 参数
            f = open(file_path, "r")
        try:
            for i, line in enumerate(f):
                if i >= SCAN_LINES:
                    break
                if LOCK_MARKER in line:
                    return True
        finally:
            f.close()
    except Exception:
        return False
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        file_path = tool_input.get("path", "")

    if not file_path:
        sys.exit(0)

    if is_locked(file_path):
        decision = {
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "文件 {} 包含 // {} 标记，禁止修改。"
                "如确需修改，请用户手动移除该标记后重试。".format(file_path, LOCK_MARKER)
            ),
        }
        print(json.dumps(decision, ensure_ascii=False))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
