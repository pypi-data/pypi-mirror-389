#!/usr/bin/env python3
"""
Nsc410 命令行接口
"""

import sys
import argparse
from .core import Ns4ev, set_compiler
from Nsc371 import Compiler

def main():
    parser = argparse.ArgumentParser(
        description="Nsc410 表达式处理器 - 命令行工具",
        epilog="示例: nsc410 '2 + 3 * 4' 或 nsc410 'f\"结果是: {2+3}\"'"
    )
    
    parser.add_argument(
        "expression",
        help="要处理的表达式"
    )
    
    parser.add_argument(
        "-s", "--space",
        action="store_true",
        help="保留空格（不自动移除）"
    )
    
    parser.add_argument(
        "-c", "--compiler",
        action="store_true", 
        help="启用 Nsc371 编译器支持"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="显示版本信息"
    )
    
    args = parser.parse_args()
    
    if args.version:
        from . import __version__, __author__
        print(f"Nsc410 v{__version__} by {__author__}")
        return
    
    try:
        # 如果启用编译器支持
        compiler = None
        if args.compiler:
            compiler = Compiler()
            set_compiler(compiler)
            print("✓ 编译器支持已启用")
        
        # 处理表达式
        result = Ns4ev(args.expression, space=args.space, compiler=compiler)
        
        # 输出结果
        print("输入:", args.expression)
        print("输出:", result)
        print("类型:", type(result).__name__)
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()