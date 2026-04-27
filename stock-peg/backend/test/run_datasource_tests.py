#!/usr/bin/env python3
"""Datasource 测试运行器

运行方式：
    python test/run_datasource_tests.py
    python test/run_datasource_tests.py --verbose
    python test/run_datasource_tests.py --coverage
"""
import sys
import subprocess
from pathlib import Path

# 添加 backend 到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def run_tests(verbose=False, coverage=False):
    """运行 datasource 测试"""
    
    # 构建测试命令
    cmd = ["python", "-m", "pytest", "test/test_datasource.py"]
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend([
            "--cov=datasource",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    print("=" * 60)
    print("运行 Datasource 单元测试")
    print("=" * 60)
    print(f"命令: {' '.join(cmd)}")
    print("=" * 60)
    
    # 运行测试
    result = subprocess.run(cmd, cwd=backend_dir)
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="运行 Datasource 测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", "-c", action="store_true", help="生成覆盖率报告")
    
    args = parser.parse_args()
    
    exit_code = run_tests(verbose=args.verbose, coverage=args.coverage)
    sys.exit(exit_code)
