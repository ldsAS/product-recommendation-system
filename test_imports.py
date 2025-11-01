"""快速測試套件導入"""
import sys

print("測試套件導入...")
print("=" * 60)

packages = [
    ("pandas", "資料處理"),
    ("numpy", "數值計算"),
    ("pydantic", "資料驗證"),
    ("fastapi", "Web 框架"),
    ("lightgbm", "機器學習"),
    ("sklearn", "機器學習基礎"),
]

success_count = 0
fail_count = 0

for package, description in packages:
    try:
        __import__(package)
        print(f"✓ {package:20s} - {description}")
        success_count += 1
    except ImportError as e:
        print(f"✗ {package:20s} - 未安裝")
        fail_count += 1

print("=" * 60)
print(f"成功: {success_count}/{len(packages)}")
print(f"失敗: {fail_count}/{len(packages)}")

if fail_count > 0:
    print("\n請執行以下命令安裝缺少的套件:")
    print("python -m pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✓ 所有核心套件已安裝！")
    sys.exit(0)
