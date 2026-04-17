#!/usr/bin/env python3
"""
系数量化和分析工具

功能:
1. 浮点系数转定点
2. 分析量化误差
3. 检测系数对称性和零值
4. 生成 Verilog localparam 语句

用法:
    python quantize_coef.py --coef "0.5, 0.25, -0.125" --format "S(14,11)"
    python quantize_coef.py --file coef.txt --format "S(16,15)"
"""

import argparse
import numpy as np
from typing import List, Tuple


def parse_swf_format(format_str: str) -> Tuple[int, int]:
    """解析 S(W,F) 格式字符串"""
    format_str = format_str.strip().upper()
    if format_str.startswith('S(') and format_str.endswith(')'):
        parts = format_str[2:-1].split(',')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    raise ValueError(f"无效格式: {format_str}, 应为 S(W,F) 格式，如 S(14,11)")


def quantize_coefficient(value: float, total_bits: int, frac_bits: int) -> int:
    """量化单个系数"""
    scale = 2 ** frac_bits
    quantized = int(round(value * scale))

    # 饱和处理
    max_val = (1 << (total_bits - 1)) - 1
    min_val = -(1 << (total_bits - 1))
    quantized = max(min(quantized, max_val), min_val)

    return quantized


def analyze_symmetry(coefs: List[float], tolerance: float = 1e-10) -> dict:
    """分析系数对称性"""
    n = len(coefs)
    result = {
        'is_symmetric': True,
        'is_antisymmetric': True,
        'symmetric_pairs': [],
        'zero_indices': [],
        'center_index': None
    }

    # 检查对称性
    for i in range(n // 2):
        j = n - 1 - i
        if abs(coefs[i] - coefs[j]) > tolerance:
            result['is_symmetric'] = False
        if abs(coefs[i] + coefs[j]) > tolerance:
            result['is_antisymmetric'] = False
        if abs(coefs[i] - coefs[j]) <= tolerance:
            result['symmetric_pairs'].append((i, j))

    # 检查零值
    for i, c in enumerate(coefs):
        if abs(c) < tolerance:
            result['zero_indices'].append(i)

    # 中心系数 (奇数长度)
    if n % 2 == 1:
        result['center_index'] = n // 2

    return result


def generate_verilog(coefs: List[float], total_bits: int, frac_bits: int,
                     prefix: str = "COEF") -> str:
    """生成 Verilog localparam 语句"""
    lines = []
    lines.append(f"// Coefficient Definition: S({total_bits},{frac_bits}) format")
    lines.append(f"// Quantization: scale = 2^{frac_bits} = {2**frac_bits}")
    lines.append("")

    for i, coef in enumerate(coefs):
        q_val = quantize_coefficient(coef, total_bits, frac_bits)
        q_float = q_val / (2 ** frac_bits)
        error = coef - q_float

        sign = "" if q_val >= 0 else "-"
        abs_val = abs(q_val)

        lines.append(
            f"localparam signed [{total_bits-1}:0] {prefix}_{i} = "
            f"{sign}{total_bits}'sd{abs_val};  "
            f"// {coef:.10f} -> {q_float:.10f}, err={error:.2e}"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="系数量化工具")
    parser.add_argument('--coef', type=str, help='逗号分隔的系数列表')
    parser.add_argument('--file', type=str, help='系数文件路径')
    parser.add_argument('--format', type=str, default='S(14,11)',
                        help='定点格式，如 S(14,11)')
    parser.add_argument('--prefix', type=str, default='COEF',
                        help='Verilog 参数前缀')

    args = parser.parse_args()

    # 解析系数
    if args.coef:
        coefs = [float(x.strip()) for x in args.coef.split(',')]
    elif args.file:
        with open(args.file, 'r') as f:
            coefs = [float(line.strip()) for line in f if line.strip()]
    else:
        # 默认示例
        coefs = [-0.0318603515625, 0, 0.2818603515625, 0.5,
                 0.2818603515625, 0, -0.0318603515625]

    # 解析格式
    total_bits, frac_bits = parse_swf_format(args.format)

    print("=" * 60)
    print("系数量化分析")
    print("=" * 60)
    print(f"\n格式: S({total_bits},{frac_bits})")
    print(f"范围: [{-2**(total_bits-frac_bits-1)}, {2**(total_bits-frac_bits-1)})")
    print(f"精度: 2^(-{frac_bits}) = {2**(-frac_bits):.10f}")
    print(f"系数数量: {len(coefs)}")

    # 对称性分析
    print("\n" + "=" * 60)
    print("对称性分析")
    print("=" * 60)
    sym = analyze_symmetry(coefs)
    print(f"对称: {sym['is_symmetric']}")
    print(f"反对称: {sym['is_antisymmetric']}")
    print(f"对称对: {sym['symmetric_pairs']}")
    print(f"零值索引: {sym['zero_indices']}")
    print(f"中心索引: {sym['center_index']}")

    # 优化建议
    if sym['is_symmetric'] and sym['symmetric_pairs']:
        num_mults = len(coefs) - len(sym['symmetric_pairs']) - len(sym['zero_indices'])
        print(f"\n优化: 可使用预加法器，乘法器从 {len(coefs)} 减少到 {num_mults}")

    # 量化结果
    print("\n" + "=" * 60)
    print("量化结果")
    print("=" * 60)
    print(f"\n{'索引':<6} {'原始值':<20} {'量化值':<10} {'还原值':<20} {'误差':<15}")
    print("-" * 71)

    total_error = 0
    for i, coef in enumerate(coefs):
        q_val = quantize_coefficient(coef, total_bits, frac_bits)
        q_float = q_val / (2 ** frac_bits)
        error = coef - q_float
        total_error += error ** 2
        print(f"{i:<6} {coef:<20.10f} {q_val:<10} {q_float:<20.10f} {error:<15.2e}")

    rms_error = np.sqrt(total_error / len(coefs))
    print(f"\nRMS 误差: {rms_error:.2e}")

    # Verilog 输出
    print("\n" + "=" * 60)
    print("Verilog 代码")
    print("=" * 60)
    print()
    print(generate_verilog(coefs, total_bits, frac_bits, args.prefix))


if __name__ == "__main__":
    main()
