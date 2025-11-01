"""
測試執行腳本
執行所有測試並生成報告
"""
import sys
import subprocess
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(test_type="all", verbose=True):
    """
    執行測試
    
    Args:
        test_type: 測試類型 ('all', 'unit', 'integration', 'performance')
        verbose: 是否顯示詳細輸出
    """
    print("=" * 70)
    print("執行測試")
    print("=" * 70)
    
    # 基本命令
    cmd = ["pytest"]
    
    # 根據測試類型選擇測試檔案
    if test_type == "unit":
        cmd.extend([
            "tests/test_recommendation_engine.py",
            "tests/test_validators.py",
            "tests/test_api_endpoints.py"
        ])
        print("測試類型: 單元測試")
    elif test_type == "integration":
        cmd.append("tests/test_integration.py")
        print("測試類型: 整合測試")
    elif test_type == "performance":
        cmd.append("tests/test_performance.py")
        print("測試類型: 效能測試")
    else:
        cmd.append("tests/")
        print("測試類型: 所有測試")
    
    # 添加選項
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "--tb=short",
        "-s"  # 顯示 print 輸出
    ])
    
    print(f"執行命令: {' '.join(cmd)}")
    print("=" * 70)
    
    # 執行測試
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"執行測試時發生錯誤: {e}")
        return 1


def run_tests_with_coverage():
    """執行測試並生成覆蓋率報告"""
    print("=" * 70)
    print("執行測試（含覆蓋率）")
    print("=" * 70)
    
    cmd = [
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term",
        "-v"
    ]
    
    print(f"執行命令: {' '.join(cmd)}")
    print("=" * 70)
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("覆蓋率報告已生成: htmlcov/index.html")
            print("=" * 70)
        
        return result.returncode
    except Exception as e:
        print(f"執行測試時發生錯誤: {e}")
        return 1


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='執行測試')
    parser.add_argument(
        '--type',
        type=str,
        default='all',
        choices=['all', 'unit', 'integration', 'performance'],
        help='測試類型'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='生成覆蓋率報告'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=True,
        help='顯示詳細輸出'
    )
    
    args = parser.parse_args()
    
    if args.coverage:
        return run_tests_with_coverage()
    else:
        return run_tests(args.type, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
