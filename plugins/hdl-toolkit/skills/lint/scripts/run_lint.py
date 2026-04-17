#!/usr/bin/env python3
"""
Verilog 全面代码审查工具

检查类别:
- syntax:    语法检查 (Verilator/Verible/Icarus)
- style:     风格检查
- synthesis: 可综合性检查
- cdc:       跨时钟域检查
- robust:    健壮性检查 (FSM, 边界条件)
- all:       全部检查

用法:
    python run_lint.py --file module.v --check all
    python run_lint.py --file module.v --check cdc
    python run_lint.py --file module.v --check robust
"""

import argparse
import subprocess
import sys
import os
import re
from typing import List, Dict, Tuple
from pathlib import Path


def detect_tools() -> Dict[str, bool]:
    """检测已安装的工具"""
    tools = {
        'verilator': False,
        'iverilog': False,
        'verible': False
    }

    for tool in tools:
        try:
            if tool == 'verible':
                subprocess.run(['verible-verilog-lint', '--version'],
                              capture_output=True, check=False)
            else:
                subprocess.run([tool, '--version'],
                              capture_output=True, check=False)
            tools[tool] = True
        except FileNotFoundError:
            pass

    return tools


def run_verilator(file_path: str, strict: bool = False) -> Tuple[int, str]:
    """运行 Verilator lint"""
    cmd = ['verilator', '--lint-only']
    if strict:
        cmd.extend(['-Wall', '-Werror'])
    cmd.append(file_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stderr


def run_iverilog(file_path: str) -> Tuple[int, str]:
    """运行 Icarus Verilog 语法检查"""
    cmd = ['iverilog', '-t', 'null', '-Wall', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stderr


def run_verible(file_path: str) -> Tuple[int, str]:
    """运行 Verible lint"""
    cmd = ['verible-verilog-lint', file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def analyze_code_style(file_path: str) -> List[Dict]:
    """静态代码风格分析"""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # 行长度检查
        if len(line.rstrip()) > 100:
            issues.append({
                'line': i,
                'type': 'STYLE',
                'severity': 'low',
                'message': f'行长度 {len(line.rstrip())} 超过 100 字符'
            })

        # Tab 字符检查
        if '\t' in line:
            issues.append({
                'line': i,
                'type': 'STYLE',
                'severity': 'low',
                'message': '使用 Tab 字符，建议用空格'
            })

        # 驼峰命名检查
        camel_match = re.search(r'\b(reg|wire|logic)\s+.*\s+([a-z]+[A-Z][a-zA-Z]*)\b', line)
        if camel_match:
            issues.append({
                'line': i,
                'type': 'STYLE',
                'severity': 'low',
                'message': f"信号 '{camel_match.group(2)}' 使用驼峰命名，建议改为 snake_case"
            })

        # 硬编码数值检查
        hardcode_match = re.search(r'\[\s*(\d{2,})\s*:\s*0\s*\]', line)
        if hardcode_match:
            val = int(hardcode_match.group(1))
            if val not in [7, 15, 31, 63, 127]:  # 常见位宽
                issues.append({
                    'line': i,
                    'type': 'MAINTAIN',
                    'severity': 'low',
                    'message': f'硬编码位宽 [{val}:0]，建议使用 parameter'
                })

    return issues


def analyze_synthesis(file_path: str) -> List[Dict]:
    """可综合性检查"""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    patterns = [
        (r'#\d+', 'SYNTHESIS', 'high', '延迟语句 (#delay) 不可综合'),
        (r'\$display', 'SYNTHESIS', 'medium', '$display 是仿真专用'),
        (r'\$finish', 'SYNTHESIS', 'medium', '$finish 是仿真专用'),
        (r'\$time', 'SYNTHESIS', 'medium', '$time 是仿真专用'),
        (r'\$random', 'SYNTHESIS', 'high', '$random 不可综合'),
        (r'initial\s+begin', 'SYNTHESIS', 'medium',
         'initial 块: FPGA 可用, ASIC 不可综合'),
        (r'forever\s+begin', 'SYNTHESIS', 'high', 'forever 循环不可综合'),
        (r'\bwait\b', 'SYNTHESIS', 'high', 'wait 语句不可综合'),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, issue_type, severity, message in patterns:
            if re.search(pattern, line):
                issues.append({
                    'line': i,
                    'type': issue_type,
                    'severity': severity,
                    'message': message
                })

    # Latch 检测 (简单启发式)
    in_always_comb = False
    always_start = 0
    for i, line in enumerate(lines, 1):
        if re.search(r'always\s*@\s*\(\s*\*\s*\)', line) or \
           re.search(r'always_comb', line):
            in_always_comb = True
            always_start = i
        elif in_always_comb and re.search(r'\bend\b', line):
            in_always_comb = False

    return issues


def analyze_cdc(file_path: str) -> List[Dict]:
    """跨时钟域 (CDC) 检查"""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # 提取所有时钟信号
    clocks = set()
    for line in lines:
        # 常见时钟命名模式
        clk_match = re.findall(r'\b(clk\w*|clock\w*|\w+_clk)\b', line, re.IGNORECASE)
        clocks.update(clk_match)

    # 检测多时钟域
    if len(clocks) > 1:
        issues.append({
            'line': 0,
            'type': 'CDC_INFO',
            'severity': 'info',
            'message': f'检测到多时钟域: {", ".join(sorted(clocks))}'
        })

    for i, line in enumerate(lines, 1):
        # 检查异步复位是否有同步释放
        if re.search(r'negedge\s+rst', line, re.IGNORECASE):
            # 查找是否有同步器模式
            context = '\n'.join(lines[max(0,i-5):min(len(lines),i+10)])
            if not re.search(r'rst.*_sync|sync.*rst|reset_sync', context, re.IGNORECASE):
                issues.append({
                    'line': i,
                    'type': 'CDC',
                    'severity': 'high',
                    'message': '异步复位建议使用同步释放 (reset synchronizer)'
                })

        # 检查手动门控时钟 (有毛刺风险)
        if re.search(r'=\s*clk\s*[&|]\s*\w+', line) or \
           re.search(r'=\s*\w+\s*[&|]\s*clk', line):
            issues.append({
                'line': i,
                'type': 'CDC',
                'severity': 'high',
                'message': '手动门控时钟有毛刺风险，应使用 ICG 单元或让工具自动插入'
            })

        # 检查是否有同步器实例
        if re.search(r'sync_2ff|sync_3ff|synchronizer', line, re.IGNORECASE):
            issues.append({
                'line': i,
                'type': 'CDC_INFO',
                'severity': 'info',
                'message': '检测到同步器实例'
            })

    # 检查是否有 ASYNC_REG 属性
    if '(* ASYNC_REG' not in content and 'async_reg' not in content.lower():
        if len(clocks) > 1:
            issues.append({
                'line': 0,
                'type': 'CDC',
                'severity': 'medium',
                'message': '多时钟域设计但未发现 ASYNC_REG 属性，同步器可能被优化'
            })

    return issues


def analyze_robustness(file_path: str) -> List[Dict]:
    """健壮性检查 (FSM, 边界条件)"""
    issues = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # FSM 检查
    case_blocks = []
    in_case = False
    case_start = 0
    has_default = False
    brace_count = 0

    for i, line in enumerate(lines, 1):
        # 检测 case 语句开始
        if re.search(r'\bcase\s*\(', line) or re.search(r'\bcasez\s*\(', line) or \
           re.search(r'\bcasex\s*\(', line):
            in_case = True
            case_start = i
            has_default = False

        if in_case:
            if re.search(r'\bdefault\s*:', line):
                has_default = True
            if re.search(r'\bendcase\b', line):
                if not has_default:
                    issues.append({
                        'line': case_start,
                        'type': 'ROBUST',
                        'severity': 'high',
                        'message': 'case 语句缺少 default 分支 (FSM 可能无法从非法状态恢复)'
                    })
                in_case = False

    # FIFO 边界检查
    for i, line in enumerate(lines, 1):
        # 写入时未检查 full
        if re.search(r'wr_en|write_en', line, re.IGNORECASE):
            context = '\n'.join(lines[max(0,i-3):min(len(lines),i+3)])
            if 'full' not in context.lower() and 'wr_ptr' not in context.lower():
                issues.append({
                    'line': i,
                    'type': 'ROBUST',
                    'severity': 'medium',
                    'message': '写使能信号附近未检测到 full 标志检查'
                })

        # 读取时未检查 empty
        if re.search(r'rd_en|read_en', line, re.IGNORECASE):
            context = '\n'.join(lines[max(0,i-3):min(len(lines),i+3)])
            if 'empty' not in context.lower() and 'rd_ptr' not in context.lower():
                issues.append({
                    'line': i,
                    'type': 'ROBUST',
                    'severity': 'medium',
                    'message': '读使能信号附近未检测到 empty 标志检查'
                })

    # 计数器溢出检查
    for i, line in enumerate(lines, 1):
        # 简单的递增计数器
        if re.search(r'<=\s*\w+\s*\+\s*1', line):
            context = '\n'.join(lines[max(0,i-5):min(len(lines),i+5)])
            # 检查是否有溢出保护
            if not re.search(r'!=|<|>|==.*MAX|==.*max|overflow|saturate', context):
                issues.append({
                    'line': i,
                    'type': 'ROBUST',
                    'severity': 'low',
                    'message': '计数器递增，建议检查是否需要溢出保护'
                })

    # 参数化检查 - 硬编码位宽
    for i, line in enumerate(lines, 1):
        # 检查是否有未参数化的位宽
        match = re.search(r'\[\s*(\d+)\s*:\s*0\s*\]', line)
        if match and 'parameter' not in line.lower() and 'localparam' not in line.lower():
            width = int(match.group(1)) + 1
            if width > 8 and width not in [16, 32, 64]:
                issues.append({
                    'line': i,
                    'type': 'MAINTAIN',
                    'severity': 'low',
                    'message': f'非标准位宽 {width}，建议使用 parameter 参数化'
                })

    return issues


def generate_report(file_path: str, lint_output: str,
                   all_issues: Dict[str, List[Dict]]) -> str:
    """生成审查报告"""
    report = []
    report.append(f"## 代码审查报告: {os.path.basename(file_path)}")
    report.append("")

    # 统计
    errors = lint_output.count('Error') + lint_output.count('error')
    warnings = lint_output.count('Warning') + lint_output.count('warning')

    high_count = sum(1 for issues in all_issues.values()
                     for i in issues if i.get('severity') == 'high')
    medium_count = sum(1 for issues in all_issues.values()
                       for i in issues if i.get('severity') == 'medium')
    low_count = sum(1 for issues in all_issues.values()
                    for i in issues if i.get('severity') == 'low')

    report.append("### 摘要")
    report.append(f"| 严重性 | 数量 |")
    report.append(f"|--------|------|")
    report.append(f"| **高** | {high_count + errors} |")
    report.append(f"| 中 | {medium_count + warnings} |")
    report.append(f"| 低 | {low_count} |")
    report.append("")

    # Lint 工具输出
    if lint_output.strip():
        report.append("### 语法检查")
        report.append("```")
        report.append(lint_output.strip()[:2000])  # 限制长度
        if len(lint_output.strip()) > 2000:
            report.append("... (输出截断)")
        report.append("```")
        report.append("")

    # 各类问题
    category_names = {
        'cdc': '跨时钟域 (CDC)',
        'robust': '健壮性',
        'synthesis': '可综合性',
        'style': '风格',
    }

    for category, issues in all_issues.items():
        if issues:
            name = category_names.get(category, category)
            report.append(f"### {name}问题")

            # 按严重性排序
            sorted_issues = sorted(issues,
                key=lambda x: {'high': 0, 'medium': 1, 'low': 2, 'info': 3}.get(x.get('severity', 'low'), 2))

            for issue in sorted_issues:
                severity = issue.get('severity', 'low')
                severity_mark = {'high': '**[高]**', 'medium': '[中]', 'low': '[低]', 'info': '[信息]'}.get(severity, '')
                if issue['line'] > 0:
                    report.append(f"- 行 {issue['line']} {severity_mark}: {issue['message']}")
                else:
                    report.append(f"- {severity_mark}: {issue['message']}")
            report.append("")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Verilog 全面代码审查工具')
    parser.add_argument('--file', '-f', required=True, help='Verilog 文件路径')
    parser.add_argument('--tool', '-t', choices=['verilator', 'iverilog', 'verible', 'auto'],
                       default='auto', help='使用的 lint 工具')
    parser.add_argument('--check', '-c',
                       choices=['syntax', 'style', 'synthesis', 'cdc', 'robust', 'all'],
                       default='all', help='检查类型')
    parser.add_argument('--strict', action='store_true', help='严格模式')

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"错误: 文件不存在: {args.file}")
        sys.exit(1)

    print("=" * 60)
    print("Verilog 全面代码审查")
    print("=" * 60)
    print(f"文件: {args.file}")
    print(f"检查类型: {args.check}")

    # 检测工具
    tools = detect_tools()
    available = [t for t, v in tools.items() if v]
    print(f"可用工具: {', '.join(available) if available else '无'}")

    lint_output = ""
    all_issues = {}

    # 运行外部 lint 工具
    if args.check in ['syntax', 'all']:
        tool = args.tool
        if tool == 'auto':
            if tools['verilator']:
                tool = 'verilator'
            elif tools['iverilog']:
                tool = 'iverilog'
            elif tools['verible']:
                tool = 'verible'
            else:
                print("警告: 未检测到 lint 工具，跳过语法检查")
                tool = None

        if tool:
            print(f"\n运行 {tool} 语法检查...")
            if tool == 'verilator':
                code, lint_output = run_verilator(args.file, args.strict)
            elif tool == 'iverilog':
                code, lint_output = run_iverilog(args.file)
            elif tool == 'verible':
                code, lint_output = run_verible(args.file)

    # CDC 检查
    if args.check in ['cdc', 'all']:
        print("运行 CDC 检查...")
        all_issues['cdc'] = analyze_cdc(args.file)

    # 健壮性检查
    if args.check in ['robust', 'all']:
        print("运行健壮性检查...")
        all_issues['robust'] = analyze_robustness(args.file)

    # 可综合性检查
    if args.check in ['synthesis', 'all']:
        print("运行可综合性检查...")
        all_issues['synthesis'] = analyze_synthesis(args.file)

    # 风格检查
    if args.check in ['style', 'all']:
        print("运行风格检查...")
        all_issues['style'] = analyze_code_style(args.file)

    # 生成报告
    report = generate_report(args.file, lint_output, all_issues)
    print("\n" + report)


if __name__ == "__main__":
    main()
